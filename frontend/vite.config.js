import process from 'node:process'
import { existsSync, rmSync } from 'node:fs'
import { resolve } from 'node:path'
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import showcaseAudio from './scripts/showcase-audio.mjs' // integrate-1

// The showcase needs avatar-animated.glb (with its .json); avatar-web.glb (the old fallback) is no longer shipped. The
// two source models in public/ are 43 MB each, so leave them, the placeholder files and the forest
// drop-folder notes out of dist-showcase.
const dropHeavyModels = (outDir) => ({
  name: 'showcase-drop-heavy-models',
  apply: 'build',
  closeBundle() {
    for (const f of ['avatar/avatar.glb', 'avatar/avatar-round7.glb', 'avatar/.gitkeep', 'forest/README.md']) {
      rmSync(resolve(import.meta.dirname, outDir, 'models', f), { force: true })
    }
  },
})

// integrate-1: the dev preview pages read the gitignored dev-audio/ folder with import.meta.glob. In
// a showcase build that must find nothing, or every clip in the folder would be copied into dist.
// The meadow page gets its few clips from showcase-audio.mjs instead.
const noDevAudioGlobs = () => ({
  name: 'showcase-no-dev-audio-globs',
  enforce: 'pre',
  apply: 'build',
  transform(code) {
    if (!code.includes('import.meta.glob') || !code.includes('/dev-audio/')) return null
    return { code: code.replaceAll("'/dev-audio/", "'/__no-dev-audio__/"), map: null }
  },
})

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Showcase build (VITE_SHOWCASE=1): the preview pages for the team site, built with
  // `vite build --base /page/` into dist-showcase. Off by default; a normal build is unchanged.
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  const showcase = (process.env.VITE_SHOWCASE ?? env.VITE_SHOWCASE) === '1'

  // A bind mount from Windows into the Linux dev container sends no file-change events, so the dev
  // server kept serving stale modules. docker-compose.yml (dev only) sets VITE_WATCH_POLL=1 to poll.
  // A static prod build never starts the dev server, so this has no effect there.
  const poll = process.env.VITE_WATCH_POLL === '1' || Boolean(process.env.CHOKIDAR_USEPOLLING)

  return {
    ...(poll ? { server: { watch: { usePolling: true, interval: 300 } } } : {}),
    plugins: [
      react(),
      tailwindcss(),
      ...(showcase ? [noDevAudioGlobs(), dropHeavyModels('dist-showcase'), showcaseAudio(import.meta.dirname, 'dist-showcase')] : []),
    ],
    ...(showcase
      ? {
          define: {
            'import.meta.env.VITE_FOREST_MANIFEST': JSON.stringify(
              existsSync(resolve(import.meta.dirname, 'public/models/forest/forest-manifest.json')) ? '1' : '0',
            ),
          },
        }
      : {}),
    ...(showcase
      ? {
          build: {
            outDir: 'dist-showcase',
            rollupOptions: {
              input: {
                main: resolve(import.meta.dirname, 'index.html'),
                'avatar-component-preview': resolve(import.meta.dirname, 'avatar-component-preview.html'),
                'avatar-preview': resolve(import.meta.dirname, 'avatar-preview.html'),
              },
            },
          },
        }
      : {}),
  }
})
