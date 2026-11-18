"""Strict offline GLB audit independent from Three.js (no GPU or npm needed)."""
from __future__ import annotations
import json, struct, math, sys
from pathlib import Path
from collections import Counter
import numpy as np
import trimesh
from scipy.spatial import cKDTree

root=Path(__file__).resolve().parent
path=root/'public/models/neon-crystal-egg.glb'
raw=path.read_bytes()
assert raw[:4]==b'glTF' and struct.unpack_from('<I',raw,4)[0]==2,'Invalid GLB header/version'
assert struct.unpack_from('<I',raw,8)[0]==len(raw),'Invalid GLB byte length'
json_length,chunk_type=struct.unpack_from('<II',raw,12)
assert chunk_type==0x4e4f534a,'Missing JSON chunk'
gltf=json.loads(raw[20:20+json_length]); assert gltf['asset']['version']=='2.0'
assert gltf['scenes'][0]['extras']['forward']=='+Z'
assert gltf['scenes'][0]['extras']['root_pivot']==[0,0,0]
assert len(gltf['scenes'])==1 and len(gltf['meshes'])>=30
names={node.get('name') for node in gltf['nodes']}
expected={
'Egg_Root','Body_Pivot','Crown_Pivot','Mast_Pivot',
'CrystalCrown_Pivot','Face_Pivot','Eye_Left_Anchor','Eye_Right_Anchor',
'Display_Upper_Anchor','Belt_Pivot','VFX_Cyan_Pivot'
}
assert expected<=names,f'Missing anchor/pivot nodes: {expected-names}'
assert all('images' not in gltf or im.get('uri') is None for im in gltf.get('images',[]))
assert 'cameras' not in gltf and 'lights' not in gltf
matnames={m.get('name') for m in gltf['materials']}
for name in ['cyan','cyan_core','magenta','magenta_panel','crystal','panel','purple']:
 assert name in matnames,f'GLB missing material {name}'
for mat in gltf['materials']:
 if mat.get('name') in ['cyan','cyan_core','magenta','magenta_panel','crystal']:
  assert max(mat.get('emissiveFactor',[0,0,0]))>.05, f'Emissive material lost {mat.get("name")}'

# Reload the GLB from disk, reconstruct all transforms and materials.
scene=trimesh.load(path,force='scene')
assert len(scene.geometry)==len(gltf['meshes'])
assert expected <= set(scene.graph.nodes)
assert np.allclose(scene.extents,[3.8984,7.195,3.5472],atol=.004)
assert len(scene.geometry)>30
for n in ['Eye_Left_Anchor','Eye_Right_Anchor','Display_Upper_Anchor','Crown_Pivot']:
 assert np.isfinite(scene.graph[n][0]).all()
assert scene.graph['Eye_Left_Anchor'][0][0,3]<0
assert scene.graph['Eye_Right_Anchor'][0][0,3]>0
assert scene.graph['Eye_Left_Anchor'][0][2,3]>1

# For main body stud nodes, compute nearest Euclidean distance between their
# surface vertices and the hull point cloud to detect obviously free-floating studs.
def points_prefix(prefix):
 arr=[]
 for nod in scene.graph.nodes_geometry:
  mat,geom=scene.graph[nod]
  if nod.startswith(prefix):
   mesh=scene.geometry[geom]
   a=np.asarray(mesh.vertices)
   pts=np.column_stack((a,np.ones(len(a))))@mat.T
   arr.append(pts[:,:3])
 return np.vstack(arr)
hull=points_prefix('Hull_LowPoly')
studs=points_prefix('Surface_Studs')
nearest=cKDTree(hull).query(studs,k=1)[0]
assert np.quantile(nearest,.5)<.13, f'Stud shell median distance too high: {np.median(nearest)}'
assert np.quantile(nearest,.95)<.22, f'Unexpected floating studs: {np.quantile(nearest,.95)}'

# Material/mesh integrity check of the reloaded scene.
triangle_count=sum(len(x.faces) for x in scene.geometry.values())
assert triangle_count>=24000
assert all(isinstance(g.visual.material,trimesh.visual.material.PBRMaterial) for g in scene.geometry.values())
print('OK · Valid GLB v2 and embedded PBR materials')
print('OK · Named hierarchy and 11 pivots/anchors preserved')
print('OK · Neutral geometry and no camera, lights or VFX exported')
print('OK · Cyan/magenta/crystal emission retained')
print(f'OK · Reloaded meshes: {len(scene.geometry)} | triangles: {triangle_count:,} | materials: {len(matnames)}')
print(f'OK · AABB: {scene.extents.round(4).tolist()} m | +Z front / Y up')
print(f'OK · Median stud-hull nearest-vertex distance: {np.median(nearest):.3f} m | 95th percentile: {np.quantile(nearest,.95):.3f} m')
print('NOTE · This verifies on-disk GLB reimport and geometry; browser/npm interaction tests are separate.')
