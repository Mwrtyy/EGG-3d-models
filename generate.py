"""Parametric 3D reconstruction of the neon studded crystal egg.

Run: python generate.py
Units: metres (arbitrary design units); Y up; +Z front; root at bottom centre.
Requires numpy, trimesh, Pillow. Creates public/models/neon-crystal-egg.glb.
"""
from __future__ import annotations
import math
from pathlib import Path
from collections import defaultdict
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial
from trimesh.visual.texture import TextureVisuals

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'public' / 'models'
OUT.mkdir(parents=True, exist_ok=True)
S = trimesh.Scene()
np.random.seed(14)

# All registered parts share the same materials: glTF PBR emissive factors are embedded.
MATS = {
    'shell': ('#171426', 0),
    'shell2': ('#24213a', 0),
    'panel': ('#292743', 0),
    'panel_light': ('#353253', 0),
    'panel_dark': ('#201d36', 0),
    'metal': ('#3a285f', 0),
    'purple': ('#60338a', 0),
    'purple_light': ('#8543b3', 0),
    'purple_deep': ('#39204f', 0),
    'bolt': ('#1c1535', 0),
    'cyan': ('#18efff', 1.2),
    'cyan_core': ('#66fff9', 1.4),
    'cyan_frame': ('#06435a', 0),
    'magenta': ('#ff00ca', 1.0),
    'magenta_light': ('#ff3bfa', 0.85),
    'magenta_dark': ('#b700a2', 0.26),
    'magenta_panel': ('#e700d7', 0.95),
    'crystal': ('#e800d8', 0.45),
    'crystal_light': ('#ff4af6', 0.55),
    'crystal_edge': ('#fc08f2', 0.55),
    'crystal_deep': ('#960eae', 0.15),
    'pink': ('#f500e0', 0.8),
}
def rgba(hexstr):
    h=hexstr.lstrip('#');return [int(h[i:i+2],16) for i in (0,2,4)] + [255]
MATERIAL={}
for k,(hexstr,emit) in MATS.items():
    c = np.array(rgba(hexstr)[:3])/255.
    MATERIAL[k]=PBRMaterial(name=k, baseColorFactor=rgba(hexstr), metallicFactor=(.38 if k not in ('cyan','cyan_core','magenta','magenta_panel','magenta_light','pink') else .04), roughnessFactor=.40 if 'crystal' in k else (.32 if emit else .6), emissiveFactor=list(np.minimum(c*emit,1)))

# Parent nodes exist even when no geometry is attached to the group.
pivots = {
    'Egg_Root': ((0,0,0), None),
    'Body_Pivot': ((0,0,0), 'Egg_Root'),
    'Crown_Pivot': ((0,4.42,0), 'Egg_Root'),
    'Mast_Pivot': ((0,4.38,0), 'Crown_Pivot'),
    'CrystalCrown_Pivot': ((0,4.45,0), 'Crown_Pivot'),
    'Face_Pivot': ((0,0,0), 'Body_Pivot'),
    'Eye_Left_Anchor': ((-.95,1.94,1.50), 'Face_Pivot'),
    'Eye_Right_Anchor': ((.95,1.94,1.50), 'Face_Pivot'),
    'Display_Upper_Anchor': ((.26,3.42,1.44), 'Face_Pivot'),
    'Belt_Pivot': ((0,1.08,0), 'Body_Pivot'),
    'VFX_Cyan_Pivot': ((0,0,0), 'Face_Pivot'),
}
world={}
for n,(pos,par) in pivots.items():
    p=np.array(pos,float); world[n]=p
    local=p-(world.get(par, np.zeros(3)))
    S.graph.update(frame_from=par if par else 'world',frame_to=n,matrix=trimesh.transformations.translation_matrix(local))

