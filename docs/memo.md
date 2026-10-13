# Memo

**Title:** Cap Ad Frequency and Rebalance Spend Toward High-Efficiency Campaigns
**To:** Product Manager, Ad Platform
**From:** Analytics Team
**Date:** October 2026

---

## 1. Problem

Across 661 qualifying campaigns (>=1,000 impressions each), a disproportionate share of Criteo ad budget flows to campaigns that under-deliver on campaign-attributed conversion credit. At the same time, conversion rate increases monotonically with ad frequency. That relationship is observational and may reflect user-intent differences rather than causal frequency effects.

## 2. Key Findings

**Finding 1 -- Spend concentration without conversion payoff**
The top 20% of qualifying campaigns by spend (132 of 661) account for **72.8% of transformed cost** but deliver **62.9% of campaign-attributed conversion credit** -- a **9.9 percentage-point efficiency gap**. This spend-versus-credit gap is the stronger signal than a best-to-worst campaign cost-per-conversion ratio, which is highly sensitive to low-volume campaigns. *(Source: `results/campaign_performance.csv`, Charts 1 & 2.)*

**Finding 2 -- Attribution model is robust at the top, but reshuffles mid-tier**
The full dataset contains **16,468,027 impressions** and **435,810 distinct conversion IDs**, of which **236,331 (54.2%) are uniquely attributed to Criteo**. The 661 qualifying campaigns receive **236,948 campaign-level attribution credits** because a small number of conversion paths touch multiple campaigns; campaign credit is therefore distinct from the unique portfolio count. The top 3 campaigns by credit are stable across all four attribution models (last-touch, first-touch, linear, time-decay), while mid-tier campaigns (ranks 4-50) shift materially. *(Source: `results/attribution_model_comparison.csv`, `results/funnel_by_campaign.csv`.)*

**Finding 3 -- Frequency correlates with conversion; lag requires conversion-level counting**
Conversion rate rises monotonically with frequency: **1.6%** (1 impression) -> **4.4%** (2) -> **8.2%** (3-4) -> **15.2%** (5-9) -> **28.3%** (10+). Selection bias is likely: heavy-exposure users may have higher purchase intent independent of ad volume. The corrected lag analysis collapses each conversion ID to one record and measures from its last impression: **38.9%** occur within 1 hour and **62.7%** within 3 days. The remaining conversions extend through the observed 30-day dataset window. *(Source: `results/frequency_buckets.csv`, `results/conversion_lag_buckets.csv`.)*

---

## 3. Recommendation

**Introduce a frequency cap of 9 impressions per user per campaign per 7-day rolling window** and reallocate freed impressions toward the top-quintile most efficient campaigns.

The 9-impression threshold preserves the observed 5-9 bucket while avoiding an unvalidated assumption that the 10+ bucket represents incremental causal lift. This is a testable product hypothesis, not a conclusion from the observational data.

**Scope:** All 661 campaigns with >=1,000 impressions. Use one consistent attribution model for the experiment; last-touch is recommended for continuity with the existing attribution flag.

## 4. Expected Impact and Success Metric

**Primary metric:** Cost per attributed conversion -- target a >=10% reduction in treatment, informed by the 9.9 percentage-point spend-versus-campaign-credit gap.

**Win condition:** Cost per attributed conversion falls by >=10% with statistical significance (p < 0.05) after the pre-specified analysis window.

**Guardrail:** Unique attributed conversions must not decline by more than 5% -- the goal is efficiency, not sacrificing volume.

## 5. How We'd Test It

| Parameter | Detail |
|---|---|
| **Unit of randomization** | User, to prevent cross-contamination |
| **Design** | 50/50 A/B split |
| **Treatment** | Hard frequency cap: 9 impressions per campaign per 7-day window |
| **Control** | No cap (current behavior) |
| **Duration** | Minimum 2 weeks; extend to 4 weeks to capture the full observed conversion window |
| **Primary metric** | Cost per attributed conversion (treatment vs control) |
| **Guardrail** | Unique attributed conversions (<=5% drop acceptable) |
| **Analysis** | Pre-specified two-sided comparison with daily monitoring for novelty effects |

## 6. Risks and Caveats

- **Observational data, not causal.** High-frequency users may have inherently higher purchase intent; the A/B test is required before attributing conversion uplift to frequency.
- **Conversion-level counting.** The raw `conversion = 1` flag marks impression rows associated with a conversion window. Portfolio counts and lag distributions therefore collapse repeated rows by `conversion_id`; frequency analysis flags each user-campaign pair only once.
- **Dataset-card discrepancy.** The downloaded database currently returns 435,810 distinct positive `conversion_id` values, not the approximately 45K conversions stated in the upstream README. This project reports the observed conversion IDs and flags the upstream discrepancy rather than silently substituting a different definition.
- **Transformed cost.** `cost` and `cpo` are transformed by Criteo and cannot be expressed in real currency. Cost comparisons are relative only.
- **Full dataset used.** The run uses all **16,468,027 impressions** across **6,142,256 users** and 675 campaigns. Campaign-level tables retain the 661 campaigns with at least 1,000 impressions, containing **16,460,456 impressions**.
- **Attribution model sensitivity.** Top-3 campaign rankings are stable across models, but mid-tier rankings shift. Decisions beyond the top cohort are model-dependent.
- **Advertiser-side data only.** No publisher or placement data is available, so publisher effects cannot be measured here.

## 7. Implication for Publishers *(reasoning only -- not measured in this dataset)*

A frequency cap will reduce impressions served to high-frequency users, which may temporarily reduce ad-request volume from Criteo campaigns on publisher inventory. If improved advertiser efficiency increases retention and platform budget, publisher fill and effective RPM could recover; this requires publisher-side data to quantify.

---

*All numbers above are derived from verified query outputs in `results/`. The default command `python run_all.py` runs the full dataset; `python run_all.py --sample-users` enables the optional deterministic 5% user sample. The dataset is licensed CC BY-NC-SA 4.0; public use must retain the Criteo authors' attribution and is non-commercial/share-alike.*
