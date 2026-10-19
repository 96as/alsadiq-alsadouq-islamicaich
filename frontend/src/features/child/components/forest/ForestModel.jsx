/* Applies the Blender model to the runtime object by design. */
/* eslint-disable react-hooks/immutability */
import { useEffect, useMemo } from 'react';
import { assetUrl } from '../../../../utils/assetUrl';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import { useForest } from './forestContext';
import { addTriangles } from './runtime';

const SWAY_HEAD = 'uniform float uTime;\nuniform float uSway;\nuniform vec3 uSwayBox;\n';

/** True when the node, or any ancestor, has a name that starts with the prefix. */
function hasNamedAncestor(node, prefix) {
  for (let n = node; n; n = n.parent) {
    if (n.name && n.name.startsWith(prefix)) return true;
  }
  return false;
}

/** The nearest node at or above `node` whose name starts with the prefix. */
function namedAncestor(node, prefix) {
  let n = node;
  while (n && !(n.name && n.name.startsWith(prefix))) n = n.parent;
  return n || null;
}

/**
 * The Blender object a node belongs to. three.js splits one object into
 * several nodes: a multi-material mesh becomes a Group of primitive meshes
 * ("Click_shelf_1", "Click_shelf_2", with no glTF node name of their own), and
 * the pipeline moves the mesh of an object with children into a same-named
 * child ("Click_lamp" > "Click_lamp_1"). Walks back up to the object.
 */
function objectOf(node) {
  let n = node;
  while (n.parent) {
    const own = n.userData.name;
    const part = own === undefined ? n.isMesh && n.parent.isGroup : own === n.parent.userData.name;
    if (!part) break;
    n = n.parent;
  }
  return n;
}

/** The Click_ object for a Click_-named node (its parts all report the object's name). */
function clickObject(node) {
  const o = objectOf(node);
  return o.name.startsWith('Click_') ? o : node;
}

// three.js strips dots from node names ("CamStart.001" becomes "CamStart001").
const EMPTY_NAME = /^(AvatarSpot|CamStart|CamStartLook|CamTalk|CamTalkLook)(\.?\d+)?$/;

/**
 * Wind sway for "Sway_*" meshes. The pipeline quantises positions, so the raw
 * local y is tiny; the height weight comes from the vertex's WORLD y measured
 * against the mesh's world bounding box (uSwayBox = base y, height, amplitude).
 */
function makeSway(material, rt, box) {
  const m = material.clone();
  const height = Math.max(box.max.y - box.min.y, 0.05);
  const amp = 0.16 * THREE.MathUtils.clamp(height, 0.2, 2);
  const swayBox = new THREE.Vector3(box.min.y, height, amp);
  m.onBeforeCompile = (shader) => {
    shader.uniforms.uTime = rt.shared.uTime;
    shader.uniforms.uSway = rt.shared.uSway;
    shader.uniforms.uSwayBox = { value: swayBox };
    shader.vertexShader = SWAY_HEAD + shader.vertexShader.replace(
      '#include <begin_vertex>',
      `#include <begin_vertex>
       vec4 swWorld = modelMatrix * vec4(transformed, 1.0);
       float swH = clamp((swWorld.y - uSwayBox.x) / uSwayBox.y, 0.0, 1.0);
       float swPh = swWorld.x * 0.7 + swWorld.z * 0.45;
       vec3 swOff = vec3(
         sin(uTime * 1.3 + swPh) + 0.4 * sin(uTime * 2.6 + swPh * 1.9),
         0.0,
         0.45 * cos(uTime * 1.1 + swPh * 1.3)
       ) * (swH * swH * uSwayBox.z * uSway);
       transformed += inverse(mat3(modelMatrix)) * swOff;`,
    );
  };
  m.customProgramCacheKey = () => 'forest-sway-world';
  return m;
}

function worldPos(node) {
  const v = new THREE.Vector3();
  node.updateWorldMatrix(true, false);
  return node.getWorldPosition(v);
}

/**
 * Loads the Blender-made forest listed in forest-manifest.json and wires up
 * the node-name contract (see README.md in this folder).
 * Calls onLoaded({ hasBackdrop, clicks }) when the model is in the scene.
 */