parts=defaultdict(list)
# Relative-to-parent coordinates: parts are authored in common world space then converted
# to local coordinates during a single material-batched export. This preserves pivots.
def put(name,mesh,material,group='Body_Pivot'):
    mesh = mesh.copy();
    if len(mesh.vertices)==0:return
    mesh.apply_translation(-world[group]);
    parts[(name,group,material)].append(mesh)

def box(center,dims,material,name,group='Body_Pivot',bevel=0):
    m=trimesh.creation.box(extents=dims)
    if bevel:
        # Keep the segmented angular silhouette rather than smoothing all edges.
        pass
    m.apply_translation(center);put(name,m,material,group)

def cyl(center,r,height,mat,name,axis=(0,0,1),sections=10,group='Body_Pivot'):
    m=trimesh.creation.cylinder(radius=r,height=height,sections=sections)
    axis=np.asarray(axis,float);axis/=np.linalg.norm(axis)
    q=trimesh.geometry.align_vectors([0,0,1],axis)
    m.apply_transform(q);m.apply_translation(center);put(name,m,mat,group)

def mesh_triangles(vertices,faces,material,name,group='Body_Pivot'):
    m=trimesh.Trimesh(vertices=np.asarray(vertices,dtype=float),faces=np.asarray(faces,int),process=False)
    put(name,m,material,group)

def radial(y,ang,offset=0):
    # A smoothly varying, slightly squared oval approximating front and side profiles.
    knots=[(0.01,.35),(.10,.59),(.31,.97),(.58,1.24),(.96,1.51),(1.52,1.73),
           (2.20,1.81),(2.83,1.77),(3.34,1.65),(3.74,1.44),(4.12,1.17),
           (4.44,.82),(4.65,.49),(4.76,.23)]
    ys,rs=zip(*knots)
    r=float(np.interp(max(.01,min(y,4.76)),ys,rs))+offset
    # Front surface points toward +Z: 1.55 horizontal half width, ~1.37 depth.
    return np.array([r*math.sin(ang),y,r*.88*math.cos(ang)])

def face_normal(y,ang):
    dx=radial(y,ang+.001)-radial(y,ang-.001)
    dy=radial(min(y+0.001,4.75),ang)-radial(max(y-.001,.02),ang)
    n=np.cross(dy,dx); n=n/(np.linalg.norm(n)+1e-9)
    if np.dot(n,[math.sin(ang),0,math.cos(ang)])<0:n=-n
    return n

# Body core: low polygonal ring surface, top and bottom caps.
N=40
rlevels=np.linspace(.035,4.74,31)
v=[];f=[]
for y in rlevels:
    for k in range(N):v.append(radial(float(y),2*math.pi*k/N))
for j in range(len(rlevels)-1):
    for k in range(N):
        a=j*N+k;b=j*N+(k+1)%N;c=(j+1)*N+(k+1)%N;d=(j+1)*N+k
        f.extend([(a,b,c),(a,c,d)])
# Caps not crucial; visually occluded by the bottom rim and crown.
mesh_triangles(v,f,'shell','Hull_LowPoly')

# Armor shingles: curved individual panels in the front, sides and back with thin dark seams.
def curved_patch(ya,yb,ang_a,ang_b,offset=.022,sub=2):
    verts=[]
    for y in np.linspace(ya,yb,3):
      for a in np.linspace(ang_a,ang_b,3):verts.append(radial(y,a,offset))
    fs=[]
    for j in range(2):
      for k in range(2):
        aa=j*3+k;bb=aa+1;cc=aa+4;dd=aa+3
        fs.extend([(aa,bb,cc),(aa,cc,dd)])
    return trimesh.Trimesh(vertices=verts,faces=fs,process=False)

for row in range(12):
    ya=.42+row*.304;yb=ya+.291
    for k in range(34):
        a=-math.pi+2*math.pi*k/34+.011
        b=-math.pi+2*math.pi*(k+1)/34-.011
        m=curved_patch(ya,yb,a,b,offset=.018 if row%2 else .024)
        mat=['panel','panel_dark','shell2','panel','panel_light','panel'][((k*3+row*5)%6)]
        put('Armor_Plates',m,mat)

