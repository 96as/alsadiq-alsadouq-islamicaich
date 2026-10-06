"""
Notes Section for the file:
- xAI streaming TTS compatible with current xAI WebSocket API.
- livekit-plugins-xai uses an older wire protocol (config + text_chunk + nested audio).
- xAI's documented API uses query parameters on the upgrade URL and text.delta / audio.delta:
- https://docs.x.ai/developers/model-capabilities/audio/text-to-speech#streaming-tts-websocket
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import weakref
from dataclasses import dataclass, replace
from urllib.parse import urlencode

import aiohttp

from livekit.agents import (
    APIConnectionError,
    APIConnectOptions,
    APIStatusError,
    APITimeoutError,
    tokenize,
    tts,
    utils,
)
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, NOT_GIVEN, NotGivenOr
from livekit.agents.utils import is_given

logger = logging.getLogger(__name__)

SAMPLE_RATE = 24000
NUM_CHANNELS = 1
XAI_WS_BASE = "wss://api.x.ai/v1/tts"
DEFAULT_VOICE = "leo"


@dataclass
class _TTSOptions:
    voice: str
    language: str
    tokenizer: tokenize.WordTokenizer


class TTS(tts.TTS):
    """xAI TTS using the documented bidirectional WebSocket protocol."""

    def __init__(
        self,
        *,
        api_key: NotGivenOr[str] = NOT_GIVEN,
        voice: str = DEFAULT_VOICE,
        language: str = "auto",
        tokenizer: tokenize.WordTokenizer | None = None,
        http_session: aiohttp.ClientSession | None = None,
    ) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=True),
            sample_rate=SAMPLE_RATE,
            num_channels=NUM_CHANNELS,
        )
        resolved_key: str | None = api_key if is_given(api_key) else os.environ.get("XAI_API_KEY")
        if not resolved_key:
            raise ValueError(
                "xAI API key is required, either as argument or set XAI_API_KEY environment variable"
            )
        self._api_key = resolved_key
        if tokenizer is None:
            tokenizer = tokenize.basic.WordTokenizer(ignore_punctuation=False)
        self._opts = _TTSOptions(voice=voice, language=language, tokenizer=tokenizer)
        self._session = http_session
        self._streams = weakref.WeakSet[SynthesizeStream]()

    @property
    def model(self) -> str:
        return "xai-tts-ws"

    @property
    def provider(self) -> str:
        return "xAI"

    def _ws_url(self) -> str:
        voice = (self._opts.voice or DEFAULT_VOICE).strip().lower()
        language = (self._opts.language or "auto").strip() or "auto"
        q = urlencode(
            {
                "language": language,
                "voice": voice,
                "codec": "pcm",
                "sample_rate": str(SAMPLE_RATE),
            }
        )
        return f"{XAI_WS_BASE}?{q}"

    async def _connect_ws(self, timeout: float) -> aiohttp.ClientWebSocketResponse:
        try:
            ws = await asyncio.wait_for(
                self._ensure_session().ws_connect(
                    self._ws_url(),
                    headers={"Authorization": f"Bearer {self._api_key}"},
                ),
                timeout,
            )
        except (
            aiohttp.ClientConnectorError,
            aiohttp.ClientConnectionResetError,
            asyncio.TimeoutError,
        ) as e:
            raise APIConnectionError("failed to connect to xAI TTS WebSocket") from e
        return ws

    async def _close_ws(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        await ws.close()

    def _ensure_session(self) -> aiohttp.ClientSession:
        if not self._session:
            self._session = utils.http_context.http_session()
        return self._session

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> tts.ChunkedStream:
        return self._synthesize_with_stream(text, conn_options=conn_options)

    def stream(
        self, *, conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS
    ) -> SynthesizeStream:
        stream = SynthesizeStream(tts=self, conn_options=conn_options)
        self._streams.add(stream)
        return stream

    async def aclose(self) -> None:
        for stream in list(self._streams):
            await stream.aclose()
        self._streams.clear()


class SynthesizeStream(tts.SynthesizeStream):
    def __init__(self, *, tts: TTS, conn_options: APIConnectOptions):
        super().__init__(tts=tts, conn_options=conn_options)
        self._tts: TTS = tts
        self._opts = replace(tts._opts)
        self._segments_ch = utils.aio.Chan[tokenize.WordStream]()

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        request_id = utils.shortuuid()
        output_emitter.initialize(
            request_id=request_id,
            sample_rate=SAMPLE_RATE,
            num_channels=NUM_CHANNELS,
            stream=True,
            mime_type="audio/pcm",
        )

        async def _tokenize_input() -> None:
            input_stream = None
            async for input in self._input_ch:
                if isinstance(input, str):
                    if input_stream is None:
                        input_stream = self._opts.tokenizer.stream()
                        self._segments_ch.send_nowait(input_stream)
                    input_stream.push_text(input)
                elif isinstance(input, self._FlushSentinel):
                    if input_stream:
                        input_stream.end_input()
                    input_stream = None
            self._segments_ch.close()

        async def _run_segments() -> None:
            async for input_stream in self._segments_ch:
                await self._run_ws(input_stream, output_emitter)

        tasks = [
            asyncio.create_task(_tokenize_input()),
            asyncio.create_task(_run_segments()),
        ]
        try:
            await asyncio.gather(*tasks)
        except asyncio.TimeoutError:
            raise APITimeoutError() from None
        except aiohttp.ClientResponseError as e:
            raise APIStatusError(
                message=e.message,
                status_code=e.status,
                request_id=request_id,
                body=None,
            ) from None
        except Exception as e:
            raise APIConnectionError() from e
        finally:
            await utils.aio.gracefully_cancel(*tasks)

    async def _run_ws(
        self, input_stream: tokenize.WordStream, output_emitter: tts.AudioEmitter
    ) -> None:
        segment_id = utils.shortuuid()
        output_emitter.start_segment(segment_id=segment_id)
        input_ended = False
        audio_done = False

        async def _send_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            nonlocal input_ended
            async for word in input_stream:
                self._mark_started()
                await ws.send_str(
                    json.dumps({"type": "text.delta", "delta": word.token})
                )
            await ws.send_str(json.dumps({"type": "text.done"}))
            input_ended = True

        async def _recv_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            nonlocal audio_done
            while True:
                msg = await ws.receive()
                if msg.type in (
                    aiohttp.WSMsgType.CLOSED,
                    aiohttp.WSMsgType.CLOSE,
                    aiohttp.WSMsgType.CLOSING,
                ):
                    raise APIStatusError(
                        "xAI TTS WebSocket closed unexpectedly",
                        status_code=ws.close_code or -1,
                        body=f"{msg.data=} {msg.extra=}",
                    )
                if msg.type != aiohttp.WSMsgType.TEXT:
                    logger.warning("Unexpected xAI TTS message type %s", msg.type)
                    continue
                try:
                    payload = json.loads(msg.data)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from xAI TTS: %s", msg.data[:200])
                    continue
                event_type = payload.get("type")
                if event_type == "audio.delta":
                    delta = payload.get("delta")
                    if delta:
                        output_emitter.push(base64.b64decode(delta))
                elif event_type == "audio.done":
                    audio_done = True
                    output_emitter.end_segment()
                    break
                elif event_type == "error":
                    raise APIConnectionError(payload.get("message", "xAI TTS error"))
                else:
                    logger.debug("xAI TTS event: %s", event_type)

        ws = await self._tts._connect_ws(self._conn_options.timeout)
        tasks = [
            asyncio.create_task(_send_task(ws)),
            asyncio.create_task(_recv_task(ws)),
        ]
        try:
            await asyncio.gather(*tasks)
        finally:
            await utils.aio.gracefully_cancel(*tasks)
            await self._tts._close_ws(ws)

        if input_ended and not audio_done:
            raise APIConnectionError("xAI TTS closed without audio.done")
