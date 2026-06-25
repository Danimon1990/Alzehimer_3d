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
├── neuron_usd/               # Python pipeline
│   ├── main.py               # CLI — emit pyramidal / bilateral / multipolar neurons
│   ├── conditions.py         # CLI — emit healthy / alzheimers condition layers
│   ├── procedural_neuron.py  # BasisCurves neuron geometry builder
│   ├── microtubule_chain.py  # PointInstancer microtubule chain
│   ├── cortical_pyramidal_builder.py
│   ├── msn_builder.py        # Medium spiny neuron
│   ├── network_builder.py    # Multi-neuron network scene
│   └── neuron_microtubules_scene.py
├── assets/
│   ├── microtubules.usdc     # Blender-exported microtubule segment (binary)
│   └── neuron_model.usda     # Base neuron mesh
├── output/                   # Generated USD layers
│   ├── condition_healthy.usda
│   ├── condition_alzheimers.usda
│   ├── Network.usda
│   └── ...
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

**Generate a neuron preset:**

```bash
python -m neuron_usd pyramidal
python -m neuron_usd bilateral
python -m neuron_usd multipolar
```

**Emit a condition layer:**

```bash
python -m neuron_usd.conditions healthy
python -m neuron_usd.conditions alzheimers
```

Use `--force` to overwrite existing output files. Use `--out-dir` to change the output directory.

## Key USD concepts demonstrated

| Concept | Where |
|---|---|
| `UsdGeomPointInstancer` | `microtubule_chain.py` — GPU-efficient N-copy instancing |
| `BasisCurves` | `procedural_neuron.py` — axons, dendrites, spines |
| Layer sublayering | `conditions.py` — non-destructive condition overlays |
| `UsdPreviewSurface` | neuron shell transparency / material overrides |
| `UsdGeomXform` | coordinate correction (Blender Z-up → USD Y-up) |
