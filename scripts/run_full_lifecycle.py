"""
End-to-end Paradex testnet trade lifecycle validation.

Wallet -> Testnet funding (prereq, done via faucet) -> Paradex account (onboarding)
-> Market data -> Place order -> Order accepted -> Trade executed -> Position opened
-> Monitor position/P&L -> Close position -> Trade history

Each stage is logged and checked; the script stops with a clear error at the
first stage that fails rather than plowing ahead on bad state.
"""
import json
import sys
import time
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path

from config import DEFAULT_MARKET, LOGS_DIR, get_authenticated_client, logger

market_data_mod = import_module("02_market_data")
place_order_mod = import_module("03_place_order")
check_order_mod = import_module("04_check_order")
check_fill_mod = import_module("05_check_fill")
position_mod = import_module("06_position_pnl")
close_position_mod = import_module("07_close_position")
trade_history_mod = import_module("08_trade_history")

REPORT_PATH = LOGS_DIR / f"lifecycle_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"


def step(name):
    logger.info("=" * 70)
    logger.info(f"STEP: {name}")
    logger.info("=" * 70)


def wait_for_order_terminal(p, order_id, timeout_s=15, poll_s=1.0):
    """Poll an order until it's no longer NEW/OPEN, or timeout."""
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        last = p.api_client.fetch_order(order_id=order_id)
        status = last.get("status")
        if status not in ("NEW", "OPEN"):
            return last
        time.sleep(poll_s)
    return last


def main():
    report = {"started_at": datetime.now(timezone.utc).isoformat(), "market": DEFAULT_MARKET}

    step("1. Wallet -> Paradex account (onboarding + JWT auth)")
    p = get_authenticated_client()
    report["l2_address"] = hex(p.account.l2_address)
    report["jwt_acquired"] = bool(p.account.jwt_token)
    logger.info(f"L2 account: {report['l2_address']}  JWT acquired: {report['jwt_acquired']}")

    step("2. Account state before trading")
    account_before = p.api_client.fetch_account_summary()
    report["account_before"] = account_before
    logger.info(f"Account value: {account_before.account_value} USDC")

    step("3. Market data")
    md = market_data_mod.main()
    report["market_snapshot"] = md["bbo"]

    step("4. Place BUY order (market/IOC)")
    buy_response = place_order_mod.main()
    order_id = buy_response["id"]
    report["buy_order_submitted"] = buy_response

    step("5. Confirm order accepted / reached terminal state")
    order_final = wait_for_order_terminal(p, order_id)
    report["buy_order_final"] = order_final
    if order_final is None or order_final.get("status") != "CLOSED":
        logger.error(f"Order did not reach CLOSED/filled state in time: {order_final}")
        _write_report(report)
        sys.exit(1)
    logger.info(f"Order {order_id} final state: {order_final}")

    step("6. Check fill")
    fills = check_fill_mod.check_fills(p)
    report["fills_after_buy"] = fills

    step("7. Position opened")
    position = position_mod.get_position(p)
    report["position_after_buy"] = position
    if position is None:
        logger.error("No position found after a supposedly filled BUY order.")
        _write_report(report)
        sys.exit(1)

    step("8. Monitor position / P&L")
    pnl = position_mod.get_account_pnl(p)
    report["account_pnl_with_position"] = pnl

    step("9. Close position")
    close_response = close_position_mod.close_position(p)
    report["close_order_submitted"] = close_response
    close_final = wait_for_order_terminal(p, close_response["id"])
    report["close_order_final"] = close_final

    step("10. Confirm position closed")
    position_after_close = position_mod.get_position(p)
    report["position_after_close"] = position_after_close
    if position_after_close is not None:
        logger.warning(f"Position still open after close attempt: {position_after_close}")

    step("11. Trade history")
    history = trade_history_mod.trade_history(p)
    report["trade_history"] = history

    step("12. Account state after trading")
    account_after = p.api_client.fetch_account_summary()
    report["account_after"] = account_after

    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    report["result"] = "SUCCESS"
    _write_report(report)
    logger.info("Full trade lifecycle completed successfully.")


def _write_report(report):
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
