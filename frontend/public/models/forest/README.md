# Forest model drop folder

Put the Blender forest here. Do not commit sample files.

- `forest.glb` and `forest-manifest.json` are written by the pipeline in `blender-mcp/forest-pipeline` (`prepare-forest.ps1 -Blend <file> -Install <worktree>`).
- With no manifest here, the forest scene uses the built-in procedural forest.
- The node-name contract (AvatarSpot, CamStart, CamTalk, Sway_*, Click_*) is described in `frontend/src/features/child/components/forest/README.md`.
