"""CLI for standard neuron presets (pyramidal, bilateral, multipolar)."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from neuron_usd.procedural_neuron import default_spec_for, emit_neuron_usda

_PRESETS = {
    "pyramidal": ("neuron.usda", "pyramidal"),
    "bilateral": ("bilateral_neuron.usda", "bilateral"),
    "multipolar": ("multipolar_neuron.usda", "multipolar"),
}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "preset",
        choices=sorted(_PRESETS.keys()),
        help="Which neuron preset to emit",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("output"),
        help="Directory for neuron.usda / bilateral_neuron.usda / multipolar_neuron.usda",
    )
    p.add_argument("--seed", type=int, default=42, help="Deterministic RNG seed")
    p.add_argument(
        "--bouton-rootlets",
        type=int,
        default=None,
        metavar="N",
        help="Micro-branches per bouton (filopodia look); default from preset (often 5). Use 0 to disable.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing file of the same name",
    )
    args = p.parse_args(argv)

    filename, kind = _PRESETS[args.preset]
    out = args.out_dir / filename
    if out.exists() and not args.force:
        raise SystemExit(
            f"Refusing to overwrite {out} (pass --force). "
            "Existing hand-tuned USD in output/ is kept by default."
        )

    spec = default_spec_for(kind)
    if args.bouton_rootlets is not None:
        spec = replace(spec, bouton_rootlets_per_bouton=args.bouton_rootlets)
    text = emit_neuron_usda(spec, args.seed)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out} ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