# Studs are actual short 8-sided cylinders anchored normal to the local hull, spread over the complete egg.
for row in range(12):
    y=.54+row*.304
    for k in range(34):
        a=-math.pi+2*math.pi*(k+.5)/34
        # Raised studs (not an image texture).
        n=face_normal(y,a)
        # place centre slightly beyond sheet to avoid floating studs
        center=radial(y,a,.022)+n*.011
        mat='bolt' if (k+row)%11==0 else ('purple' if (k+row)%4==0 else 'panel_light')
        cyl(center,.068,.055,mat,'Surface_Studs',axis=n,sections=8)

# Radius-controlled angular segmented metal arches and central spine.
def ribbon(angle,width,ya,yb,mat,name,depth=.087):
    verts=[]
    for y in np.linspace(ya,yb,6):
       for ang in [angle-width/2,angle+width/2]:verts.append(radial(float(y),ang,depth))
    faces=[]
    for i in range(5):
       k=i*2; faces.extend([(k,k+1,k+3),(k,k+3,k+2)])
    mesh_triangles(verts,faces,mat,name)

for angle in [0,-.57,.57,-1.22,1.22,math.pi]:
    if angle==0: ya,yb=.38,4.62; width=.21
    elif abs(angle)<.7:ya,yb=1.62,4.18;width=.30
    else: ya,yb=.58,3.64;width=.14
    segments=np.linspace(ya,yb,max(8,int((yb-ya)/.34))+1)
    for i in range(len(segments)-1):
        a=float(segments[i]);b=float(segments[i+1]-.008)
        ribbon(angle,width,a,b,'purple' if i%2==0 else 'metal','Armored_Ribs')
        # Colored horizontal buckles and dark raised circular bolts.
        if i%3 in (0,1):
            y=b
            ribbon(angle,width+.11,y-.050,y+.046,'purple_light' if i%3==0 else 'purple','Rib_Buckles',depth=.133)
        y=(a+b)/2
        n=face_normal(y,angle)
        cyl(radial(y,angle,.155)+n*.021,.068,.053,'bolt','Rib_Bolts',axis=n,sections=10)

# Outer side hoops following the contour, interrupted by square armor clasps.
for angle in [-1.48,1.48,-1.68,1.68]:
    ribbon(angle,.085,.57,3.35,'metal','Side_Cage_Rails',depth=.085)
    for y in [1.17,1.94,2.71,3.27]:
        ribbon(angle,.22,y-.065,y+.07,'purple_light','Side_Cage_Clips',depth=.145)

# Rectangular lit glass indicators with raised bevel frames; oriented roughly tangent
# to the hull, meaning left and right eye panels rotate outward.
def oriented_rect(name,ang,y,width,height,material,depth=.07,group='Face_Pivot'):
    n=face_normal(y,ang)
    center=radial(y,ang,.132)
    # local plane tangent x and global Y, front face normal n
    tangent=np.array([math.cos(ang),0,-.88*math.sin(ang)])
    tangent/=np.linalg.norm(tangent)
    up=np.array([0,1,0])
    # construct actual rectangular beveled-ish block with normals following face angle
    m=trimesh.creation.box(extents=[width,height,depth])
    mat=np.eye(4);mat[:3,0]=tangent;mat[:3,1]=up;mat[:3,2]=n;mat[:3,3]=center
    if np.linalg.det(mat[:3,:3])<0: mat[:3,0]*=-1
    m.apply_transform(mat)
    put(name,m,material,group)

