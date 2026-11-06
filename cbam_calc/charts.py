"""Generate the charts shown in the README: ``python -m cbam_calc.charts``."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from . import calculator, policy  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent / "docs"
YEARS = list(range(policy.FIRST_YEAR, policy.FULL_PHASE_IN_YEAR + 1))


def _style(ax, title: str, ylabel: str) -> None:
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    ax.set_xticks(YEARS)


def cost_per_tonne_by_basis(path: Path) -> None:
    """EUR per tonne of hot-rolled steel: India default vs. verified intensities."""
    hrf = policy.load_products()["hot_rolled_flat"]
    scenarios = [
        ("India default value (+ mark-up)", dict(product=hrf), "#c0392b"),
        ("Verified 2.5 tCO2e/t", dict(product=hrf, verified_intensity=2.5), "#e67e22"),
        ("Verified 2.0 tCO2e/t", dict(product=hrf, verified_intensity=2.0), "#2980b9"),
        ("Verified 1.4 tCO2e/t (near benchmark)", dict(product=hrf, verified_intensity=1.4), "#27ae60"),
    ]
    fig, ax = plt.subplots(figsize=(9, 5))
    for label, kw, color in scenarios:
        costs = [e.cost_per_tonne for e in calculator.projection(1000, **kw)]
        ax.plot(YEARS, costs, marker="o", label=label, color=color, linewidth=2)
    _style(ax, "CBAM cost per tonne of Indian hot-rolled steel",
           f"EUR per tonne (certificate price EUR {policy.DEFAULT_PRICE})")
    ax.legend(frameon=False)
    fig.text(0.01, 0.01, "Law in force (Reg. 2023/956, Impl. Reg. 2025/2621). Price held constant.",
             fontsize=8, color="gray")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def price_sensitivity(path: Path) -> None:
    """Annual bill for 10,000 t on default values at three certificate prices."""
    hrf = policy.load_products()["hot_rolled_flat"]
    fig, ax = plt.subplots(figsize=(9, 5))
    width = 0.27
    for i, (price, color) in enumerate([(75, "#95a5a6"), (100, "#2980b9"), (130, "#2c3e50")]):
        costs = [e.cost_eur / 1e6 for e in calculator.projection(10_000, product=hrf, price=price)]
        ax.bar([y + (i - 1) * width for y in YEARS], costs, width=width, label=f"EUR {price}/tCO2e",
               color=color)
    _style(ax, "Annual CBAM bill for 10,000 t of hot-rolled steel (India default values)",
           "EUR million per year")
    ax.legend(frameon=False, title="Certificate price")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def method_gap(path: Path) -> None:
    """Full method vs. 'payable share' shortcut for India default values."""
    hrf = policy.load_products()["hot_rolled_flat"]
    full, short = [], []
    for e in calculator.projection(1000, product=hrf):
        full.append(e.cost_per_tonne)
        short.append(calculator.simplified_estimate(1, e.year, e.intensity, e.price))
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(YEARS, full, marker="o", linewidth=2, color="#c0392b",
            label="Full method (embedded emissions - benchmark adjustment)")
    ax.plot(YEARS, short, marker="o", linewidth=2, linestyle="--", color="#7f8c8d",
            label="Shortcut (embedded emissions x payable share)")
    ax.fill_between(YEARS, short, full, color="#c0392b", alpha=0.08)
    _style(ax, "Why the 'payable share' shortcut understates early CBAM costs",
           "EUR per tonne")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    cost_per_tonne_by_basis(DOCS / "cost_per_tonne.png")
    price_sensitivity(DOCS / "price_sensitivity.png")
    method_gap(DOCS / "method_gap.png")
    print(f"Charts written to {DOCS}")


if __name__ == "__main__":
    main()
