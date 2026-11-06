"""Policy parameters for the EU CBAM definitive period (from 1 January 2026).

Every number here comes from a published source listed in ``data/SOURCES.md``.
All of them can be overridden when calling the calculator, so the tool keeps
working when the Commission updates benchmarks, default values or prices.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

FIRST_YEAR = 2026
FULL_PHASE_IN_YEAR = 2034

# Share of the free-allocation benchmark that is still deducted each year
# ("CBAM factor", Article 10a(1a) of Directive 2003/87/EC as amended).
# 97.5 % in 2026 means the importer pays for 2.5 % of the benchmark.
CBAM_FACTOR: dict[int, float] = {
    2026: 0.975,
    2027: 0.95,
    2028: 0.90,
    2029: 0.775,
    2030: 0.515,
    2031: 0.39,
    2032: 0.265,
    2033: 0.14,
    2034: 0.0,
}

# Mark-up added to country-specific default values when no verified
# installation data is supplied (Implementing Regulation (EU) 2025/2621).
DEFAULT_VALUE_MARKUP: dict[int, float] = {2026: 0.10, 2027: 0.20}
DEFAULT_VALUE_MARKUP_FROM_2028 = 0.30

# Importers below this annual net mass (iron & steel, aluminium, fertilisers,
# cement) are exempt from CBAM obligations.
DE_MINIMIS_TONNES = 50.0

# Published quarterly CBAM certificate prices for 2026 (EUR / tCO2e).
CERTIFICATE_PRICES: dict[str, float] = {
    "2026-Q1": 75.36,
    "2026-Q3": 82.32,
}
DEFAULT_PRICE = CERTIFICATE_PRICES["2026-Q3"]

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _check_year(year: int) -> None:
    if year < FIRST_YEAR:
        raise ValueError(
            f"CBAM financial obligations start in {FIRST_YEAR}; got {year}."
        )


def cbam_factor(year: int) -> float:
    """Share of the benchmark still deducted as free-allocation adjustment."""
    _check_year(year)
    return CBAM_FACTOR.get(year, 0.0)


def payable_share(year: int) -> float:
    """Share of the benchmark no longer covered by free allocation."""
    return 1.0 - cbam_factor(year)


def default_value_markup(year: int) -> float:
    """Regulatory mark-up applied to default values in a given year."""
    _check_year(year)
    return DEFAULT_VALUE_MARKUP.get(year, DEFAULT_VALUE_MARKUP_FROM_2028)


@dataclass(frozen=True)
class Product:
    """A CBAM steel product with its India default value and benchmark."""

    key: str
    name: str
    cn_code: str
    india_default: float  # tCO2e per tonne, before mark-up
    benchmark: float | None  # tCO2e per tonne, None if not yet sourced


def load_products(path: Path | None = None) -> dict[str, Product]:
    """Load product presets from ``data/india_steel_defaults.csv``."""
    path = path or DATA_DIR / "india_steel_defaults.csv"
    products: dict[str, Product] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            benchmark = row["benchmark_tco2e_per_t"].strip()
            products[row["key"]] = Product(
                key=row["key"],
                name=row["name"],
                cn_code=row["cn_code"],
                india_default=float(row["india_default_tco2e_per_t"]),
                benchmark=float(benchmark) if benchmark else None,
            )
    return products
