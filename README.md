# NEON CRYSTAL EGG — interactive 3D reconstruction

A faceted, studded, emissive egg based on the supplied front and left-profile sheet. Includes a Vite + Three.js orbit viewer, a neutral GLB, material-batched real 3D stud geometry, reusable assembly pivots, a procedural generator, orthographic QA comparisons and a future Roblox VFX mapping. **No Roblox Studio import has been performed.**

![Five views of the reloaded GLB](comparisons/all_views.png)

## Quick start

```bash
npm install
npm run dev
```

Open the localhost URL shown by Vite (usually `http://localhost:5173`).

To create a production bundle:

```bash
npm run build
npm run preview
```

The browser viewer imports the prebuilt `public/models/neon-crystal-egg.glb`. Python is **not** required to run it. It has front, oblique left profile, back, three-quarter, and top camera presets, plus free orbit/pan/zoom, toggled VFX/auto-rotation and a one-shot pulse. The **Télécharger le GLB** button downloads the same neutral GLB and reparses its exact bytes through `GLTFLoader`, reporting node/material/bounds consistency. **Recharger & vérifier** repeats this check.

## Source and how to regenerate

```bash
python -m pip install numpy trimesh scipy pillow vtk
python generate.py       # regenerate public/models/neon-crystal-egg.glb
python verify_glb.py     # GLB format/hierarchy/materials/geometry audit
python render_compare.py # offline EGL inspection from the reloaded GLB
```

The supplied GLB is already generated: **53 named geometry primitives**, **25,679 triangles**, **21 PBR materials**, and **11 named pivot/anchor transforms**. There are no texture image dependencies, cameras, lights, background or VFX in the GLB. Pixel patterns, segmented plates, raised studs, crystals and belt faces are true meshes. Repeated components sharing a name/material are batched into a single mesh for better Roblox preparation.

## Reference characteristics

| Priority | Distinctive feature | View / check |
|---|---|---|
| 1 | Tall dark armored egg / studded polygonal shell | Front and left profile: oval body tapers above and below; front ±1.95 m widest point |
| 2 | Tall central mast with magenta pointed crown | Front: central spine extends to the highest point (Y=7.23 m) |
| 3 | Outward-fanning pink crystal wreath | Front + oblique left profile: crystalline fan emerges from shoulders and intersects shell |
| 4 | Paired magenta pixel aliens above bright cyan rectangular eyes, upper cyan display | Front: left/right eye panels mirrored around spine, invaders immediately above; upper display right-of-centre |
| 5 | Purple bolted structural ribs and rectangular magenta belt panels | Front and profile: ribs follow the curvature, belt circles lower third of egg |

## Scale, axes and hierarchy

- **Units:** nominal metres / modelling units, not automatically Roblox studs. Decide a Roblox import scale at the later integration step.
- **Bounding dimensions:** **3.8984 W × 7.195 H × 3.5472 D**, AABB min **(-1.9492, 0.0350, -1.7736)**, max **(1.9492, 7.2300, 1.7736)**.
- **Main pivot:** `Egg_Root`, origin `(0,0,0)` at centre, below the lower shell. **Y up; +Z forward** (face). +X is the model's right side.
- **Pivots:** `Body_Pivot` (0,0,0), `Face_Pivot` (0,0,0), `Belt_Pivot` (0,1.08,0), `Crown_Pivot` (0,4.42,0), `Mast_Pivot` (0,4.38,0), `CrystalCrown_Pivot` (0,4.45,0), plus `Eye_Left_Anchor`, `Eye_Right_Anchor`, `Display_Upper_Anchor`, `VFX_Cyan_Pivot`.
- Each mesh is parented beneath its conceptual assembly pivot. The GLB has no unapplied transforms or external files.

## Visual QA and iterations

1. **Initial front and true 90° profile:** the crystal fan was too low and narrow; some studs showed a visible gap at the sides.
2. **Correction:** extend/fan and lift shoulder crystals; move stud positions toward the body; broaden and brighten side ribs. Compare **[`front_before.png`](comparisons/front_before.png)** and **[`front.png`](comparisons/front.png)** with the same camera.
3. **GLB reload validation:** `verify_glb.py` loads the exported binary from disk; `render_compare.py` renders that reloaded GLB from front, oblique left profile, back, three-quarter and top using fixed camera settings. Generated side-by-side images are in [`comparisons/`](comparisons).
4. **Remaining approximations:** supplied 'profil gauche' is evidently an oblique side view rather than a calibrated orthographic projection; its exact yaw, perspective and depth cannot be proven. The hidden rear is an inferred symmetric studded armor surface, with no extra neon characters. The source image has sophisticated bloom, beveling and reflective crystal facets not fully reproduced in the neutral GLB or flat-lit offline QC renders. The model is a reconstruction, not a photogrammetric match.

> **Verification scope:** Three.js JavaScript syntax, GLB binary/scene hierarchy/PBR materials and GPU-free rendered image comparisons were checked offline. This working environment has no network route to the npm registry, so `npm install`, the actual Vite compilation, browser controls and download/reload button interactions were **not executable here**. Those require the indicated commands on a network-enabled machine. Do not treat them as verified. The offline comparison is based on the GLB reloaded with `trimesh` / VTK, not a screenshot from Three.js.

## Roblox handoff (later step)

Read [VFX_PORTAGE.md](VFX_PORTAGE.md) for Roblox-ready attachment names, local offsets, orientation, timing and animations. Import and Studio tests are intentionally deferred. The GLB is designed for use as a mesh-based reference; for individually editable Roblox Parts, recreate or split the batched meshes after importer validation. PBR emissive materials do not automatically reproduce postprocess bloom in Roblox: this will require Roblox `Neon`, `PointLight`, `ParticleEmitter`, `BillboardGui` or other native counterparts.