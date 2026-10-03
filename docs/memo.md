# Memo

**Title:** Cap Ad Frequency and Rebalance Spend Toward High-Efficiency Campaigns

**To:** Product Manager, Ad Platform &nbsp;&nbsp; **From:** [Your name] &nbsp;&nbsp; **Date:** [Date of analysis]

---

## 1. Problem

A meaningful share of Criteo campaign budget is flowing to campaigns that generate a disproportionately small share of attributed conversions, suggesting both over-frequency and misallocated spend. We need to decide whether to introduce a frequency cap and reallocate budget to improve cost efficiency across the platform.

---

## 2. Key Findings

> **Fill in the bracketed numbers after running your queries.**

- **Finding 1 — Spend concentration without conversion payoff:** The top [X]% of campaigns by spend account for [Y]% of total transformed cost but deliver only [Z]% of attributed conversions. This efficiency gap suggests material waste in the current allocation. *(Source: `results/campaign_performance.csv`, Chart 2)*

- **Finding 2 — Funnel leakage is view-driven, not click-driven:** Across campaigns with ≥ 1,000 impressions, [P]% of conversions happened with no click in the path (post-view attribution). For campaigns where this share exceeds [Q]%, clicks may not be the right optimization signal. *(Source: `results/funnel_by_campaign.csv`, Chart 5)*

- **Finding 3 — Diminishing returns appear at high frequency:** Users who saw a campaign's ads [10+] times had a conversion rate of [R]%, compared to [S]% for users who saw 1–2 ads. Continuing to serve impressions beyond this threshold appears to yield diminishing incremental returns. *(Source: `results/frequency_buckets.csv`, Chart 4)*

---

## 3. Recommendation

**Introduce a frequency cap of [N] impressions per user per campaign per 7-day window** and reallocate freed impressions and budget toward the top-[K] most efficient campaigns (lowest cost per attributed conversion).

*What to change:* Set a hard frequency cap at the user–campaign level in campaign delivery.
*For whom:* All campaigns with sufficient volume (≥ 1,000 impressions in the sample period).
*Test scope:* A/B test (see Section 5).

---

## 4. Expected Impact and Success Metric

**Primary metric:** Cost per attributed conversion — target a [X]% reduction in the treatment group.

**How to call it a win:** Cost per attributed conversion falls by ≥ [X]% with statistical significance (p < 0.05) after [duration].

**Guardrail metric:** Total attributed conversions must not decline by more than [Y]% — we are optimizing efficiency, not sacrificing volume.

---

## 5. How We'd Test It

- **Unit of randomization:** User (to avoid cross-contamination between control and treatment).
- **Design:** 50/50 A/B split. Treatment group sees a hard frequency cap of [N] impressions per campaign per 7-day window; control group sees no cap.
- **Duration:** Minimum 2 weeks to capture weekly patterns; longer if conversion windows are long.
- **Primary metric:** Cost per attributed conversion (treatment vs control).
- **Guardrail:** Total attributed conversions in treatment group vs control.
- **Analysis:** Two-sided t-test on cost per attributed conversion; track daily to catch novelty effects early.

---

## 6. Risks and Caveats

- **Observational data, not causal.** The frequency–conversion relationship observed here is a correlation. High-frequency users may have inherently higher intent; frequency itself may not be causing the outcome. The A/B test in Section 5 is required to establish causation.
- **Transformed cost.** `cost` and `cpo` are transformed by Criteo and cannot be expressed in real currency. All cost comparisons in this memo are relative (campaign vs campaign).
- **User-level sample.** This analysis used a 5% user-level sample ([N] impressions). Estimates may differ from the full dataset; always re-run on full data before making production decisions.
- **Advertiser-side data only.** The dataset contains no publisher or placement information. Publisher-side effects (e.g., which placements benefit from frequency capping) cannot be measured here.
- **Attribution rule affects counts.** Attributed conversions here use the dataset's built-in rule (`attribution = 1`). A different attribution model (last-touch, time-decay) would redistribute credit and change campaign rankings. See *Future Plan: Attribution Model Comparison*.

---

## 7. Implication for Publishers *(reasoning, not measured)*

If frequency capping reduces the number of impressions served to high-frequency users, publishers may see a short-term drop in ad requests from Criteo campaigns. However, if more efficient spend improves advertiser ROI and retention on the platform, total demand — and thus publisher fill rates and RPM — could increase over a longer horizon. This effect is not observable in the current dataset and would require publisher-side data to validate.

---

*All numbers above must come from your own query runs. Do not quote agent-generated estimates without verifying them yourself.*
