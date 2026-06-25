# Microtubules in Neurons — Biology Reference

## Why axons and dendrites, not the soma

The **cell body (soma)** has microtubules, but they're short, dynamic, and disorganized — more for general cell scaffolding. The real story is in the processes:

- **Axons and dendrites** are long, thin extensions that can stretch from micrometers to *over a meter* (e.g. motor neurons going to your toes). They have no ribosomes — they can't make proteins locally. Everything has to be **shipped from the soma**.
- Microtubules are the **highway system** for that shipping. Motor proteins walk along them carrying cargo: mitochondria, vesicles, neurotransmitter precursors, ion channels.

---

## How they're organized

**Axons**: all microtubules run **parallel**, with their **plus-ends pointing away** from the soma (anterograde direction). This polarity is critical:
- **Kinesin** motors walk toward the plus end → cargo moves *away* from soma (anterograde transport)
- **Dynein** motors walk toward the minus end → cargo moves *back* to soma (retrograde transport)
- A single axon can contain **hundreds of parallel microtubules**

**Dendrites**: also longitudinal but with **mixed polarity** — some plus-ends pointing toward the soma, some away. This is one of the key structural differences that distinguishes axons from dendrites at the molecular level.

**Dendritic spines** (the small bumps where synapses form): generally *no* stable microtubules — they're actin-based instead.

---

## The Alzheimer's Connection

This is the core of the `healthy_vs_alz` project.

In healthy neurons, a protein called **tau** binds along microtubules in the axon and **stabilizes them**, keeping the transport highway intact.

In Alzheimer's disease:

1. Tau becomes **hyperphosphorylated** (too many phosphate groups attached to it)
2. Hyperphosphorylated tau **detaches** from microtubules
3. Microtubules **depolymerize** — the highway falls apart
4. Detached tau aggregates into **neurofibrillary tangles** (one of the two hallmarks of Alzheimer's, alongside amyloid-beta plaques)
5. Without the transport highway → synapses starve → neurons die

> **Modeling microtubule integrity is literally modeling Alzheimer's pathology.**

---

## What this means for the scene

| State | Microtubule appearance |
|---|---|
| **Healthy neuron** | Dense, parallel, well-organized bundles running the full length of axons and dendrites |
| **Alzheimer's neuron** | Fragmented, sparse, broken segments — tau tangles where ordered bundles used to be |

In reality, microtubules don't run as a single tube — they run as **parallel bundles of 10–100 microtubules** side by side inside the axon, not one isolated tube.

Each tubulin dimer segment is approximately **8nm** long. They're made of **13 protofilaments** arranged in a hollow ring (~25nm diameter).

---

## Tomorrow's plan: Healthy Neuron Scene

### Goal
Build a healthy neuron scene in OpenUSD that:
1. Shows the **full neuron** (from a rendered model) with a **fade/transparency effect** on the membrane
2. Reveals **microtubule bundles** running along axons and dendrites inside
3. Contrasts structurally with a future Alzheimer's version

### Steps planned
1. **Microtubule chain**: Stack instances of `assets/microtubules.usdc` along the Z axis using `UsdGeomPointInstancer` — efficient GPU instancing, one prototype, N position offsets spaced ~5.92 units apart
2. **Bundle**: Place several parallel chains offset from each other to approximate a real axon bundle cross-section
3. **Neuron shell**: Import the rendered neuron model, apply a semi-transparent material (low `opacity` in `UsdPreviewSurface`) to create the fade/cutaway effect
4. **Placement**: Position microtubule bundles inside the axon and dendrite paths of the neuron shell

### Key USD concepts involved
- `UsdGeomPointInstancer` — efficient repeated geometry
- `UsdShade.Material` + `opacity` input — transparency for the neuron shell
- `prepend references` — referencing external assets
- Layer composition — keeping neuron shell and microtubules in separate files, composed together

---

## Asset reference

- Segment asset: `assets/microtubules.usdc`
- Segment bbox Z extent: `−3.47` to `+2.45` → **~5.92 units long** → use this as the instancing stride
- Segment local orientation: along **Z axis**; scene applies `rotateZYX(90,0,0)` to reorient along Y
- Protofilaments in asset: ~11 BézierCurve meshes + 1 central Cylinder = 12 total (13 is biologically correct — close enough)
- USD Python env: `cd /home/daniel/usd_root && source python-usd-venv/bin/activate`
