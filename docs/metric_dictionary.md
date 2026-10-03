# Metric Dictionary

> **Scope:** Criteo Attribution Analytics project — user-level 5% sample of Criteo display-ad data (30 days, ~[N] impressions after sampling). All metrics computed in DuckDB from the `stg_events` view unless stated otherwise.

---

## Core Counts

| Metric | Definition | DuckDB expression |
|---|---|---|
| **Impressions** | Count of ad impressions served | `COUNT(*)` on `stg_events` |
| **Users** | Distinct users in the sample | `COUNT(DISTINCT uid)` |
| **Campaigns** | Distinct campaigns with ≥ 1,000 impressions | `COUNT(DISTINCT campaign)` in `res_campaign` |
| **Clicks** | Impressions where `click = 1` | `SUM(click)` |

---

## Conversion Metrics

| Metric | Definition | Notes |
|---|---|---|
| **Conversions** | `COUNT(DISTINCT conversion_id)` where `conversion_id IS NOT NULL` | **Not** `SUM(conversion)`. One conversion event can appear on multiple impression rows (Pitfall 2 from dataset). |
| **Attributed conversions** | `COUNT(DISTINCT conversion_id)` where `attribution = 1` | Conversions credited to Criteo under the dataset's attribution rule. A different rule (last-touch, first-touch) would change this number. |
| **Conversion flag rows** | `SUM(conversion)` | Raw flag sum — overcounts if `conversion_id` repeats across rows. Used only for the sanity check in Block 2. |

---

## Rate Metrics

| Metric | Definition | Formula |
|---|---|---|
| **CTR** (click-through rate) | Share of impressions that were clicked | `clicks / impressions` |
| **Attribution rate** | Share of conversions that Criteo was credited for | `attributed_conversions / conversions` |
| **Share of conversions with a click** | Among all conversions for a campaign, how many had at least one click in the path | `conversions_with_click / conversions` |
| **Conversion rate (frequency analysis)** | Among all (user, campaign) pairs in a frequency bucket, the fraction where the user had any conversion | `AVG(converted)` in `res_frequency` |

---

## Cost Metrics

| Metric | Definition | Important caveat |
|---|---|---|
| **Cost** | `SUM(cost)` | **Transformed value** — not real currency. Use only for relative comparisons between campaigns. Never present as monetary amounts. |
| **Cost per attributed conversion** | `total_cost / attributed_conversions` | Our own derived metric; uses the transformed cost. Compare campaigns to each other only. |
| **CPO** (`cpo` column) | Cost per order as recorded in the dataset | Also transformed; dataset-level metric, not our computation. |

---

## Share Metrics

| Metric | Definition | Formula |
|---|---|---|
| **Spend share** | Campaign's share of total transformed cost | `total_cost / SUM(total_cost) OVER ()` |
| **Conversion share** | Campaign's share of total attributed conversions | `attributed_conversions / SUM(attributed_conversions) OVER ()` |
| **Efficiency gap** | Spend share minus conversion share | Positive = campaign costs more than it delivers relative to the portfolio |

---

## Frequency Metrics

| Metric | Definition |
|---|---|
| **Frequency** | Number of impressions a user received from one campaign |
| **Frequency bucket** | Grouped frequency ranges: `1`, `2`, `3-4`, `5-9`, `10+` |
| **User-campaign pair** | One (uid, campaign) combination; the unit of analysis in `res_frequency` |

---

## Data Pitfalls (stated once, applied everywhere)

1. **`-1` is a NULL placeholder.** All `-1` values in `conversion_timestamp`, `conversion_id`, `click_pos`, `click_nb`, and `time_since_last_click` are converted to `NULL` in the staging view (`stg_events`). Never average or compare raw `-1` values.

2. **Conversion IDs repeat across impression rows.** One `conversion_id` can appear on many rows. Always use `COUNT(DISTINCT conversion_id)` for conversion counts. `SUM(conversion)` is used only as a diagnostic cross-check.

3. **Cost and CPO are transformed.** The dataset documentation confirms both columns are transformed and cannot be converted to real currency. All cost-based comparisons in this project are relative (campaign A vs campaign B), not absolute.

---

*Last updated: [date of analysis run]. All metrics verified via `sql/06_reconciliation.sql`.*
