#!/usr/bin/env python3
"""
Does volunteer mapping follow the kind of crisis, rather than its size?

OCHA labels each appeal with a plan type. Grouping the country-year panel by
that label tests directly whether mapping tracks sudden-onset disasters more
closely than protracted crises or refugee-hosting.
"""
import json
import numpy as np
import pandas as pd
from analyze import projects, appeals

import os
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

GROUP = {"FA": "Flash appeal (sudden onset)",
         "REG": "Regional refugee response",
         "HRP": "Protracted crisis (HRP)", "HNRP": "Protracted crisis (HRP)",
         "SRP": "Protracted crisis (HRP)", "Other": "Other"}

pr = projects()
plans = json.load(open(os.path.join(DATA, "ocha_plans.json")))
rows = []
for p in plans:
    share = (p.get("requirements") or 0) / len(p["iso3"])
    for i in p["iso3"]:
        rows.append({"iso3": i, "year": p["year"], "usd": share,
                     "ptype": p.get("plan_type"),
                     "grp": GROUP.get(p.get("plan_type"), "Other")})
ap = pd.DataFrame(rows)

# mapping effort in that country in that calendar year
eff = pr.groupby(["iso3", "year"]).agg(
    part=("participations", "sum"), proj=("pid", "size")).reset_index()
ap = ap.merge(eff, on=["iso3", "year"], how="left")
ap["part"] = ap.part.fillna(0)
ap["proj"] = ap.proj.fillna(0)
ap["mapped"] = ap.proj > 0
ap.to_csv(os.path.join(DATA, "appeal_year_panel.csv"), index=False)

print("=" * 74)
print("MAPPING RESPONSE BY THE KIND OF CRISIS OCHA SAYS IT IS")
print("=" * 74)
print(f"{'plan type':<30}{'n':>5}{'% mapped':>10}{'median part':>13}{'part per $B':>13}")
for g, d in ap.groupby("grp"):
    usd = d.usd.sum() / 1e9
    per = d.part.sum() / usd if usd else np.nan
    print(f"{g:<30}{len(d):>5}{d.mapped.mean():>9.0%}"
          f"{d.part.median():>13,.0f}{per:>13,.0f}")

print("\n" + "=" * 74)
print("SAME TEST, ONLY APPEALS OVER $100M (drops tiny plans that skew rates)")
print("=" * 74)
big = ap[ap.usd > 1e8]
print(f"{'plan type':<30}{'n':>5}{'% mapped':>10}{'median part':>13}{'part per $B':>13}")
for g, d in big.groupby("grp"):
    usd = d.usd.sum() / 1e9
    print(f"{g:<30}{len(d):>5}{d.mapped.mean():>9.0%}"
          f"{d.part.median():>13,.0f}{d.part.sum()/usd:>13,.0f}")

print("\n" + "=" * 74)
print("FLASH APPEALS: THE SUDDEN-ONSET CASES, MOST RECENT FIRST")
print("=" * 74)
fa = ap[(ap.ptype == "FA")].sort_values("year", ascending=False)
print(f"  {len(fa)} flash-appeal country-years, {fa.mapped.mean():.0%} drew mapping")
for _, r in fa.head(16).iterrows():
    m = f"{r.proj:>4.0f} proj {r.part:>7,.0f} part" if r.mapped else "   no mapping that year"
    print(f"    {r.year}  {r.iso3}  ${r.usd/1e6:>6.0f}M   {m}")
