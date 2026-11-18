"""Offscreen model quality-control renders. Uses VTK EGL without a browser."""
import sys
from pathlib import Path
import numpy as np
import trimesh
import vtk
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from PIL import Image,ImageOps,ImageDraw,ImageFont,ImageEnhance
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'public/models/neon-crystal-egg.glb'
SC=trimesh.load(SRC,force='scene')
OUT=ROOT/'comparisons';OUT.mkdir(exist_ok=True)

REN=vtk.vtkRenderer();REN.SetBackground(.125,.123,.164)
REN.SetBackground2(.32,.31,.38);REN.GradientBackgroundOn()
RW=vtk.vtkRenderWindow();RW.SetOffScreenRendering(1);RW.AddRenderer(REN)
RW.SetSize(780,950);RW.SetMultiSamples(8)

for nod in SC.graph.nodes_geometry:
    tf,geom=SC.graph[nod];m=SC.geometry[geom]
    vert=np.asarray(m.vertices,float)
    homo=np.column_stack((vert,np.ones(len(vert))))
    vert=(homo@tf.T)[:,:3]
    points=vtk.vtkPoints();points.SetData(numpy_to_vtk(np.ascontiguousarray(vert)))
    faces=np.asarray(m.faces,np.int64)
    cells=vtk.vtkCellArray()
    packed=np.column_stack((np.full(len(faces),3),faces)).reshape(-1)
    cells.SetCells(len(faces),numpy_to_vtk(packed,deep=True,array_type=vtk.VTK_ID_TYPE))
    pd=vtk.vtkPolyData();pd.SetPoints(points);pd.SetPolys(cells)
    normals=vtk.vtkPolyDataNormals();normals.SetInputData(pd);normals.ComputeCellNormalsOn();normals.SplittingOn();normals.ConsistencyOn();normals.Update()
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
    actor=vtk.vtkActor();actor.SetMapper(mapper)
    mat=m.visual.material
    c=np.array(mat.baseColorFactor[:3])/255.
    actor.GetProperty().SetColor(c)
    # Emission simplified by stronger ambient, not actual PBR emission.
    glow=float(np.max(getattr(mat,'emissiveFactor',[0,0,0])))
    actor.GetProperty().SetAmbient(min(.52+glow*.3,1.0));actor.GetProperty().SetDiffuse(.6 if glow<.1 else .38)
    actor.GetProperty().SetSpecular(.34 if glow<.1 else .14);actor.GetProperty().SetSpecularPower(24)
    REN.AddActor(actor)
for pos,power,warm in [((8,12,12),.9,(.85,.9,1)),((-9,4,3),.65,(.8,.6,1)),((2,8,-8),.75,(1,.45,.94))]:
    light=vtk.vtkLight();light.SetPosition(*pos);light.SetFocalPoint(0,3.4,0);light.SetIntensity(power);light.SetColor(*warm);REN.AddLight(light)

camera=REN.GetActiveCamera();camera.SetFocalPoint(0,3.65,0);camera.ParallelProjectionOn();camera.SetParallelScale(4.04);camera.SetViewUp(0,1,0)
VIEWS={'front':(0,3.65,15),'left':(13,3.65,5),'back':(0,3.65,-15),'three_quarter':(11,5.6,14),'top':(0,16,.01)}
for n,pos in VIEWS.items():
    camera.SetPosition(*pos);camera.SetViewUp(0,0,-1 if n=='top' else 0) if n=='top' else camera.SetViewUp(0,1,0)
    camera.OrthogonalizeViewUp();REN.ResetCameraClippingRange();RW.Render()
    win=vtk.vtkWindowToImageFilter();win.SetInput(RW);win.SetInputBufferTypeToRGBA();win.ReadFrontBufferOff();win.Update()
    im=vtk_to_numpy(win.GetOutput().GetPointData().GetScalars()).reshape((950,780,4))
    out=Image.fromarray(np.flipud(im)[:,:,:3].copy(),'RGB')
    out.save(OUT/f'{n}.png')
    print('rendered',n)

# Image sheet includes an apples-to-apples crop of the user's supplied reference.
ref=Image.open('/mnt/data/image(20261118-032227).png').convert('RGB')
# crop away the border/labels and keep object proportions (front sheet 690x860; side begins at 690px)
ref_front=ref.crop((65,30,650,790))
ref_side=ref.crop((752,30,1638,790))
for k,crop in [('front',ref_front),('left',ref_side)]:
    base=Image.new('RGB',(1560,1020),(24,22,38))
    photo=ImageOps.contain(crop,(750,950));photo=photo.resize((int(photo.width*.93),int(photo.height*.93)))
    base.paste(photo,((780-photo.width)//2,40+(930-photo.height)//2))
    render=Image.open(OUT/f'{k}.png').convert('RGB')
    base.paste(render,(780,30))
    d=ImageDraw.Draw(base)
    d.text((24,18),'REFERENCE / '+('FACE' if k=='front' else 'PROFIL GAUCHE'),fill='#fefefe',stroke_width=0)
    d.text((806,18),'GLB RECHARGE / '+k.upper(),fill='#ffffff',stroke_width=0)
    base.save(OUT/f'comparison_{k}.png')
# contact sheet
ims=[Image.open(OUT/f'{v}.png').resize((390,475)) for v in VIEWS]
contact=Image.new('RGB',(390*len(ims),510),'#17152c')
d=ImageDraw.Draw(contact)
for i,(name,im) in enumerate(zip(VIEWS,ims)):
    contact.paste(im,(i*390,35));d.text((i*390+13,9),name.upper().replace('_',' '),fill='white')
contact.save(OUT/'all_views.png')
print('render comparison complete')
