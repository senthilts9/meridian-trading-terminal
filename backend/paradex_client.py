"""Singleton exchange clients for the Meridian API server.

Reuses scripts/config.py (env loading, CA bundle wiring, client factories) so
the backend and the CLI lifecycle scripts share one source of truth for
wallet/subkey credentials -- no duplicated auth logic.
"""
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from config import (  # noqa: E402
    DEFAULT_MARKET,
    compute_min_order_size,
    get_authenticated_client,
    get_public_client,
    logger,
)

_public_client = None
_trading_client = None


def public_client():
    """Cached public (unauthenticated) client -- market data, system info."""
    global _public_client
    if _public_client is None:
        _public_client = get_public_client()
    return _public_client


def trading_client():
    """Cached trading-subkey client. Created once at first use; the SDK
    handles JWT auto-refresh internally so we don't need to recreate it
    per-request."""
    global _trading_client
    if _trading_client is None:
        _trading_client = get_authenticated_client()
    return _trading_client


__all__ = ["public_client", "trading_client", "compute_min_order_size", "DEFAULT_MARKET", "logger"]
