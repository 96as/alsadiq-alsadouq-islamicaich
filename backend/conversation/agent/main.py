"""
Notes Section for the file:
- Entry point for the LiveKit agent process.
- Runs as a separate container using the same Django codebase.
- Initialises Django ORM before starting the LiveKit worker so
  the agent can read/write models directly (no REST API needed).
- Docker command:  python -m conversation.agent.main start
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django  # noqa: E402
django.setup()

from livekit.agents import cli, WorkerOptions  # noqa: E402
from conversation.agent.entrypoint import entrypoint, prewarm  # noqa: E402


def _worker_options() -> WorkerOptions:
    """Build WorkerOptions. AGENT_NUM_IDLE_PROCESSES caps the warm job processes.

    Each idle process preloads Django and Silero VAD (several hundred MB). Left
    unset, livekit-agents 1.5.1 keeps one per CPU core (up to 4) in production
    mode and none in dev mode. docker-compose.prod.yml sets it to 1 to save RAM.
    """
    kwargs = {}
    raw = os.getenv('AGENT_NUM_IDLE_PROCESSES', '').strip()
    if raw:
        try:
            kwargs['num_idle_processes'] = max(0, int(raw))
        except ValueError:
            print(f'Ignoring invalid AGENT_NUM_IDLE_PROCESSES={raw!r}', file=sys.stderr)
    return WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, **kwargs)


if __name__ == "__main__":
    cli.run_app(_worker_options())
