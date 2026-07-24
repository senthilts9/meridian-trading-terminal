"""Shared setup: env loading, CA bundle wiring, and Paradex client factory."""
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Must happen before any https call (paradex_py, requests, etc.) is made.
_ca_bundle = os.getenv("SSL_CERT_FILE") or os.getenv("REQUESTS_CA_BUNDLE")
if _ca_bundle:
    _ca_path = Path(_ca_bundle)
    if not _ca_path.is_absolute():
        _ca_path = PROJECT_ROOT / _ca_path
    os.environ["SSL_CERT_FILE"] = str(_ca_path)
    os.environ["REQUESTS_CA_BUNDLE"] = str(_ca_path)

from paradex_py import Paradex, ParadexEvm, ParadexSubkey  # noqa: E402
from paradex_py.environment import PROD, TESTNET  # noqa: E402

LOG_FILE = LOGS_DIR / f"run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("paradex-bot")
logger.info(f"Logging to {LOG_FILE}")

ENV = TESTNET if os.getenv("PARADEX_ENV", "testnet").lower() == "testnet" else PROD

DEFAULT_MARKET = os.getenv("PARADEX_MARKET", "BTC-USD-PERP")


def compute_min_order_size(market_cfg: dict, mark_price: float, safety_multiplier: float = 1.5):
    """Smallest size that clears min_notional, rounded up to order_size_increment."""
    from decimal import ROUND_UP, Decimal

    increment = Decimal(market_cfg["order_size_increment"])
    min_notional = Decimal(market_cfg["min_notional"])
    price = Decimal(str(mark_price))

    raw_size = (min_notional * Decimal(str(safety_multiplier))) / price
    steps = (raw_size / increment).quantize(Decimal("1"), rounding=ROUND_UP)
    return steps * increment


def get_public_client() -> Paradex:
    """Client for public endpoints only (market data, system info) — no auth."""
    return Paradex(env=ENV, logger=logger)


def get_evm_client() -> ParadexEvm:
    """EVM/SIWE-authenticated client for the main account.

    Can onboard, read account/positions/orders/fills, and register subkeys --
    but cannot sign orders itself (no Starknet key of its own). This is the
    path that actually works on the current testnet; the legacy
    Paradex(l1_address=..., l1_private_key=...) constructor derives a native
    Starknet account that currently fails to deploy (Paradex-side bug: its
    proxy account class isn't declared on their chain -- see README).
    """
    l1_address = os.getenv("L1_ADDRESS")
    l1_private_key = os.getenv("L1_PRIVATE_KEY")
    if not l1_address or not l1_private_key:
        raise RuntimeError(
            "L1_ADDRESS / L1_PRIVATE_KEY not set. Run scripts/00_generate_wallet.py "
            "first, then copy the values into .env."
        )
    return ParadexEvm(
        env=ENV,
        evm_address=l1_address,
        evm_private_key=l1_private_key,
        logger=logger,
    )


def get_authenticated_client() -> ParadexSubkey:
    """Trading-capable client. Uses a Starknet subkey registered to the main
    EVM account (see scripts/01_register_subkey.py) -- this is what can
    actually sign and submit orders. Supports all the same read endpoints
    (account/positions/orders/fills) as the EVM client, just not withdrawals."""
    subkey_private_key = os.getenv("SUBKEY_L2_PRIVATE_KEY")
    main_l2_address = os.getenv("MAIN_L2_ADDRESS")
    if not subkey_private_key or not main_l2_address:
        raise RuntimeError(
            "SUBKEY_L2_PRIVATE_KEY / MAIN_L2_ADDRESS not set. Run "
            "scripts/01_register_subkey.py first, then copy the values into .env."
        )
    return ParadexSubkey(
        env=ENV,
        l2_private_key=subkey_private_key,
        l2_address=main_l2_address,
        logger=logger,
    )
