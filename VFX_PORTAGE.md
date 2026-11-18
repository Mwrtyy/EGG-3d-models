# VFX PORTAGE — Neon Crystal Egg / future Roblox implementation

No Roblox Studio has been opened and no Roblox assets have been imported or tested. The table below maps the **viewer-only** effects onto **GLB node names** and local transforms for later implementation.

**Axes:** Y up, +Z front. Coordinates are in GLB modelling units (nominal metres), not Roblox studs. Offsets below are local to named GLB nodes. All neutral meshes are saved in the GLB, while the lights, particle geometry, camera, floor and bloom belong **only** to the Three.js viewer.

| Viewer VFX | Named anchor in GLB | Local position | Local orientation | Start / duration | Roblox suggestion |
|---|---|---|---|---|---|
| Cyan eye left glow | `Eye_Left_Anchor` | (0,0,0) | viewer billboard faces camera; local normal +Z | Constant while VFX enabled, subtle 3.5 Hz intensity variation | `Attachment` + `BillboardGui`/`PointLight` cyan; orient billboard to camera |
| Cyan eye right glow | `Eye_Right_Anchor` | (0,0,0) | camera-facing billboard | Same | `Attachment` + billboard / cyan light |
| Upper cyan display glow | `Display_Upper_Anchor` | (0,0,0) | camera-facing billboard | Same | Billboard / light |
| Pink crown aura | `CrystalCrown_Pivot` | (0,+1.00,0) | camera-facing sprite | Constant while VFX enabled | Magenta light + soft sprite / emitter |
| Magenta expanding ring | `CrystalCrown_Pivot` | (0,+0.72,0) | torus plane **XZ**, normal **+Y** | On `Rejouer le pulse`; **1.75 s**; expands from 0.4× to 2.9× model mesh radius | Ring mesh / Beam, TweenService scale/opacity |
| Spiraling magenta particles | `CrystalCrown_Pivot` | starts at (0,+0.72,0) | radial in XZ, rises along +Y | On same pulse, **1.75 s**; 48 points, orbit with angle `i*2.39996 + t*0.36`, radial distance `0.35 + (i*19 % 17)/17*1.2 + t*0.28`, vertical offset `(i % 11)/11*1.35 + t/1.75*0.5` | `ParticleEmitter` or scripted particles; gradient alpha 0.72 → 0 |

**Toggle contract:** disabling VFX hides sprites, pulse ring, particles, bloom and attached point lights. Re-enable does not replay an expired one-shot effect. Animation updates anchor world transforms every frame, so glows and particles follow parent groups when the model is repositioned. Pulse can be replayed explicitly. The GLB remains a neutral 3D asset without effects.

**Anchor transforms in world space at neutral pose:** `Eye_Left_Anchor=(-0.95,1.94,1.50)`, `Eye_Right_Anchor=(+0.95,1.94,1.50)`, `Display_Upper_Anchor=(+0.26,3.42,1.44)`, `CrystalCrown_Pivot=(0,4.45,0)`. All are children of the relevant named pivots.

**Roblox material mapping:** `cyan` / `cyan_core` → bright cyan `Neon`; `magenta` / `magenta_panel` / `pink` → magenta `Neon` with pink decals if desired; `crystal_*` → translucent-looking faceted material with limited surface transparency; `panel_*` and `purple_*` → metallic or smooth-plastic armor. Importer/material equivalence is not assumed.