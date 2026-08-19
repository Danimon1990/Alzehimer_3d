# Healthy vs. Alzheimer's — OpenUSD Visualization

A procedural OpenUSD project for visualizing healthy neuronal transport and
Alzheimer's pathology. The repository contains reusable biological assets,
layered presentation shots, and Python publishing tools.

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

Use a Python 3.12 environment containing the OpenUSD `pxr` bindings, then
install the project in editable mode:

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

## Published shot stacks

Each shot is composed from layout, animation, lighting, camera, and render
layers. Layout owns asset placement; reusable assets own geometry, units,
orientation, and their default appearance. Generated shot roots remain thin
and contain no geometry.

The current v2 layout layers sublayer the existing approved presentations so
the migration preserves root-level render settings and the visual result.
Legacy inputs can be replaced incrementally with published component assets.

## Development

Run the pipeline tests with:

```bash
python -m unittest discover -s tests
```

Biological background is available in
[`MICROTUBULES_BIOLOGY.md`](MICROTUBULES_BIOLOGY.md).
