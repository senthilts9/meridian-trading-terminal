#include "liquidation_model.hpp"

#include <cstring>
#include <iomanip>
#include <iostream>
#include <optional>
#include <string>

namespace {

void print_usage(const char* prog) {
    std::cout
        << "Independent liquidation-price estimator (standalone, no network calls)\n\n"
        << "Usage:\n"
        << "  " << prog << " --side LONG|SHORT --entry <price> --size <size>\n"
        << "         --collateral <total_collateral> --imf-base <value> --mmf-factor <value>\n"
        << "         [--actual <exchange_reported_value>]\n\n"
        << "Example (real captured data from this project's testnet run):\n"
        << "  " << prog << " --side SHORT --entry 66000 --size 0.00023 \\\n"
        << "       --collateral 100001.00961987 --imf-base 0.02 --mmf-factor 0.5 \\\n"
        << "       --actual 430351430.25096846\n";
}

std::optional<double> parse_double(const std::string& s) {
    try {
        size_t pos;
        double v = std::stod(s, &pos);
        if (pos != s.size()) return std::nullopt;
        return v;
    } catch (...) {
        return std::nullopt;
    }
}

} // namespace

int main(int argc, char** argv) {
    std::optional<std::string> side_str;
    std::optional<double> entry, size, collateral, imf_base, mmf_factor, actual;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        auto next = [&](const char* flag) -> std::optional<std::string> {
            if (arg == flag && i + 1 < argc) {
                return std::string(argv[++i]);
            }
            return std::nullopt;
        };

        if (arg == "--help" || arg == "-h") {
            print_usage(argv[0]);
            return 0;
        }
        if (auto v = next("--side")) { side_str = v; continue; }
        if (auto v = next("--entry")) { entry = parse_double(*v); continue; }
        if (auto v = next("--size")) { size = parse_double(*v); continue; }
        if (auto v = next("--collateral")) { collateral = parse_double(*v); continue; }
        if (auto v = next("--imf-base")) { imf_base = parse_double(*v); continue; }
        if (auto v = next("--mmf-factor")) { mmf_factor = parse_double(*v); continue; }
        if (auto v = next("--actual")) { actual = parse_double(*v); continue; }

        std::cerr << "Unrecognized argument: " << arg << "\n\n";
        print_usage(argv[0]);
        return 1;
    }

    if (!side_str || !entry || !size || !collateral || !imf_base || !mmf_factor) {
        std::cerr << "Missing required argument(s).\n\n";
        print_usage(argv[0]);
        return 1;
    }

    quant::Side side;
    if (*side_str == "LONG" || *side_str == "long") {
        side = quant::Side::Long;
    } else if (*side_str == "SHORT" || *side_str == "short") {
        side = quant::Side::Short;
    } else {
        std::cerr << "--side must be LONG or SHORT, got: " << *side_str << "\n";
        return 1;
    }

    quant::PositionInputs in{side, *entry, *size, *collateral, *imf_base, *mmf_factor};

    try {
        quant::LiquidationEstimate est = quant::estimate_liquidation_price(in);

        std::cout << std::fixed << std::setprecision(6);
        std::cout << "Side:                        " << *side_str << "\n";
        std::cout << "Entry price:                 " << *entry << "\n";
        std::cout << "Size:                        " << *size << "\n";
        std::cout << "Total collateral:            " << *collateral << "\n";
        std::cout << "Maintenance margin fraction: " << est.maintenance_margin_fraction << "\n";
        std::cout << "---\n";
        if (est.liquidation_price <= 0.0) {
            std::cout << "Model liquidation estimate:  " << est.liquidation_price
                       << "  (<= 0 -- position cannot be liquidated by a price move alone\n"
                       << "                               at this collateral level; collateral vastly\n"
                       << "                               exceeds what this position could ever lose)\n";
        } else {
            std::cout << "Model liquidation estimate:  " << est.liquidation_price << "\n";
            std::cout << "Distance from entry:         " << std::setprecision(2)
                       << est.distance_pct << "%\n";
        }

        if (actual) {
            double diff_pct = std::fabs(est.liquidation_price - *actual) / *actual * 100.0;
            std::cout << "---\n";
            std::cout << std::setprecision(6);
            std::cout << "Exchange-reported value:     " << *actual << "\n";
            std::cout << "Relative error:              " << std::setprecision(4)
                       << diff_pct << "%\n";
        }
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }

    return 0;
}
