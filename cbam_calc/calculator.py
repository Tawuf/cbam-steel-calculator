"""Core CBAM cost calculation.

For one importer, one product and one year::

    embedded emissions   EE  = tonnes x intensity
                               (intensity = verified value, or India default x (1 + mark-up))
    free-alloc. adjust.  FAA = tonnes x benchmark x CBAM factor x CSCF
    origin carbon price  OCP = deduction for carbon price effectively paid abroad
    certificates             = max(EE - FAA - OCP, 0)
    cost (EUR)               = certificates x certificate price

``simplified_estimate`` reproduces the common shortcut "embedded emissions x
payable share", so the two methods can be compared. The shortcut is only
correct when a producer's intensity equals the benchmark; for high-emission
producers it heavily understates the bill in the early years.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from . import policy


@dataclass(frozen=True)
class Estimate:
    year: int
    tonnes: float
    intensity: float  # tCO2e per tonne actually used
    intensity_basis: str  # "default" or "verified"
    embedded_emissions: float  # tCO2e
    free_allocation_adjustment: float  # tCO2e
    origin_carbon_price_deduction: float  # tCO2e
    certificates: float  # tCO2e (= number of CBAM certificates)
    price: float  # EUR per certificate
    cost_eur: float
    exempt: bool

    @property
    def cost_per_tonne(self) -> float:
        return self.cost_eur / self.tonnes if self.tonnes else 0.0

    def as_dict(self) -> dict:
        data = asdict(self)
        data["cost_per_tonne"] = self.cost_per_tonne
        return data


def resolve_intensity(
    year: int,
    product: policy.Product | None = None,
    verified_intensity: float | None = None,
) -> tuple[float, str]:
    """Return the intensity to use and whether it is a default or verified value."""
    if verified_intensity is not None:
        if verified_intensity < 0:
            raise ValueError("verified_intensity must be non-negative")
        return verified_intensity, "verified"
    if product is None:
        raise ValueError("Give either a product (to use its default) or a verified intensity.")
    marked_up = product.india_default * (1 + policy.default_value_markup(year))
    return marked_up, "default"


def estimate(
    tonnes: float,
    year: int,
    *,
    product: policy.Product | None = None,
    verified_intensity: float | None = None,
    benchmark: float | None = None,
    price: float = policy.DEFAULT_PRICE,
    cscf: float = 1.0,
    origin_carbon_price: float = 0.0,
    annual_importer_tonnes: float | None = None,
) -> Estimate:
    """Estimate CBAM certificates and cost for one import line in one year.

    Parameters
    ----------
    tonnes:
        Net mass imported (tonnes).
    year:
        Calendar year of import (2026 or later).
    product:
        Product preset; supplies the India default value and benchmark.
    verified_intensity:
        Verified installation-level emissions (tCO2e/t). Overrides the default.
    benchmark:
        CBAM benchmark (tCO2e/t). Overrides the product's benchmark.
    price:
        CBAM certificate price in EUR/tCO2e.
    cscf:
        Cross-sectoral correction factor (1.0 for 2026-2030).
    origin_carbon_price:
        Carbon price effectively paid in the country of origin (EUR/tCO2e).
        Today India's CCTS is not recognised, so the default is 0.
    annual_importer_tonnes:
        Importer's total annual imports of covered goods, for the 50 t de
        minimis test. Defaults to ``tonnes``.
    """
    if tonnes < 0:
        raise ValueError("tonnes must be non-negative")
    if price < 0:
        raise ValueError("price must be non-negative")

    intensity, basis = resolve_intensity(year, product, verified_intensity)

    if benchmark is None:
        benchmark = product.benchmark if product else None
    if benchmark is None:
        raise ValueError(
            "No benchmark available for this product. Pass benchmark=... "
            "(tCO2e/t) from the CBAM benchmark implementing act."
        )

    annual = tonnes if annual_importer_tonnes is None else annual_importer_tonnes
    exempt = annual < policy.DE_MINIMIS_TONNES

    embedded = tonnes * intensity
    faa = tonnes * benchmark * policy.cbam_factor(year) * cscf
    gross = max(embedded - faa, 0.0)

    # Article 9: certificates are reduced by the carbon price already paid,
    # converted into an equivalent number of certificates.
    ocp = 0.0
    if origin_carbon_price > 0 and price > 0:
        ocp = min(embedded * min(origin_carbon_price, price) / price, gross)

    certificates = 0.0 if exempt else gross - ocp
    return Estimate(
        year=year,
        tonnes=tonnes,
        intensity=intensity,
        intensity_basis=basis,
        embedded_emissions=embedded,
        free_allocation_adjustment=faa,
        origin_carbon_price_deduction=0.0 if exempt else ocp,
        certificates=certificates,
        price=price,
        cost_eur=certificates * price,
        exempt=exempt,
    )


def simplified_estimate(tonnes: float, year: int, intensity: float, price: float) -> float:
    """Shortcut used in many press articles: EE x payable share x price (EUR)."""
    return tonnes * intensity * policy.payable_share(year) * price


def projection(
    tonnes: float,
    years: range | list[int] = range(policy.FIRST_YEAR, policy.FULL_PHASE_IN_YEAR + 1),
    **kwargs,
) -> list[Estimate]:
    """Run :func:`estimate` for every year in ``years`` with the same inputs."""
    return [estimate(tonnes, year, **kwargs) for year in years]


def break_even_intensity(year: int, benchmark: float, cscf: float = 1.0) -> float:
    """Intensity (tCO2e/t) below which a verified producer owes no certificates."""
    return benchmark * policy.cbam_factor(year) * cscf
