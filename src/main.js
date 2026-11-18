import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

// Exported GLB is the single source of truth. No scenery/cameras/lamps/VFX are in it.
const MODEL_URL = '/models/neon-crystal-egg.glb';
const viewport = document.querySelector('#viewport');
const status = document.querySelector('#status');
const shapeCount = document.querySelector('#shapeCount');
const testResult = document.querySelector('#testResult');
const vfxToggle = document.querySelector('#vfxToggle');
const rotateToggle = document.querySelector('#rotateToggle');
const loader = new GLTFLoader();
const scene = new THREE.Scene();
scene.background = new THREE.Color('#222130');
scene.fog = new THREE.FogExp2('#222130', 0.012);
const camera = new THREE.PerspectiveCamera(36, 1, .06, 140);
camera.position.set(0, 3.70, 14.8);
const renderer = new THREE.WebGLRenderer({ alpha: false, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setSize(viewport.clientWidth, viewport.clientHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.38;
renderer.shadowMap.enabled = false;
viewport.prepend(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 3.55, 0);
controls.enableDamping = true;
controls.dampingFactor = .08;
controls.enablePan = true;
controls.minDistance = 5;
controls.maxDistance = 32;
controls.maxPolarAngle = Math.PI * .96;
controls.autoRotateSpeed = 1.3;

const lightAmbient = new THREE.HemisphereLight(0xbbcaff, 0x28132e, 2.1);
scene.add(lightAmbient);
const key = new THREE.DirectionalLight(0xc8d4ff, 3.1); key.position.set(5, 10, 8); scene.add(key);
const rim = new THREE.DirectionalLight(0xff2cee, 2.0); rim.position.set(-5, 7, -6); scene.add(rim);
const fill = new THREE.DirectionalLight(0x8674ff, 1.2); fill.position.set(-7, 3, 5); scene.add(fill);

const floorCanvas = document.createElement('canvas');floorCanvas.width = floorCanvas.height = 128;
const fctx = floorCanvas.getContext('2d');
const grad = fctx.createRadialGradient(64, 64, 5, 64, 64, 64);
grad.addColorStop(0,'rgba(10,7,19,.6)');grad.addColorStop(.4,'rgba(15,9,28,.35)');grad.addColorStop(1,'rgba(15,9,28,0)');
fctx.fillStyle=grad;fctx.fillRect(0,0,128,128);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(7.2, 5.5),new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(floorCanvas),transparent:true,depthWrite:false}));
floor.rotation.x=-Math.PI/2;floor.position.y=.01;scene.add(floor);

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(viewport.clientWidth,viewport.clientHeight), .72, .65, .80);
composer.addPass(bloom);
composer.addPass(new OutputPass());

let model = null;
let fxRoot = new THREE.Group();scene.add(fxRoot);
let fxAnchors = [];
let pulseParticles = null;
let pulseRing = null;
let pulseTime = -100;
let currentView = 'front';
let timeLast=performance.now();
let vfxEnabled=true;

function resize() {
  const {clientWidth:w,clientHeight:h} = viewport;
  if (!w || !h) return;
  camera.aspect = w / h;camera.updateProjectionMatrix();
  renderer.setSize(w,h,false);composer.setSize(w,h);
}
new ResizeObserver(resize).observe(viewport);

const viewPos = {
  front: [0,3.68,14.8],
  left: [13.9,3.68,5.35], // 69° oblique: matches supplied labeled profile (not orthographic)
  back: [0,3.68,-14.8],
  quarter: [10.2,5.8,11.5],
  top: [0.005,17.8,0.002],
};
function setView(keyName) {
  if (!(keyName in viewPos)) return;
  currentView=keyName;
  camera.position.set(...viewPos[keyName]);
  camera.up.set(0, keyName==='top'?0:1, keyName==='top'?-1:0);
  controls.target.set(0,3.55,0);
  controls.update();
  document.querySelectorAll('.view-btn').forEach(b=>b.classList.toggle('selected',b.dataset.view===keyName));
  document.querySelector('#qualityChip').textContent = keyName.toUpperCase()+' / GLB';
}
document.querySelectorAll('.view-btn').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
window.addEventListener('keydown',e=>{
  if (e.target instanceof HTMLElement && ['INPUT','TEXTAREA'].includes(e.target.tagName)) return;
  const v=['front','left','back','quarter','top'][Number(e.key)-1];
  if(v)setView(v);
});

