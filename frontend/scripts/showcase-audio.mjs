// integrate-1: showcase-only build step. Not part of a normal build.
//
// The meadow page plays a few REAL clips with text-timed lip sync. The clips live in the gitignored
// frontend/dev-audio/ folder (never committed). On a showcase build (VITE_SHOWCASE=1) this plugin
// converts the chosen clips to small mono mp3 files (default 80 kbps) and copies their alignment
// JSON next to them, plus a manifest.json the page reads:
//
//   dist-showcase/showcase-audio/manifest.json
//   dist-showcase/showcase-audio/<id>.mp3
//   dist-showcase/showcase-audio/<id>.align.json
//
// Nothing here ends up in git: dist-showcase is ignored and the source audio never moves. If the
// source clips or ffmpeg are missing the build still succeeds and writes an EMPTY manifest, and
// the page falls back to its made-up voice (and says so).
//
// Settings (environment):
//   SHOWCASE_AUDIO_DIR   the folder holding eval-ar/ and eval-en/   (default: frontend/dev-audio)
//   FFMPEG_PATH          the ffmpeg executable                      (default: ffmpeg on PATH, or the
//                        vibe copy on Majd's PC)
//   SHOWCASE_AUDIO_KBPS  mp3 bitrate, 64 to 96                      (default 80)
//
// The clips are children's lines (a greeting, a praise, a story sentence, a goodnight, one English
// line). None is scripture. `talk` is the talk style the page gives the avatar director while the
// clip plays (the agent would publish it as al.talk_style).
import { spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { resolve } from 'node:path'

export const SHOWCASE_CLIPS = [
  { id: 'ar01', src: 'eval-ar/ar01.diac', lang: 'ar', talk: 'explain', en: 'Greeting', ar: 'تحية' },
  { id: 'ar20', src: 'eval-ar/ar20.diac', lang: 'ar', talk: 'praise', en: 'Praise', ar: 'مدح' },
  { id: 'ar04', src: 'eval-ar/ar04.diac', lang: 'ar', talk: 'story', en: 'White cat', ar: 'القطة' },
  { id: 'ar30', src: 'eval-ar/ar30.diac', lang: 'ar', talk: 'gentle', en: 'Goodnight', ar: 'تصبح على خير' },
  { id: 'en02', src: 'eval-en/en02', lang: 'en', talk: 'explain', en: 'Bedtime game', ar: 'لعبة' },
]

const VIBE_FFMPEG = resolve(homedir(), 'AppData/Local/vibe/ffmpeg.exe')

function findFfmpeg() {
  if (process.env.FFMPEG_PATH) return process.env.FFMPEG_PATH
  const probe = spawnSync('ffmpeg', ['-version'], { stdio: 'ignore' })
  if (!probe.error && probe.status === 0) return 'ffmpeg'
  return existsSync(VIBE_FFMPEG) ? VIBE_FFMPEG : ''
}

export default function showcaseAudio(root, outDir) {
  return {
    name: 'showcase-audio',
    apply: 'build',
    closeBundle() {
      const dest = resolve(root, outDir, 'showcase-audio')
      rmSync(dest, { recursive: true, force: true })
      mkdirSync(dest, { recursive: true })
      const srcDir = process.env.SHOWCASE_AUDIO_DIR || resolve(root, 'dev-audio')
      const ffmpeg = findFfmpeg()
      const kbps = Math.min(96, Math.max(64, Number(process.env.SHOWCASE_AUDIO_KBPS) || 80))
      const clips = []
      if (!ffmpeg) console.warn('[showcase-audio] ffmpeg not found: the meadow page keeps its made-up voice')
      for (const c of ffmpeg ? SHOWCASE_CLIPS : []) {
        const wav = resolve(srcDir, `${c.src}.wav`)
        const align = resolve(srcDir, `${c.src}.align.json`)
        if (!existsSync(wav) || !existsSync(align)) {
          console.warn(`[showcase-audio] missing source for ${c.id}, skipped`)
          continue
        }
        const mp3 = resolve(dest, `${c.id}.mp3`)
        const r = spawnSync(ffmpeg, ['-y', '-v', 'error', '-i', wav, '-ac', '1', '-ar', '44100', '-codec:a', 'libmp3lame', '-b:a', `${kbps}k`, mp3], {
          stdio: 'inherit',
        })
        if (r.status !== 0) {
          console.warn(`[showcase-audio] ffmpeg failed for ${c.id}, skipped`)
          continue
        }
        // Keep only what the page needs from the alignment: the text and the per-character times.
        const a = JSON.parse(readFileSync(align, 'utf8'))
        const slim = { text: a.text, sr: a.sr, duration: a.duration, characters: a.characters, starts: a.starts, ends: a.ends }
        writeFileSync(resolve(dest, `${c.id}.align.json`), JSON.stringify(slim))
        clips.push({ id: c.id, lang: c.lang, talk: c.talk, en: c.en, ar: c.ar, text: a.text, audio: `${c.id}.mp3`, align: `${c.id}.align.json`, duration: a.duration })
      }
      writeFileSync(resolve(dest, 'manifest.json'), JSON.stringify({ version: 1, kbps, clips }, null, 1))
      console.log(`[showcase-audio] ${clips.length} clip(s) at ${kbps} kbps in ${outDir}/showcase-audio`)
    },
  }
}
