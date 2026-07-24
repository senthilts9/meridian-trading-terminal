#pragma once

// Independent cross-margin liquidation price estimator.
//
// Standalone by design: this does not call any exchange API and is not wired
// into the live backend. It takes the same inputs a position/account
// snapshot already contains and computes an estimate to compare against
// whatever the exchange reports (when it reports anything at all -- see
// README for why that field isn't always populated).

namespace quant {

enum class Side { Long, Short };

struct PositionInputs {
    Side side;
    double entry_price;     // average entry price of the position
    double size;             // position size, always positive (side carries direction)
    double total_collateral; // account collateral backing the position (single-position
                              // account assumption -- see README "Assumptions")
    double imf_base;         // initial margin fraction base, from market config
                              // (delta1_cross_margin_params.imf_base)
    double mmf_factor;       // maintenance margin factor, from market config
                              // (delta1_cross_margin_params.mmf_factor)
};

struct LiquidationEstimate {
    double liquidation_price;
    double maintenance_margin_fraction; // mmf = imf_base * mmf_factor
    double distance_pct;                // % move from entry to estimated liquidation
};

// Throws std::invalid_argument if inputs are non-physical (zero/negative size,
// non-positive prices, mmf >= 1, etc.) -- fails loud rather than returning a
// silently wrong number.
LiquidationEstimate estimate_liquidation_price(const PositionInputs& in);

} // namespace quant