function attachSprites() {
  const cv=document.createElement('canvas');cv.width=cv.height=128;
  const x=cv.getContext('2d');const g=x.createRadialGradient(64,64,2,64,64,64);
  g.addColorStop(0,'rgba(255,255,255,.75)');g.addColorStop(.12,'rgba(120,255,250,.45)');g.addColorStop(.35,'rgba(0,240,250,.16)');g.addColorStop(1,'rgba(0,220,250,0)');
  x.fillStyle=g;x.fillRect(0,0,128,128);
  const texture=new THREE.CanvasTexture(cv);
  const points=[
    ['Eye_Left_Anchor',0x22ffff,[0,.0,0],.93],
    ['Eye_Right_Anchor',0x22ffff,[0,.0,0],.93],
    ['Display_Upper_Anchor',0x22ffff,[0,0,0],1.00],
    ['CrystalCrown_Pivot',0xff11e0,[0,1.00,0],1.35],
  ];
  for (const [name,color,pos,sz] of points) {
    const anchor=model?.getObjectByName(name);
    if(!anchor)continue;
    const sprite=new THREE.Sprite(new THREE.SpriteMaterial({map:texture,color,blending:THREE.AdditiveBlending,depthWrite:false,transparent:true,opacity:name.startsWith('Crystal')?.28:.38}));
    sprite.scale.set(sz*1.6,sz*1.25,1);
    fxRoot.add(sprite);
    const light=new THREE.PointLight(color,name.startsWith('Crystal')?3.0:1.25,name.startsWith('Crystal')?5.5:2.2,2);
    scene.add(light);
    fxAnchors.push({anchor,sprite,light,pos: new THREE.Vector3(...pos)});
  }
  // One-shot pulse. Positions are updated in the coordinate system of CrystalCrown_Pivot.
  pulseRing=new THREE.Mesh(new THREE.TorusGeometry(.65,.019,5,80),new THREE.MeshBasicMaterial({color:0xff38ef,transparent:true,depthWrite:false,opacity:0,blending:THREE.AdditiveBlending}));
  pulseRing.rotation.x=Math.PI/2;fxRoot.add(pulseRing);
  const cloud=new Float32Array(48*3);
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.BufferAttribute(cloud,3));
  pulseParticles=new THREE.Points(geometry,new THREE.PointsMaterial({color:0xff65f1,size:.07,transparent:true,opacity:0,blending:THREE.AdditiveBlending,depthWrite:false,sizeAttenuation:true}));
  fxRoot.add(pulseParticles);
  updateFXVisibility();
}
function clearFX() {
  for(const {sprite,light} of fxAnchors){sprite.material.dispose();scene.remove(light);}
  fxAnchors=[];
  if(pulseRing){pulseRing.geometry.dispose();pulseRing.material.dispose();}
  if(pulseParticles){pulseParticles.geometry.dispose();pulseParticles.material.dispose();}
  fxRoot.clear();pulseRing=null;pulseParticles=null;
}
function updateFXVisibility() {
  fxRoot.visible=vfxEnabled;
  fxAnchors.forEach(({light})=>light.visible=vfxEnabled);
  bloom.strength=vfxEnabled?.72:0;
  document.querySelector('#replayBtn').disabled=!vfxEnabled;
}
function playPulse(){if(vfxEnabled)pulseTime=performance.now()/1000;}
document.querySelector('#replayBtn').addEventListener('click',playPulse);
vfxToggle.addEventListener('change',()=>{vfxEnabled=vfxToggle.checked;updateFXVisibility();});
rotateToggle.addEventListener('change',()=>{controls.autoRotate=rotateToggle.checked;});

const tmp = new THREE.Vector3();
function animate(now){
  const t=now/1000,dt=Math.min((now-timeLast)/1000,.1);timeLast=now;
  if(vfxEnabled && model){
    for(const {anchor,sprite,light,pos} of fxAnchors){
      anchor.localToWorld(tmp.copy(pos));sprite.position.copy(tmp);light.position.copy(tmp);
      sprite.material.opacity=.30+Math.sin(t*3.5)*.07;
    }
    const anchor=model.getObjectByName('CrystalCrown_Pivot');
    if(anchor && pulseRing && pulseParticles){
      anchor.localToWorld(tmp.set(0,.72,0));pulseRing.position.copy(tmp);
      const elapsed=t-pulseTime;const phase=Math.max(0,Math.min(1,elapsed/1.75));
      const opacity=elapsed>=0 && elapsed<1.75?(1-phase)*.72:0;
      pulseRing.material.opacity=opacity;pulseRing.scale.setScalar(.4+phase*2.5);
      pulseParticles.material.opacity=opacity;
      const attr=pulseParticles.geometry.attributes.position;
      for(let j=0;j<48;j++){
        const angle=j*2.39996+elapsed*.36;
        const r=.35+((j*19)%17)/17*1.2+Math.max(0,elapsed)*.28;
        attr.setXYZ(j,tmp.x+Math.cos(angle)*r,tmp.y+(j%11)/11*1.35+phase*.5,tmp.z+Math.sin(angle)*r);
      }
      attr.needsUpdate=true;
    }
  }
  controls.update();composer.render(dt);requestAnimationFrame(animate);
}
requestAnimationFrame(animate);

