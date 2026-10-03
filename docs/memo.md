# Memo

**Title:** Cap Ad Frequency and Rebalance Spend Toward High-Efficiency Campaigns

**To:** Product Manager, Ad Platform &nbsp;&nbsp; **From:** [Your name] &nbsp;&nbsp; **Date:** [Date of analysis]

---

## 1. Problem

A meaningful share of Criteo campaign budget is flowing to campaigns that generate a disproportionately small share of attributed conversions, suggesting both over-frequency and misallocated spend. We need to decide whether to introduce a frequency cap and reallocate budget to improve cost efficiency across the platform.

---

## 2. Key Findings

- **Finding 1 — Spend concentration without conversion payoff:** The top 20% of campaigns by spend (38 of 191 qualifying campaigns) account for **60.3% of total transformed cost** but deliver only **41.7% of attributed conversions** — an 18.6 percentage-point efficiency gap. The least efficient campaign costs **1,212× more** per attributed conversion than the most efficient. *(Source: `results/campaign_performance.csv`, Chart 1 & 2)*

- **Finding 2 — Attribution gap:** Of 17,175 total conversions in qualifying campaigns, only **9,159 (53.3%) are attributed to Criteo** under the dataset's built-in rule. This means nearly half of observed conversions are not credited to Criteo's impressions under the current attribution model. *(Source: `results/funnel_by_campaign.csv`, Chart 5)*

- **Finding 3 — Frequency-conversion correlation:** Users who saw a campaign's ads **10+ times** converted at **28.2%**, vs **1.6%** for users who saw just 1 ad — a 17.5× difference. The relationship is monotonically increasing across all five frequency buckets (1 → 2 → 3-4 → 5-9 → 10+: 1.6% → 4.3% → 8.1% → 14.8% → 28.2%). *(Source: `results/frequency_buckets.csv`, Chart 4)*

---

## 3. Recommendation

**Introduce a frequency cap of 9 impressions per user per campaign per 7-day window** and reallocate freed budget toward the top-quintile most efficient campaigns (lowest cost per attributed conversion).

*What to change:* Set a hard frequency cap at the user–campaign level in campaign delivery. The data shows conversion rate continues rising through the 5–9 bucket (14.8%) to the 10+ bucket (28.2%), but the 10+ bucket has only 8,789 pairs vs 24,636 in the 5–9 bucket — a sharply diminishing population at extreme frequency. A cap at 9 captures the 5–9 conversion uplift while preventing over-exposure.
*For whom:* All 191 campaigns with ≥ 1,000 impressions in the sample period.
*Test scope:* A/B test (see Section 5).

---

## 4. Expected Impact and Success Metric

**Primary metric:** Cost per attributed conversion — target a 15–25% reduction in the treatment group (informed by the 18.6 pp efficiency gap observed between top and bottom spend quartiles).

**How to call it a win:** Cost per attributed conversion falls by ≥ 15% with statistical significance (p < 0.05) after 2 weeks.

**Guardrail metric:** Total attributed conversions must not decline by more than 5% — we are optimizing efficiency, not sacrificing volume.

---

## 5. How We'd Test It

- **Unit of randomization:** User (to avoid cross-contamination between control and treatment).
- **Design:** 50/50 A/B split. Treatment group sees a hard frequency cap of **9 impressions per campaign per 7-day window**; control group sees no cap.
- **Duration:** Minimum 2 weeks to capture weekly ad-serving patterns; extend if conversion windows are longer than 7 days.
- **Primary metric:** Cost per attributed conversion (treatment vs control).
- **Guardrail:** Total attributed conversions in treatment group vs control (≤5% drop acceptable).
- **Analysis:** Two-sided t-test on cost per attributed conversion; track daily to catch novelty effects early.

---

## 6. Risks and Caveats

- **Observational data, not causal.** The frequency–conversion relationship observed here is a correlation. High-frequency users may have inherently higher intent; frequency itself may not be causing the outcome. The A/B test in Section 5 is required to establish causation.
- **Transformed cost.** `cost` and `cpo` are transformed by Criteo and cannot be expressed in real currency. All cost comparisons in this memo are relative (campaign vs campaign).
- **User-level sample.** This analysis used a 5% user-level sample (**823,604 impressions, 307,695 users**). Estimates may differ from the full dataset; always re-run on full data before making production decisions.
- **Advertiser-side data only.** The dataset contains no publisher or placement information. Publisher-side effects (e.g., which placements benefit from frequency capping) cannot be measured here.
- **Attribution rule affects counts.** Attributed conversions here use the dataset's built-in rule (`attribution = 1`). A different attribution model (last-touch, time-decay) would redistribute credit and change campaign rankings. See *Future Plan: Attribution Model Comparison*.

---

## 7. Implication for Publishers *(reasoning, not measured)*

If frequency capping reduces the number of impressions served to high-frequency users, publishers may see a short-term drop in ad requests from Criteo campaigns. However, if more efficient spend improves advertiser ROI and retention on the platform, total demand — and thus publisher fill rates and RPM — could increase over a longer horizon. This effect is not observable in the current dataset and would require publisher-side data to validate.

---

*All numbers above must come from your own query runs. Do not quote agent-generated estimates without verifying them yourself.*
