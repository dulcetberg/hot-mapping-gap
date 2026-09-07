# Where humanitarian mapping happens

Volunteer mapping is a finite resource. This project asks where it actually
lands, and how closely that tracks where the humanitarian system says the need
is.

It joins every public project in the Humanitarian OpenStreetMap Team's Tasking
Manager (14,510 projects across 160 countries, 2013 to 2026) against every UN
humanitarian response plan recorded by OCHA (532 plans across 111 countries,
2014 to 2026, totalling about $400 billion requested).

I started mapping for HOT about 2 months ago, mostly in Syria. This started as
a question about what I had joined.

## What it found

**Volunteer attention saturates.** Across the range as a whole, bigger appeals
do draw more mapping. Among the 36 largest emergencies, those appealing for a
billion dollars or more, that relationship disappears completely
(r = -0.12, p = 0.49). Past a certain size, a worse emergency does not recruit
more volunteers, which means the biggest crises are exactly where volunteer
mapping covers the smallest share of the need.

**The effort is highly concentrated.** The top 20 countries hold 60% of all
project participations. The least-mapped half of the 160 mapped countries holds
3.2% between them.

**A sixth of it goes outside the humanitarian system entirely.** 63 countries
that never had a UN appeal hold 16% of all volunteer effort.

## What it did not find

I expected volunteers to respond to sudden-onset disasters and to skip
protracted conflict. Using OCHA's own plan type as a label, so that the
classification is not mine, that difference is **not statistically significant**
(p = 0.06). Refugee-hosting appeals did look dramatically less mapped, but most
of that turned out to be wealthy European states inside the Ukraine regional
plans, whose maps are already complete. Dropping high-income countries cut the
effect from p = 0.0001 to p = 0.21.

The intuitive story is not supported by this data, so it is not claimed.
`tests.py` keeps the failed test alongside the ones that worked.

## Method note: dating 14,702 projects without hammering the API

The Tasking Manager returns creation dates only from its per-project endpoint,
at roughly 90KB a call. Fetching all of them would have pulled well over a
gigabyte off a nonprofit's API to read one field.

Project IDs are handed out sequentially, so `dates.py` samples 204 real
creation dates spread across the whole ID range, confirms the relationship
never runs backwards, and interpolates the rest. Validated against 60 held-out
projects the fit never saw: median error 0.33 days, worst case 5.5 days.

## Running it

```
python3 fetch_projects.py     # ~40 min, polite delay, caches to data/
python3 fetch_plans.py        # ~10 s
python3 analyze.py            # the headline numbers
python3 tests.py              # the statistics, including the failed hypothesis
python3 make_figures.py       # the three figures
```

## Sources

- HOT Tasking Manager API, `tasking-manager-tm4-production-api.hotosm.org`
- UN OCHA Humanitarian Programme Cycle API, `api.hpc.tools`
- World Bank country income classifications
- Natural Earth 1:50m admin 0 boundaries

Maps are drawn on Equal Earth (EPSG:8857). A map about where humanitarian need
is concentrated should not use a projection that inflates the wealthy northern
latitudes and shrinks the tropics.

## Caveats

- `totalContributors` is recorded per project, so a volunteer who maps five
  projects counts five times. The unit is a project participation, not a person.
- Appeal dollars are an imperfect measure of mappable need. Indonesia is the
  clearest case: a $50M appeal against 77,265 participations, because
  middle-income countries handle their own disasters without asking the UN.
  Countries appealing for under $100M are held out of the per-dollar figures.
- The Tasking Manager is not all humanitarian mapping. Bilateral work, partner
  mapping and national mapping agencies do not appear here.
