import pytest

from cbam_calc import calculator, policy

HRF = policy.load_products()["hot_rolled_flat"]


def test_cbam_factor_schedule_is_monotonic_and_ends_at_zero():
    factors = [policy.cbam_factor(y) for y in range(2026, 2035)]
    assert factors == sorted(factors, reverse=True)
    assert factors[0] == 0.975 and factors[-1] == 0.0
    assert policy.cbam_factor(2040) == 0.0


def test_markup_steps():
    assert policy.default_value_markup(2026) == 0.10
    assert policy.default_value_markup(2027) == 0.20
    assert policy.default_value_markup(2028) == 0.30
    assert policy.default_value_markup(2033) == 0.30


def test_rejects_years_before_definitive_period():
    with pytest.raises(ValueError):
        calculator.estimate(100, 2025, product=HRF)


def test_worked_example_500t_hot_rolled_2026():
    # 500 t, India default 4.28 x 1.10 = 4.708 -> 2,354 t embedded;
    # adjustment 0.975 x 1.00 x 1.370 x 500 = 667.875 t.
    e = calculator.estimate(500, 2026, product=HRF, price=82.32)
    assert e.intensity == pytest.approx(4.708)
    assert e.embedded_emissions == pytest.approx(2354.0)
    assert e.free_allocation_adjustment == pytest.approx(667.875)
    assert e.certificates == pytest.approx(1686.125)
    assert e.cost_eur == pytest.approx(1686.125 * 82.32)


def test_verified_intensity_skips_markup():
    e = calculator.estimate(100, 2028, product=HRF, verified_intensity=2.0)
    assert e.intensity == 2.0
    assert e.intensity_basis == "verified"


def test_low_emitter_owes_nothing_while_free_allocation_is_high():
    threshold = calculator.break_even_intensity(2026, HRF.benchmark)
    e = calculator.estimate(1000, 2026, product=HRF, verified_intensity=threshold - 0.01)
    assert e.certificates == 0.0


def test_full_phase_in_charges_all_embedded_emissions():
    e = calculator.estimate(1000, 2034, product=HRF, verified_intensity=1.8)
    assert e.free_allocation_adjustment == 0.0
    assert e.certificates == pytest.approx(1800.0)


def test_de_minimis_exemption():
    e = calculator.estimate(40, 2027, product=HRF)
    assert e.exempt and e.cost_eur == 0.0
    # Same line, but the importer brings in 200 t of covered goods in total
    e = calculator.estimate(40, 2027, product=HRF, annual_importer_tonnes=200)
    assert not e.exempt and e.cost_eur > 0


def test_origin_carbon_price_reduces_bill_but_never_below_zero():
    base = calculator.estimate(1000, 2030, product=HRF, price=80)
    with_ccts = calculator.estimate(1000, 2030, product=HRF, price=80, origin_carbon_price=20)
    assert with_ccts.cost_eur < base.cost_eur
    huge = calculator.estimate(1000, 2030, product=HRF, price=80, origin_carbon_price=500)
    assert huge.certificates >= 0.0


def test_product_without_benchmark_requires_one():
    pig = policy.load_products()["pig_iron"]
    with pytest.raises(ValueError, match="benchmark"):
        calculator.estimate(100, 2026, product=pig)
    e = calculator.estimate(100, 2026, product=pig, benchmark=1.3)
    assert e.certificates > 0


def test_costs_rise_every_year_on_default_values():
    costs = [e.cost_eur for e in calculator.projection(1000, product=HRF)]
    assert all(b >= a for a, b in zip(costs, costs[1:]))


def test_shortcut_understates_for_high_emitters():
    e = calculator.estimate(1000, 2026, product=HRF)
    short = calculator.simplified_estimate(1000, 2026, e.intensity, e.price)
    assert short < e.cost_eur
