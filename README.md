# Alzheimer's 3D — Neuron USD Visualization

A procedural 3D visualization pipeline comparing healthy and Alzheimer's-affected neurons, built with [OpenUSD](https://openusd.org/). The project models the role of microtubule integrity in neuronal health and tau-driven degeneration.

## What it does

- Procedurally generates neuron geometry (pyramidal, bilateral, multipolar, medium spiny) as USD layers
- Builds microtubule bundles inside axons and dendrites using `UsdGeomPointInstancer` for GPU-efficient instancing
- Composes condition layers (`healthy` vs `alzheimers`) as USD sublayers over a shared network scene
- Demonstrates key USD concepts: layer composition, `BasisCurves`, `PointInstancer`, `UsdPreviewSurface` materials

## The science

In healthy neurons, **tau proteins** stabilize microtubule bundles — the transport highways that move cargo (mitochondria, vesicles, neurotransmitters) along axons. In Alzheimer's disease:

1. Tau becomes hyperphosphorylated and detaches from microtubules
2. Microtubules depolymerize — the transport highway collapses
3. Detached tau aggregates into **neurofibrillary tangles**
4. Synapses starve and neurons die

Modeling microtubule integrity is literally modeling Alzheimer's pathology.

See [`MICROTUBULES_BIOLOGY.md`](MICROTUBULES_BIOLOGY.md) for the full biology reference.

## Project structure

```
healthy_vs_alz/
├── neuron_usd/                     # Python pipeline
│   ├── dementia_environment_scene.py  # Builds the Alzheimer's / dementia scene (output/dementia_*.usda)
│   ├── healthy_tau_scene.py           # Builds the healthy-tau scene (output/healthy_tau*.usda)
│   ├── neuron_variant_scene.py        # Neuron variant set (artist vs. procedural) used by healthy_tau
│   ├── structured_neuron.py           # BasisCurves neuron geometry used by healthy_tau
│   └── microtubule_bundle.py          # PointInstancer microtubule bundle used by both scenes
├── assets/
│   ├── neuron_model.usda           # Base neuron mesh
│   ├── Broken_neuron.usdc / Sick_neuron.usdc  # Blender-exported dementia-scene neurons
│   ├── microtubules.usdc / TAU.usdc / plaques.usdc  # Blender-exported binary assets
│   └── *.blend                     # Blender source files (not tracked, see .gitignore)
├── output/                         # Generated USD layers for the two scenes above
└── MICROTUBULES_BIOLOGY.md
```

## Requirements

- Python 3.12+
- OpenUSD Python bindings (`pxr`)

Activate the USD venv before running any scripts:

```bash
cd /path/to/usd_root
source python-usd-venv/bin/activate
```

## Usage

Each scene builder is a standalone script that writes its layers into `output/`:

```bash
python neuron_usd/dementia_environment_scene.py
python neuron_usd/healthy_tau_scene.py
```

`healthy_tau_scene.py` depends on `neuron_variant_scene.py`, `structured_neuron.py`, and
`microtubule_bundle.py` having already been run at least once to produce their layers in `output/`.

## Key USD concepts demonstrated

| Concept | Where |
|---|---|
| `UsdGeomPointInstancer` | `microtubule_bundle.py` — GPU-efficient N-copy instancing |
| `BasisCurves` | `structured_neuron.py` — axons, dendrites, spines |
| Layer sublayering | `dementia_environment_scene.py` — non-destructive scene composition |
| `UsdPreviewSurface` | neuron shell transparency / material overrides |
| `UsdGeomXform` | coordinate correction (Blender Z-up → USD Y-up) |
