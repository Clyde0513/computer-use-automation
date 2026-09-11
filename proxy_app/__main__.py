"""Command-line entry point for the local proxy application."""

from __future__ import annotations

import argparse
from wsgiref.simple_server import make_server

from .app import application


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the synthetic legacy financial servicing proxy."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    with make_server(args.host, args.port, application) as server:
        print(f"Synthetic proxy running at http://{args.host}:{args.port}/")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nProxy stopped.")


if __name__ == "__main__":
    main()
