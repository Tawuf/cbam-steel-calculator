"""Command-line interface: ``python -m cbam_calc <command> ...``."""
from __future__ import annotations

import argparse
import csv
import sys

from . import calculator, policy


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--product", default="hot_rolled_flat",
                   help="product key from data/india_steel_defaults.csv")
    p.add_argument("--tonnes", type=float, required=True, help="net mass imported per year")
    p.add_argument("--intensity", type=float,
                   help="verified emissions in tCO2e/t (omit to use the India default)")
    p.add_argument("--benchmark", type=float, help="override the product benchmark (tCO2e/t)")
    p.add_argument("--price", type=float, default=policy.DEFAULT_PRICE,
                   help=f"certificate price in EUR/tCO2e (default {policy.DEFAULT_PRICE})")
    p.add_argument("--origin-price", type=float, default=0.0,
                   help="carbon price effectively paid in India, EUR/tCO2e")


def _kwargs(args: argparse.Namespace) -> dict:
    products = policy.load_products()
    if args.product not in products:
        sys.exit(f"Unknown product '{args.product}'. Choose from: {', '.join(products)}")
    return dict(
        product=products[args.product],
        verified_intensity=args.intensity,
        benchmark=args.benchmark,
        price=args.price,
        origin_carbon_price=args.origin_price,
    )


def cmd_estimate(args: argparse.Namespace) -> None:
    e = calculator.estimate(args.tonnes, args.year, **_kwargs(args))
    if e.exempt:
        print(f"Exempt: {e.tonnes:,.0f} t is below the {policy.DE_MINIMIS_TONNES:.0f} t de minimis threshold.")
        return
    print(f"Year                          {e.year}")
    print(f"{'Intensity (' + e.intensity_basis + ')':30s}{e.intensity:.3f} tCO2e/t")
    print(f"Embedded emissions            {e.embedded_emissions:,.1f} tCO2e")
    print(f"Free-allocation adjustment  - {e.free_allocation_adjustment:,.1f} tCO2e")
    if e.origin_carbon_price_deduction:
        print(f"Origin carbon price         - {e.origin_carbon_price_deduction:,.1f} tCO2e")
    print(f"CBAM certificates             {e.certificates:,.1f}")
    print(f"Certificate price             EUR {e.price:,.2f}")
    print(f"Total cost                    EUR {e.cost_eur:,.0f}  ({e.cost_per_tonne:,.2f} EUR per tonne)")


def cmd_projection(args: argparse.Namespace) -> None:
    rows = calculator.projection(args.tonnes, **_kwargs(args))
    writer = csv.writer(sys.stdout) if args.csv else None
    header = ["year", "intensity", "certificates", "cost_eur", "cost_per_tonne"]
    if writer:
        writer.writerow(header)
    else:
        print(f"{'year':>4}  {'intensity':>9}  {'certificates':>12}  {'cost EUR':>12}  {'EUR/t':>8}")
    for e in rows:
        values = [e.year, round(e.intensity, 3), round(e.certificates, 1),
                  round(e.cost_eur), round(e.cost_per_tonne, 2)]
        if writer:
            writer.writerow(values)
        else:
            print(f"{e.year:>4}  {e.intensity:>9.3f}  {e.certificates:>12,.1f}  "
                  f"{e.cost_eur:>12,.0f}  {e.cost_per_tonne:>8.2f}")


def cmd_compare(args: argparse.Namespace) -> None:
    """Show how much the common 'payable share' shortcut misses."""
    kwargs = _kwargs(args)
    print(f"{'year':>4}  {'full method EUR':>16}  {'shortcut EUR':>13}  {'shortcut misses':>15}")
    for e in calculator.projection(args.tonnes, **kwargs):
        short = calculator.simplified_estimate(e.tonnes, e.year, e.intensity, e.price)
        print(f"{e.year:>4}  {e.cost_eur:>16,.0f}  {short:>13,.0f}  {e.cost_eur - short:>15,.0f}")


def cmd_products(_: argparse.Namespace) -> None:
    for p in policy.load_products().values():
        bm = f"{p.benchmark:.3f}" if p.benchmark is not None else "n/a (pass --benchmark)"
        print(f"{p.key:16s} CN {p.cn_code}  default {p.india_default:.2f}  benchmark {bm}  {p.name}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cbam_calc",
        description="Estimate EU CBAM costs for Indian steel exports.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("estimate", help="cost for a single year")
    _add_common(p)
    p.add_argument("--year", type=int, default=2026)
    p.set_defaults(func=cmd_estimate)

    p = sub.add_parser("projection", help="cost for every year 2026-2034")
    _add_common(p)
    p.add_argument("--csv", action="store_true", help="print CSV instead of a table")
    p.set_defaults(func=cmd_projection)

    p = sub.add_parser("compare", help="full method vs. 'payable share' shortcut")
    _add_common(p)
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("products", help="list product presets")
    p.set_defaults(func=cmd_products)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except ValueError as exc:
        sys.exit(f"Error: {exc}")


if __name__ == "__main__":
    main()
