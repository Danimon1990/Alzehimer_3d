import argparse

from healthy_vs_alz.usd.assets import ASSETS, publish_all_assets, publish_asset
from healthy_vs_alz.usd.shots import publish_all_shots, publish_shot
from healthy_vs_alz.usd.validation import validate_publish


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hvaz")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build_commands = build.add_subparsers(dest="target", required=True)
    asset = build_commands.add_parser("asset")
    asset.add_argument("name", choices=[*ASSETS, "all"])
    shot = build_commands.add_parser("shot")
    shot.add_argument("name", choices=["healthy", "alzheimers", "all"])
    commands.add_parser("validate")
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "build" and args.target == "asset":
        paths = publish_all_assets() if args.name == "all" else [publish_asset(args.name)]
    elif args.command == "build" and args.target == "shot":
        paths = publish_all_shots() if args.name == "all" else [publish_shot(args.name)]
    else:
        findings = validate_publish()
        for finding in findings:
            print(f"{finding.path}: {finding.message}")
        return 1 if findings else 0
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