export default function ForestModel({ manifest, onLoaded }) {
  const rt = useForest();
  const url = `${assetUrl(manifest.model)}${manifest.model.includes('?') ? '&' : '?'}v=${manifest.version}`;
  // Draco off (nothing is fetched from a CDN); drei decodes meshopt by default.
  const gltf = useGLTF(url, false);

  const prepared = useMemo(() => {
    const root = gltf.scene.clone(true);
    const empties = {};
    const clicks = new Set();
    const drop = [];
    const swayMaterials = [];
    const swayBoxes = new Map(); // one box per object, so the parts of a multi-material mesh bend together
    let tris = 0;
    let hasBackdrop = false;
    root.updateMatrixWorld(true);
    root.traverse((n) => {
      if (n.isLight || n.isCamera) {
        drop.push(n);
        return;
      }
      if (EMPTY_NAME.test(n.name)) empties[n.name.replace(/\.?\d+$/, '')] = worldPos(n);
      if (/^(Sky|Backdrop)/i.test(n.name)) hasBackdrop = true;
      if (n.name.startsWith('Click_')) clicks.add(clickObject(n).name);
      if (n.isMesh) {
        tris += n.geometry.index ? n.geometry.index.count / 3 : n.geometry.attributes.position.count / 3;
        if (hasNamedAncestor(n, 'Sway_')) {
          const owner = objectOf(n);
          if (!swayBoxes.has(owner)) swayBoxes.set(owner, new THREE.Box3().setFromObject(owner));
          const box = swayBoxes.get(owner);
          const wrap = (mm) => {
            const sm = makeSway(mm, rt, box);
            swayMaterials.push(sm);
            return sm;
          };
          n.material = Array.isArray(n.material) ? n.material.map(wrap) : wrap(n.material);
        }
      }
    });
    drop.forEach((n) => n.parent && n.parent.remove(n));
    return { root, empties, clicks: [...clicks], tris: Math.round(tris), hasBackdrop, swayMaterials };
  }, [gltf, rt]);

  useEffect(() => () => prepared.swayMaterials.forEach((m) => m.dispose()), [prepared]);

  useEffect(() => {
    const { empties } = prepared;
    const prevWide = { pos: rt.poses.wide.pos.clone(), look: rt.poses.wide.look.clone() };
    const prevTalk = { pos: rt.poses.talk.pos.clone(), look: rt.poses.talk.look.clone() };
    if (empties.AvatarSpot) rt.modelFeet = empties.AvatarSpot.clone();
    if (empties.CamStart && empties.CamStartLook) {
      rt.poses.wide.pos.copy(empties.CamStart);
      rt.poses.wide.look.copy(empties.CamStartLook);
    }
    if (empties.CamTalk && empties.CamTalkLook) {
      rt.poses.talk.pos.copy(empties.CamTalk);
      rt.poses.talk.look.copy(empties.CamTalkLook);
    }
    addTriangles(rt, 'model', prepared.tris);
    if (onLoaded) onLoaded({ hasBackdrop: prepared.hasBackdrop, clicks: prepared.clicks });
    return () => {
      rt.modelFeet = null;
      rt.poses.wide.pos.copy(prevWide.pos);
      rt.poses.wide.look.copy(prevWide.look);
      rt.poses.talk.pos.copy(prevTalk.pos);
      rt.poses.talk.look.copy(prevTalk.look);
      addTriangles(rt, 'model', 0);
    };
  }, [prepared, rt, onLoaded]);

  // never leave the pointer cursor behind if the model unmounts while hovered
  useEffect(
    () => () => {
      document.body.style.cursor = '';
    },
    [],
  );

  const onClick = (e) => {
    const n = namedAncestor(e.object, 'Click_');
    if (!n) return;
    e.stopPropagation();
    rt.bus.dispatchEvent(new CustomEvent('click-target', { detail: clickObject(n).name }));
  };
  const onOver = (e) => {
    if (namedAncestor(e.object, 'Click_')) document.body.style.cursor = 'pointer';
  };
  const onOut = () => {
    document.body.style.cursor = '';
  };

  return <primitive object={prepared.root} onClick={onClick} onPointerOver={onOver} onPointerOut={onOut} />;
}
