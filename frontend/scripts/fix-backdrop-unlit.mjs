/**
 * Post-process the raw avatar GLB:
 * 1. Find BackdropMat
 * 2. Move its emissiveTexture → baseColorTexture (KHR_materials_unlit reads base color)
 * 3. Apply KHR_materials_unlit extension ONLY to BackdropMat
 * 4. Leave avatar material as standard PBR (so R3F lights affect it)
 */

import {
  Document,
  NodeIO,
} from '@gltf-transform/core';
import { KHRMaterialsUnlit } from '@gltf-transform/extensions';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';

const [,, input, output] = process.argv;

const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const document = await io.read(input);
const root = document.getRoot();

let found = false;
for (const material of root.listMaterials()) {
  if (material.getName() === 'BackdropMat') {
    console.log(`Found BackdropMat — applying KHR_materials_unlit`);

    // Move emissive texture to base color (unlit uses base color)
    const emissiveTex = material.getEmissiveTexture();
    const emissiveTexInfo = material.getEmissiveTextureInfo();
    if (emissiveTex && !material.getBaseColorTexture()) {
      material.setBaseColorTexture(emissiveTex);
      // Copy texture info (UV index etc)
      if (emissiveTexInfo) {
        material.getBaseColorTextureInfo()?.setTexCoord(emissiveTexInfo.getTexCoord());
      }
      material.setEmissiveTexture(null);
      material.setEmissiveFactor([0, 0, 0]);
      console.log(`  Moved emissiveTexture → baseColorTexture`);
    } else if (emissiveTex) {
      console.log(`  Already has baseColorTexture — just clearing emissive`);
      material.setEmissiveTexture(null);
      material.setEmissiveFactor([0, 0, 0]);
    }

    // Set base color factor to white (full brightness)
    material.setBaseColorFactor([1, 1, 1, 1]);

    // Apply KHR_materials_unlit extension
    const unlitExt = document.createExtension(KHRMaterialsUnlit);
    const unlit = unlitExt.createUnlit();
    material.setExtension('KHR_materials_unlit', unlit);
    console.log(`  Applied KHR_materials_unlit`);

    found = true;
  }
}

if (!found) {
  console.warn('WARNING: BackdropMat not found in GLB. Available materials:');
  for (const m of root.listMaterials()) console.warn(' ', m.getName());
}

await io.write(output, document);
console.log(`Written: ${output}`);
