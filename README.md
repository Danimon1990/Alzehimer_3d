# Healthy vs. Alzheimer's — OpenUSD Visualization

A procedural OpenUSD project for visualizing healthy neuronal transport and
Alzheimer's pathology. The repository contains reusable biological assets,
layered presentation shots, and Python publishing tools.

## Watch the demo

- [English walkthrough](https://youtu.be/GAWZ4K7GI5w)
- [Recorrido en español](https://youtu.be/I1goe49ouos)

## What this project demonstrates

- Reusable USD component assets with payloads for source geometry.
- Healthy and Alzheimer's presentation shots composed from separate layout,
  animation, lighting, camera, and render layers.
- Python command-line tools for publishing assets and shots, with checks for
  stage metadata and unresolved dependencies.

The scenes illustrate biological concepts. The pipeline checks validate USD
structure and dependencies; they do not establish biological accuracy.

## Repository layout

```text
config/                 Project and shot configuration
src/healthy_vs_alz/     Publishing CLI and OpenUSD utilities
usd/assets/             Published component assets
usd/sequences/          Layered shot publications
assets/                 Approved source geometry from DCC applications
output/                 Legacy approved scenes used during migration
tests/                  Composition and publication checks
```

The USD composition contract and migration boundary are documented in
[`docs/USD_ARCHITECTURE.md`](docs/USD_ARCHITECTURE.md).

## Commands

Clone the repository and enter its root directory:

```bash
git clone https://github.com/Danimon1990/Alzehimer_3d.git
cd Alzehimer_3d
```

Use Python 3.12 or newer with the OpenUSD `pxr` bindings. For a standalone
Python environment on Linux or macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install usd-core
```

If you already have a compatible OpenUSD Python environment, activate it
instead. Install the project in editable mode and publish from the repository
root. The build commands regenerate files under `usd/`:

```bash
python -m pip install -e .
hvaz build asset all
hvaz build shot all
hvaz validate
```

Individual publications are also supported:

```bash
hvaz build asset neuron
hvaz build shot healthy
```

## Open the scenes

Open either published shot in a compatible USD viewer or Omniverse application:

- Healthy: `usd/sequences/comparison/healthy/healthy.usda`
- Alzheimer's: `usd/sequences/comparison/alzheimers/alzheimers.usda`

Keep the repository's directory structure intact. These shots depend on files
in `output/` and `assets/`; copying only the shot root will omit dependencies.
The `usd-core` Python package does not provide a graphical viewer.

## Published shot stacks

Each shot is composed from layout, animation, lighting, camera, and render
layers. Layout owns asset placement; reusable assets own geometry, units,
orientation, and their default appearance. Generated shot roots remain thin
and contain no geometry.

The current v2 layout layers sublayer the existing approved presentations so
the migration preserves root-level render settings and the visual result.
Legacy inputs can be replaced incrementally with published component assets.

## Known limitation

A clean checkout currently lacks `assets/textures/color_0C0C0C.exr`, referenced
by the source assets. Publishing completes, but `hvaz validate` and the
existing dependency test report this missing texture. Restore the intended
source texture before treating the publication as fully validated.

## Development

Run the pipeline tests with:

```bash
python -m unittest discover -s tests
```

Biological background is available in
[`MICROTUBULES_BIOLOGY.md`](MICROTUBULES_BIOLOGY.md).
