# Memo

**Title:** Cap Ad Frequency and Rebalance Spend Toward High-Efficiency Campaigns

**To:** Product Manager, Ad Platform    **From:** [Your name]    **Date:** October 2026

---

## 1. Problem

Across 661 qualifying campaigns (>=1,000 impressions each), a disproportionate share of Criteo ad budget flows to campaigns that under-deliver on attributed conversions. At the same time, conversion rate increases monotonically with ad frequency -- yet the relationship is observational and may reflect user-intent differences rather than causal frequency effects. We need to decide whether to introduce a frequency cap and reallocate freed budget to higher-efficiency campaigns to improve overall cost per attributed conversion.

---

## 2. Key Findings

**Finding 1 -- Spend concentration without conversion payoff**
The top 20% of campaigns by spend (132 of 661) account for **72.6% of total transformed cost** but deliver only **62.8% of attributed conversions** -- a **9.8 percentage-point efficiency gap**. The least efficient campaign costs **1,413x more** per attributed conversion than the most efficient (transformed cost ratio). *(Source: 
esults/campaign_performance.csv, Charts 1 & 2)*

**Finding 2 -- Attribution model is robust at the top, but reshuffles mid-tier**
The dataset covers **16.46 M impressions** yielding **236,948 attributed conversions** out of 438,275 total conversions (**54.1% attribution rate**). The top 3 campaigns by credit are stable across all four attribution models (last-touch, first-touch, linear, time-decay), suggesting the top cohort is genuinely high-performing. However, mid-tier campaigns (ranks 4-50) shift materially between models, meaning spend-reallocation decisions are sensitive to the attribution rule chosen. All conversions in this dataset had a click somewhere in the path to conversion (share_conversions_with_click = 100%) -- consistent with a last-click rule, though the dataset does not document the exact attribution logic. *(Source: 
esults/attribution_model_comparison.csv, 
esults/funnel_by_campaign.csv)*

**Finding 3 -- Strong frequency-conversion correlation; 38.9% of conversions occur within 1 hour**
Conversion rate rises monotonically with frequency: **1.6%** (1 impression) -> **4.4%** (2) -> **8.2%** (3-4) -> **15.2%** (5-9) -> **28.3%** (10+) -- a 17.5x spread. Selection bias is likely: heavy-exposure users may have higher purchase intent independent of ad volume. Separately, **38.9% of conversions occur within 1 hour** of the last touchpoint, 77.1% within 3 days, and 20.7% take 7-30 days. The memo A/B test runs for 4 weeks specifically to capture this full conversion tail; a shorter window would miss ~20% of conversions. *(Source: 
esults/frequency_buckets.csv, 
esults/conversion_lag_buckets.csv, Chart 4)*

---

## 3. Recommendation

**Introduce a frequency cap of 9 impressions per user per campaign per 7-day rolling window** and reallocate freed impressions toward the top-quintile most efficient campaigns (lowest cost per attributed conversion).

*Rationale for 9:* Conversion rate increases significantly through the 5-9 bucket (15.2%) and continues into 10+ (28.3%), but the 10+ bucket contains only 173,977 user-campaign pairs versus 499,984 in the 5-9 bucket -- a sharply smaller, likely self-selected population. Capping at 9 preserves the proven 5-9 uplift while eliminating potentially wasteful over-exposure above that threshold.

*Scope:* All 661 campaigns with >=1,000 impressions. Attribution decisions should use a consistent model (recommend **last-touch** for continuity with the existing ttribution flag, unless the team is ready to adopt a multi-touch model).

---

## 4. Expected Impact and Success Metric

**Primary metric:** Cost per attributed conversion -- target a >=10% reduction in the treatment group (informed by the 9.8 pp efficiency gap between the top 20% by spend and their conversion share).

**How to call it a win:** Cost per attributed conversion falls by >=10% with statistical significance (p < 0.05) after 2 weeks.

**Guardrail metric:** Total attributed conversions in the treatment group must not decline by more than 5% -- we are optimizing efficiency, not sacrificing volume.

**Secondary watch:** Attribution rate (attributed / total conversions). If the frequency cap reduces impressions near conversion events, attribution rate could shift; monitor for material change.

---

## 5. How We'd Test It

| Parameter | Detail |
|---|---|
| **Unit of randomization** | User (to prevent cross-contamination) |
| **Design** | 50/50 A/B split |
| **Treatment** | Hard frequency cap: 9 impressions per campaign per 7-day window |
| **Control** | No cap (current behavior) |
| **Duration** | Minimum 2 weeks; extend to 4 weeks to capture the 7-30-day conversion tail (20.7% of conversions) |
| **Primary metric** | Cost per attributed conversion (treatment vs control) |
| **Guardrail** | Total attributed conversions (<=5% drop acceptable) |
| **Analysis** | Two-sided t-test on cost per attributed conversion; daily monitoring for novelty effects |

---

## 6. Risks and Caveats

- **Observational data, not causal.** The frequency-conversion relationship is a correlation. High-frequency users may have inherently higher purchase intent; the A/B test in Section 5 is required before attributing the conversion uplift to frequency.
- **Transformed cost.** cost and cpo are transformed by Criteo and cannot be expressed in real currency. All cost comparisons here are relative (campaign vs campaign).
- **Full dataset used.** This analysis used the complete Criteo dataset -- 16,468,027 impressions across 6,142,256 users (the sampling clause was removed for this run). Results reflect the full 30-day traffic, not an estimate.
- **Attribution model sensitivity.** Top-3 campaign rankings are stable across models, but mid-tier rankings shift. Budget-reallocation decisions beyond the top cohort are model-dependent. Do not reallocate mid-tier spend without agreeing on an attribution model first.
- **Conversion window.** 20.7% of conversions occur 7-30 days after the last touchpoint. The test is designed to run 4 weeks to capture this tail; ensure the attribution window matches the experiment duration.
- **Advertiser-side data only.** No publisher or placement data is available. Publisher-side effects of frequency capping cannot be measured here.

---

## 7. Implication for Publishers *(reasoning only -- not measured in this dataset)*

Introducing a frequency cap will reduce the number of impressions served to high-frequency users, which may temporarily reduce ad request volume from Criteo campaigns on publisher inventory. However, if improved advertiser cost efficiency increases advertiser retention and total budget on the platform, publisher fill rates and effective RPM could recover or increase over a 1-2 quarter horizon. This effect is unobservable in the current dataset and requires publisher-side data (placement, RPM, fill rate) to quantify.

---

*All numbers above are derived from verified query outputs in `results/`. Full dataset run: 16,468,027 impressions, 6,142,256 users, 661 qualifying campaigns (>=1,000 impressions), 236,948 attributed conversions. The 5% sampling clause is restored in `sql/01_load_sample.sql`; remove the WHERE clause to reproduce this full-data run.*
