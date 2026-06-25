"""Corticostriatal pyramidal neuron export."""

from __future__ import annotations

import argparse
from pathlib import Path

from neuron_usd.procedural_neuron import cortical_spec, emit_neuron_usda


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", type=Path, default=Path("output"))
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--force", action="store_true")
    args = p.parse_args(argv)

    out = args.out_dir / "cortical_pyramidal.usda"
    if out.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite {out} (pass --force).")

    text = emit_neuron_usda(cortical_spec(), args.seed)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out} ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