for idx,ang in enumerate([-.55,.55]):
    side='Left' if idx==0 else 'Right'
    oriented_rect('Eye_'+side+'_MetalFrame',ang,1.86,.73,.48,'purple_deep',.12)
    oriented_rect('Eye_'+side+'_DarkGlass',ang,1.86,.62,.37,'cyan_frame',.129)
    oriented_rect('Eye_'+side+'_CyanPane',ang,1.86,.56,.28,'cyan',.16)
    oriented_rect('Eye_'+side+'_HotCore',ang,1.87,.45,.20,'cyan_core',.162)
# forehead offset right in front, as in the plate; profile display is near the leftmost visible edge
oriented_rect('Forehead_Display_Frame',.16,3.39,.81,.47,'metal',.14)
oriented_rect('Forehead_Display_Cyan',.16,3.39,.66,.31,'cyan',.161)
oriented_rect('Forehead_Display_Core',.16,3.40,.54,.22,'cyan_core',.166)

# Pixelated magenta motifs in raised individual 3D voxels. 9x7 game-invader design.
pixel_pattern=[
 '00100100',
 '00011000',
 '01111110',
 '11011011',
 '11111111',
 '10100101',
 '00100100'
]
# Pattern broadens the alien from ~0.6 width, with empty squares creating the pixel identity.
for side,angle in [('Left',-.57),('Right',.57)]:
    y0=2.36;dy=.087;da=.049
    for j,row in enumerate(pixel_pattern):
        for i,bit in enumerate(row):
            if bit=='1':
                aa=angle + (i-3.5)*da
                yy=y0+(6-j)*dy
                oriented_rect('Pink_Invader_'+side,aa,yy,.095,.091,'pink',.072)

# Lower belt: dark girdle and individual magenta glass panels between metal clasps.
for k in range(18):
    a=-math.pi+2*math.pi*k/18
    b=-math.pi+2*math.pi*(k+1)/18
    # Near front, rectangular magenta panels with a visible black seam.
    put('Belt_Girdle',curved_patch(.86,1.38,a+.009,b-.009,offset=.153), 'purple_deep','Belt_Pivot')
    put('Belt_Magenta_Plates',curved_patch(.965,1.285,a+.052,b-.054,offset=.216),'magenta_panel' if k%3 else 'magenta','Belt_Pivot')
    ribbon(a,.052,.79,1.49,'metal','Belt_Divider',depth=.234)
    # Riveted metal band near top and bottom
    for y in [.78,1.42]:
        n=face_normal(y,a)
        cyl(radial(y,a,.238)+n*.01,.052,.045,'purple','Belt_Rivets',axis=n,sections=8,group='Belt_Pivot')

# Pink base rim under the egg: faceted bright cap whose vertical silhouette is visible.
for k in range(16):
    a=2*math.pi*k/16;b=2*math.pi*(k+1)/16
    put('Base_Rim_Facets',curved_patch(.065,.28,a+.014,b-.014,offset=.083),'magenta' if k%3 else 'magenta_light')

# Main antenna/mast square bar and collars: real blocks and bolted center spine.
box((0,5.36,0),(.43,2.35,.40),'panel_dark','Mast_MainBar','Mast_Pivot')
box((0,5.81,.02),(.56,.22,.54),'purple','Mast_Collar_Upper','Mast_Pivot')
box((0,6.48,.015),(.55,.24,.53),'purple_light','Mast_Collar_Top','Mast_Pivot')
for y in [4.66,5.08,5.48,5.86,6.21]:
    cyl((0,y,.24),.072,.08,'bolt','Mast_Front_Bolts',group='Mast_Pivot')
for y in [5.79,6.47]:
    cyl((.29,y,0),.067,.05,'bolt','Mast_Side_Bolts',axis=(1,0,0),group='Mast_Pivot')

