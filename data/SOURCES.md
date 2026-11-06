# Data sources

| Parameter | Value used | Legal basis | Where I checked it |
|---|---|---|---|
| CBAM factor 2026–2034 | 97.5 %, 95 %, 90 %, 77.5 %, 51.5 %, 39 %, 26.5 %, 14 %, 0 % | Art. 10a(1a) Directive 2003/87/EC (as amended in 2023) | GreenSutra CBAM cost calculator; cbamguide.com free-allocation schedule |
| Default-value mark-up | +10 % (2026), +20 % (2027), +30 % (2028 onwards) | Implementing Regulation (EU) 2025/2621 | GreenSutra, "CBAM mark-up on steel default values" |
| India default values | Pig iron 2.53, DRI 4.20, hot-rolled flat 4.28 tCO2e/t | Implementing Regulation (EU) 2025/2621, Annex I | GreenSutra, "Default values for Indian steel exports" |
| Benchmark, hot-rolled flat (default-value route) | 1.370 tCO2e/t | CBAM benchmark implementing act | GreenSutra worked example (0.975 × 1.00 × 1.370) |
| Cross-sectoral correction factor | 1.00 (2026–2030) | Implementing Decision (EU) 2026/1862 | GreenSutra CBAM cost calculator |
| Certificate price | €75.36 (Q1 2026), €82.32 (Q3 2026) | Quarterly price publication, Regulation (EU) 2023/956 | GreenSutra; MSE commentary April 2026 |
| De minimis threshold | 50 t net mass per importer per year | Regulation (EU) 2025/2083 (CBAM simplification) | GreenSutra CBAM cost calculator |

## What is *not* included

* **Benchmarks for pig iron and DRI.** I could not confirm them from a source I trust, so the
  CSV leaves them empty. The calculator then asks you to pass `--benchmark` yourself.
* **The July 2026 ETS revision proposal, COM(2026) 616.** It would bring back 15 % of free allocation
  from 2028 and push full phase-in to 2038. It is still a proposal, so the tool uses the law in force.
* **India's Carbon Credit Trading Scheme (CCTS).** It is not currently recognised as a carbon price
  "effectively paid" under Article 9, so the origin-price deduction defaults to 0. You can test
  scenarios where it is recognised with `--origin-price`.

Check the official texts on EUR-Lex before using any figure in published work.
