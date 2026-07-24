#include "liquidation_model.hpp"

#include <cmath>
#include <stdexcept>

namespace quant {

// Derivation (cross-margin, single-position account):
//
//   Account value at mark price P:        V(P) = C + (P - E) * S
//   Maintenance margin requirement at P:  M(P) = mmf * |S| * P
//   Liquidation is the price where V(P) = M(P).
//
// Solving V(P) = M(P) for each side gives:
//
//   LONG  (S > 0):  P = (E*S - C) / (S * (1 - mmf))
//   SHORT (S < 0, s = |S|):  P = (C + E*s) / (s * (1 + mmf))
//
// See README.md for the full step-by-step algebra and validation against a
// real captured account snapshot (0.046% relative error).
LiquidationEstimate estimate_liquidation_price(const PositionInputs& in) {
    if (in.entry_price <= 0.0) {
        throw std::invalid_argument("entry_price must be positive");
    }
    if (in.size <= 0.0) {
        throw std::invalid_argument("size must be positive (side carries direction)");
    }
    if (in.total_collateral <= 0.0) {
        throw std::invalid_argument("total_collateral must be positive");
    }
    if (in.imf_base <= 0.0 || in.mmf_factor <= 0.0) {
        throw std::invalid_argument("imf_base and mmf_factor must be positive");
    }

    const double mmf = in.imf_base * in.mmf_factor;
    if (mmf <= 0.0 || mmf >= 1.0) {
        throw std::invalid_argument("derived maintenance margin fraction out of (0,1) range");
    }

    const double E = in.entry_price;
    const double s = in.size;
    const double C = in.total_collateral;

    double liq_price;
    if (in.side == Side::Long) {
        liq_price = (E * s - C) / (s * (1.0 - mmf));
    } else {
        liq_price = (C + E * s) / (s * (1.0 + mmf));
    }

    LiquidationEstimate out;
    out.liquidation_price = liq_price;
    out.maintenance_margin_fraction = mmf;
    out.distance_pct = std::fabs(liq_price - E) / E * 100.0;
    return out;
}

} // namespace quant
