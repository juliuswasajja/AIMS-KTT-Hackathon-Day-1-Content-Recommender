# Dispatcher Plan: Made in Rwanda Content Recommender

## Use Case
A leatherworker in Nyamirambo has no smartphone.  
He cannot check dashboards, ads, or apps.  
So the system must convert weekly search demand into a simple SMS or voice update he can act on.

## Weekly Leads Workflow
### 1) Who aggregates demand
- A district **Lead Dispatcher** (hosted by the cooperative desk or sector business office) exports weekly recommended-query volume every Monday morning.
- Input is simple: top queries from `queries.csv`, matched local SKUs from recommender output, and recent click/popularity signal from `click_log.csv`.

### 2) How the artisan is contacted
- Primary channel: SMS digest to feature phone (Monday afternoon).
- If no reply in 24 hours: dispatcher places a short voice call.
- If literacy is low: dispatcher uses voice first, then sends one confirmation SMS.

### 3) Exact numbers in the weekly message
Each artisan gets only 4 numbers:
- `Total buyer intent count` for this week (matched to their product type)
- `Top 3 query themes + counts` (for example: "leather tote women: 28")
- `Week-on-week change` (up/down % versus last week)
- `Suggested units to prepare` for top items (simple estimate = intent count x expected conversion)

### 4) What happens after contact
- Artisan confirms: `available now`, `made-to-order`, or `not available`.
- Dispatcher logs response in a shared sheet.
- Available items are pushed to partner sellers/market channels for the week.
- End of week: dispatcher records leads sent, orders closed, and issues (price, stock, quality, delivery).

## Sample SMS Digest (Simple Wording)
`Muraho Jean (Nyamirambo). This week leather demand: 46 searches. Top: tote bag 21, wallet gift 15, belt women 10. Vs last week: +18%. Prepare: tote 6, wallet 4, belt 3. Reply 1=ready, 2=made to order, 3=not available.`

## Voice/Call Fallback (Non-Smartphone or Low Literacy)
Dispatcher call script (60-90 seconds):
1. Greet and identify cooperative/project.
2. Read the 3 top demand items and counts slowly.
3. Ask stock status for each item.
4. Confirm one weekly production target.
5. Repeat back and confirm next check-in date.

If artisan cannot read SMS, dispatcher records call outcome and sends SMS only to family/co-op contact if agreed.

## 3-Month Pilot (20 Artisans)
- Location focus: Nyamirambo + nearby Kigali leather clusters.
- Cohort: 20 artisans (mostly leather; a few mixed craft sellers for comparison).
- Duration: 12 weeks.
- Cadence: weekly demand digest, weekly response tracking, and monthly review of conversion and pricing issues.

Success checks by month 3:
- at least 80% weekly response rate
- at least 1 confirmed lead action per artisan per week
- clear uplift in matched sales versus week 1 baseline

## Rough Unit Economics (Pilot Assumptions)
Assumptions for 3 months:
- Dispatcher stipend: `250,000 RWF/month` -> `750,000 RWF`
- Airtime + SMS: `120,000 RWF/month` -> `360,000 RWF`
- Field transport/check-ins: `180,000 RWF` total
- **Total pilot ops cost: 1,290,000 RWF**

Lead assumptions:
- 20 artisans x 10 usable leads/week x 12 weeks = **2,400 leads**
- **Cost per lead = 1,290,000 / 2,400 = 538 RWF**
- **Cost per artisan onboarded = 1,290,000 / 20 = 64,500 RWF**

Break-even GMV:
- If contribution margin to operations is `12%`, break-even GMV is `1,290,000 / 0.12 = 10,750,000 RWF` over 3 months.

Plain reading:
- Pilot breaks even around **10.8M RWF GMV** in 3 months, or about **180k RWF per artisan per month**.

