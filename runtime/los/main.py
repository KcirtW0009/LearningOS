"""Learning OS Runtime — Entry Point."""

from los.cli.main import build_parser, dispatch


def main() -> None:
    """Entry point for the Learning OS Runtime CLI."""
    parser = build_parser()
    args = parser.parse_args()
    output = dispatch(args)
    print(output)


if __name__ == "__main__":
    main()
