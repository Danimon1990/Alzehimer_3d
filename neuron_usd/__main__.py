"""python -m neuron_usd -- dispatch to subcommands."""

from __future__ import annotations

import argparse

from neuron_usd import __version__


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m neuron_usd")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("neuron", help="Standard neuron presets (see neuron_usd.main)")
    sp.add_argument("preset", choices=["pyramidal", "bilateral", "multipolar"])
    sp.add_argument("--out-dir", default="output")
    sp.add_argument("--seed", type=int, default=42)
    sp.add_argument("--force", action="store_true")

    sm = sub.add_parser("msn")
    sm.add_argument("variant", choices=["medium_spiny", "msn"])
    sm.add_argument("--out-dir", default="output")
    sm.add_argument("--seed", type=int, default=42)
    sm.add_argument("--force", action="store_true")

    sc = sub.add_parser("cortical")
    sc.add_argument("--out-dir", default="output")
    sc.add_argument("--seed", type=int, default=42)
    sc.add_argument("--force", action="store_true")

    sn = sub.add_parser("network")
    sn.add_argument("--out", default="output/Network_composed.usda")
    sn.add_argument("--n0", default="./multipolar_neuron.usda")
    sn.add_argument("--n1", default="./bilateral_neuron.usda")
    sn.add_argument("--n2", default="./bilateral_neuron.usda")
    sn.add_argument("--force", action="store_true")

    sd = sub.add_parser("condition")
    sd.add_argument("which", choices=["healthy", "alzheimers"])
    sd.add_argument("--network-layer", default="./Network.usda")
    sd.add_argument("--out-dir", default="output")
    sd.add_argument("--force", action="store_true")

    si = sub.add_parser("healthy-tau-intro")
    si.add_argument("--layers", type=int, default=1)
    si.add_argument("--rows", type=int, default=6)
    si.add_argument("--columns", type=int, default=6)

    args = p.parse_args(argv)

    if args.cmd == "neuron":
        from neuron_usd.main import main as run_main

        return run_main(
            [args.preset, "--out-dir", args.out_dir, "--seed", str(args.seed)]
            + (["--force"] if args.force else [])
        )
    if args.cmd == "msn":
        from neuron_usd import msn_builder

        return msn_builder.main(
            [args.variant, "--out-dir", args.out_dir, "--seed", str(args.seed)]
            + (["--force"] if args.force else [])
        )
    if args.cmd == "cortical":
        from neuron_usd import cortical_pyramidal_builder

        return cortical_pyramidal_builder.main(
            ["--out-dir", args.out_dir, "--seed", str(args.seed)] + (["--force"] if args.force else [])
        )
    if args.cmd == "network":
        from neuron_usd import network_builder

        return network_builder.main(
            ["--out", args.out, "--n0", args.n0, "--n1", args.n1, "--n2", args.n2]
            + (["--force"] if args.force else [])
        )
    if args.cmd == "condition":
        from neuron_usd import conditions

        return conditions.main(
            [args.which, "--network-layer", args.network_layer, "--out-dir", args.out_dir]
            + (["--force"] if args.force else [])
        )
    if args.cmd == "healthy-tau-intro":
        from neuron_usd import healthy_tau_intro_scene

        return healthy_tau_intro_scene.main(
            ["--layers", str(args.layers), "--rows", str(args.rows), "--columns", str(args.columns)]
        )
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