# Crystals are multi-ring pointed angular prisms. Each ring is offset to create facets
# with different shades and a hand-made asymmetrical cut.
def crystal(base, length, width, direction, which='Crystal_Spire'):
    base=np.asarray(base,float)
    direction=np.asarray(direction,float);direction/=np.linalg.norm(direction)
    ref=np.array([0,0,1.]);
    if abs(np.dot(ref,direction))>.86:ref=np.array([1.,0,0])
    U=np.cross(ref,direction); U/=np.linalg.norm(U);V=np.cross(direction,U)
    n=5
    ring0=[];ring1=[];ring2=[]
    for k in range(n):
        a=math.pi*2*k/n+.15
        vec=math.cos(a)*U+math.sin(a)*V
        ring0.append(base+vec*width*.86)
        ring1.append(base+direction*length*.19+vec*width)
        ring2.append(base+direction*length*.75+vec*width*.87)
    tip=base+direction*length
    cols=['crystal_light','crystal','crystal_edge','crystal_deep','crystal']
    # Different colors per wedge, all real triangles with facet material.
    for k in range(n):
        kk=(k+1)%n
        verts=[ring0[k],ring0[kk],ring1[kk],ring1[k],ring2[kk],ring2[k],tip]
        faces=[(0,1,2),(0,2,3),(3,2,4),(3,4,5),(5,4,6)]
        mesh_triangles(verts,faces,cols[k],which,'CrystalCrown_Pivot')

# Center pink antenna cap: offset down mast hides the crystal joint.
crystal((0,6.50,0),.73,.225,(0,1,0),'Center_Spire_Crystal')
# Asymmetric crystal wreath: most tall crystals fan out diagonally when viewed from +Z.
for i in range(12):
    a=2*math.pi*i/12
    x=.68*math.sin(a);z=.64*math.cos(a)
    y=4.36+.15*math.cos(i*2.1)
    if i in [0,1,11]:length=1.34;width=.24
    elif i in [3,4,8,9]:length=1.44;width=.27
    else:length=1.11;width=.24
    v=(math.sin(a)*.70+.02,1.04,math.cos(a)*.67)
    if math.cos(a)<-.18:
        length*=1.13; y+=.10
    crystal((x,y,z),length,width,v,'Crystal_Wreath')
    # Purple angled basal clamps bind the crystals to the shell.
    p=np.array([x,y-.02,z]);q=np.array(v);q/=np.linalg.norm(q)
    cyl(p+q*.10,.175,.23,'purple_deep','Crystal_Socket',axis=q,sections=6,group='CrystalCrown_Pivot')

# Extra front-visible shards extend the crown across both shoulders.
for x,z,y,length,w,tilt in [(-1.02,.81,4.16,1.00,.225,-.45),(-.72,1.0,4.24,1.25,.22,-.28),(.76,.96,4.24,1.23,.23,.40),(1.09,.81,4.16,1.00,.225,.59)]:
    crystal((x,y,z),length,w,(tilt,1.08,.25),'Crown_Front_Shards')

# Combine coplanar repeated pieces by semantic part and material, keeping scene hierarchy.
meshcount=0
for (name,group,material),meshes in parts.items():
    m=trimesh.util.concatenate(meshes) if len(meshes)>1 else meshes[0]
    # Keep disconnected meshes together, preserving sensible user-visible node names.
    m.visual=TextureVisuals(material=MATERIAL[material]);m.metadata['roblox_part']=name
    S.add_geometry(m, geom_name=f'{name}_{material}', node_name=f'{name}_{material}',parent_node_name=group)
    meshcount+=1

S.metadata['units']='m'
S.metadata['forward']='+Z'
S.metadata['root_pivot']=[0,0,0]
S.metadata['copyright']='Original procedural reconstruction based on user supplied sheet'
file=OUT/'neon-crystal-egg.glb'
file.write_bytes(S.export(file_type='glb'))
print(f'GLB exported: {file}, {file.stat().st_size:,} bytes')
print('Mesh primitives:',meshcount,'Grouped parts:',len(set(k[0] for k in parts)),'Triangles:',sum(len(g.faces) for g in S.geometry.values()))
print('Extent',S.bounds, 'dimensions',S.extents)
print('Named pivots:', ', '.join(pivots))