function sceneReport(root) {
  let meshes=0,triangles=0;const mats=new Set();const nodes=new Map();
  root.traverse(o=>{
    nodes.set(o.name, o);
    if(o.isMesh){meshes++;triangles+=o.geometry.index?o.geometry.index.count/3:o.geometry.attributes.position.count/3;
      for(const m of Array.isArray(o.material)?o.material:[o.material])mats.add(m.name);
    }
  });
  const box=new THREE.Box3().setFromObject(root);
  return {meshes,triangles:Math.round(triangles),materials:mats.size,bounds:[...box.min.toArray(),...box.max.toArray()],nodes};
}
function compareModels(a,b){
  const old=sceneReport(a),current=sceneReport(b);
  const must=['Egg_Root','Body_Pivot','Crown_Pivot','CrystalCrown_Pivot','Mast_Pivot','Face_Pivot','Eye_Left_Anchor','Eye_Right_Anchor','Display_Upper_Anchor','Belt_Pivot'];
  const missing=must.filter(n=>!current.nodes.has(n));
  let maximum=0;
  for(let i=0;i<6;i++) maximum=Math.max(maximum,Math.abs(old.bounds[i]-current.bounds[i]));
  const ok=!missing.length&&old.meshes===current.meshes&&old.materials===current.materials&&maximum<.0005;
  return {ok,old,current,maximum,missing};
}

async function loadModel(buffer=null){
  const data=buffer??await (await fetch(MODEL_URL)).arrayBuffer();
  const gltf=await new Promise((resolve,reject)=>loader.parse(data,'',resolve,reject));
  const next=gltf.scene;
  if(model){clearFX();scene.remove(model);}
  model=next;scene.add(next);
  model.updateMatrixWorld(true);
  const report=sceneReport(next);
  shapeCount.textContent=`${report.meshes} MAILLAGES · ${report.triangles.toLocaleString('fr-FR')} TRIANGLES`;
  attachSprites();
  status.textContent='GLB CHARGÉ · STRUCTURE COMPLÈTE';
  document.querySelector('#loading').hidden=true;
  return {data,report};
}
try {
  await loadModel();setView('front');
}catch(err){
  console.error(err);status.textContent='ÉCHEC DU CHARGEMENT';
  document.querySelector('#loading').innerHTML=`<strong>IMPOSSIBLE DE CHARGER LE GLB</strong><small>Contrôler la console et le chemin /models/neon-crystal-egg.glb</small>`;
  testResult.textContent=String(err);
}

async function reloadAndVerify(arrayBuffer=null){
  testResult.textContent='Lecture, analyse et vérification du GLB...';
  try {
    const before=model;
    const {report}=await loadModel(arrayBuffer);
    const diff=compareModels(before,model);
    testResult.textContent=diff.ok
      ? `✓ VALIDÉ · ${report.meshes} maillages, ${report.materials} matériaux, ${report.triangles.toLocaleString('fr-FR')} triangles ; pivots et bornes identiques (Δ max ${diff.maximum.toFixed(6)} m).`
      : `⚠ ÉCART DÉTECTÉ · ${diff.missing.join(', ')} · Δ dimensions ${diff.maximum.toFixed(6)} m`;
    testResult.classList.toggle('pass',diff.ok);
    return diff;
  } catch(e){testResult.textContent=`✕ ERREUR : ${e.message}`;throw e;}
}
document.querySelector('#reloadBtn').addEventListener('click',()=>reloadAndVerify());
document.querySelector('#downloadBtn').addEventListener('click',async()=>{
  const response=await fetch(MODEL_URL);if(!response.ok)throw Error(`GLB HTTP ${response.status}`);
  const bytes=await response.arrayBuffer();
  const url=URL.createObjectURL(new Blob([bytes],{type:'model/gltf-binary'}));
  const link=document.createElement('a');link.href=url;link.download='neon-crystal-egg.glb';
  document.body.appendChild(link);link.click();link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),3000);
  // Parse the exact downloaded bytes, not just the original parsed scene.
  await reloadAndVerify(bytes);
});

const referenceImg=document.querySelector('#referenceImg');
document.querySelectorAll('.tab').forEach(b=>b.addEventListener('click',()=>{
  const side=b.dataset.ref;
  referenceImg.src=side==='front'?'/reference/front.png':'/reference/left.png';
  referenceImg.alt=side==='front'?'Référence face':'Référence profil gauche';
  document.querySelector('#referenceLabel').textContent=side==='front'?'01 — FACE':'02 — PROFIL GAUCHE';
  document.querySelectorAll('.tab').forEach(el=>el.classList.toggle('active',el===b));
  if(side==='front'||side==='left')setView(side);
}));

// A small read-only test surface for automated browser verification.
window.__EGG_QA__={scene,renderer,camera,get model(){return model;},sceneReport,compareModels,reloadAndVerify,setView};
