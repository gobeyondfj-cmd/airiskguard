"""Gateway server entry point and CLI."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from airiskguard.gateway.config import GatewayConfig
from airiskguard.gateway.proxy import GatewayApp


def serve(
    config: GatewayConfig | None = None,
    config_path: str | Path | None = None,
    host: str | None = None,
    port: int | None = None,
    log_level: str = "info",
) -> None:
    """Start the airiskguard gateway server.

    Args:
        config: Pre-built :class:`GatewayConfig`. Takes precedence over config_path.
        config_path: Path to a YAML config file.
        host: Override host from config.
        port: Override port from config.
        log_level: Uvicorn log level.
    """
    try:
        import uvicorn
    except ImportError:
        print(
            "ERROR: uvicorn is required to run the gateway.\n"
            "Install with: pip install 'airiskguard[gateway]'",
            file=sys.stderr,
        )
        sys.exit(1)

    if config is None:
        config = GatewayConfig.load(config_path)

    _host = host or config.host
    _port = port or config.port
    _log_level = log_level or config.log_level

    app = GatewayApp(config)

    print(f"airiskguard gateway starting on {_host}:{_port}")
    print(f"  Outbound checks : {config.outbound_checks}")
    print(f"  Inbound checks  : {config.inbound_checks}")
    print(f"  Anthropic proxy : {config.upstream.anthropic}")
    print(f"  OpenAI proxy    : {config.upstream.openai}")
    if config.teams:
        print(f"  Teams           : {[t.name for t in config.teams]}")

    ssl_keyfile = config.tls.key if config.tls.enabled else None
    ssl_certfile = config.tls.cert if config.tls.enabled else None

    uvicorn.run(
        app,
        host=_host,
        port=_port,
        log_level=_log_level,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
    )


def main() -> None:
    """CLI entry point for ``airiskguard-gateway``."""
    parser = argparse.ArgumentParser(
        prog="airiskguard-gateway",
        description="airiskguard Enterprise AI Coding Assistant Gateway",
    )
    parser.add_argument(
        "--config", "-c",
        metavar="PATH",
        help="Path to gateway YAML config file",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Bind host (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=None,
        help="Bind port (default: 8080)",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Log level (default: info)",
    )
    parser.add_argument(
        "--outbound-checks",
        nargs="+",
        metavar="CHECKER",
        help="Outbound checkers (default: secrets compliance agent)",
    )
    parser.add_argument(
        "--inbound-checks",
        nargs="+",
        metavar="CHECKER",
        help="Inbound checkers (default: vuln agent)",
    )
    parser.add_argument(
        "--no-tls",
        action="store_true",
        help="Disable TLS even if cert/key are set in config",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = GatewayConfig.load(args.config)

    if args.outbound_checks:
        config.outbound_checks = args.outbound_checks
    if args.inbound_checks:
        config.inbound_checks = args.inbound_checks
    if args.no_tls:
        config.tls.cert = ""
        config.tls.key = ""

    serve(
        config=config,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
