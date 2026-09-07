#!/usr/bin/env python3
"""
The statistical tests behind the write-up, including the one that failed.

Run order matters less than reading it: test 3 is a hypothesis I expected to
confirm and could not. It is kept here because a rejected hypothesis is part of
the result, not a draft to be deleted.
"""
import json
import numpy as np
import pandas as pd
from scipy import stats
from analyze import projects, appeals

import os
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

INCOME = json.load(open(os.path.join(DATA, "wb_income.json")))
FLOOR = 1e8          # appeals under $100M make a per-dollar rate meaningless
GROUP = {"FA": "sudden", "HRP": "protracted", "HNRP": "protracted",
         "SRP": "protracted", "REG": "refugee"}


def country_table(pr, ap):
    need = ap.groupby("iso3").usd.sum().rename("usd")
    eff = pr.groupby("iso3").participations.sum().rename("part")
    d = pd.concat([need, eff], axis=1)
    d = d[d.usd > 0].copy()
    d["part"] = d.part.fillna(0)
    d["income"] = [INCOME.get(i, {}).get("income", "unknown") for i in d.index]
    return d


def panel(pr):
    """One row per country-year with an appeal, carrying OCHA's own plan label."""
    rows = []
    for p in json.load(open(os.path.join(DATA, "ocha_plans.json"))):
        g = GROUP.get(p.get("plan_type"))
        if not g:
            continue
        share = (p.get("requirements") or 0) / len(p["iso3"])
        for i in p["iso3"]:
            rows.append({"iso3": i, "year": p["year"], "usd": share, "grp": g})
    pt = pd.DataFrame(rows)
    eff = pr.groupby(["iso3", "year"]).agg(
        part=("participations", "sum"), proj=("pid", "size")).reset_index()
    pt = pt.merge(eff, on=["iso3", "year"], how="left")
    pt[["part", "proj"]] = pt[["part", "proj"]].fillna(0)
    pt = pt[pt.usd > FLOOR].copy()
    pt["mapped"] = pt.proj > 0
    pt["rate"] = pt.part / (pt.usd / 1e9)
    pt["income"] = pt.iso3.map(lambda i: INCOME.get(i, {}).get("income", "unknown"))
    return pt


def main():
    pr, ap = projects(), appeals()
    d = country_table(pr, ap)
    pt = panel(pr)

    print("=" * 72)
    print("TEST 1  Does the size of the appeal predict the volume of mapping?")
    print("=" * 72)
    for name, sub in [("all appeal countries", d),
                      ("appeals >= $100M", d[d.usd >= FLOOR]),
                      ("appeals >= $100M, under $1B", d[(d.usd >= FLOOR) & (d.usd < 1e9)]),
                      ("appeals >= $1B", d[d.usd >= 1e9])]:
        r, p = stats.pearsonr(np.log10(sub.usd), np.log10(sub.part.clip(lower=1)))
        print(f"  {name:<30} n={len(sub):>4}  r={r:+.3f}  p={p:.4f}"
              f"  {'significant' if p < 0.05 else 'NOT significant'}")
    print("\n  Reading: the relationship is real across the range as a whole, and")
    print("  absent among the largest emergencies. Volunteer attention saturates.")

    print("\n" + "=" * 72)
    print("TEST 2  How concentrated is volunteer mapping?")
    print("=" * 72)
    s = pr.groupby("iso3").participations.sum().sort_values(ascending=False)
    tot = s.sum()
    for n in (5, 10, 20, 50):
        print(f"  top {n:>2} countries hold {s.head(n).sum()/tot:6.1%}")
    print(f"  the least-mapped half of the {len(s)} countries holds "
          f"{s.tail(len(s)//2).sum()/tot:.2%}")
    noap = set(s.index) - set(ap.iso3)
    print(f"  {len(noap)} mapped countries never had a UN appeal, holding "
          f"{s[list(noap)].sum()/tot:.1%} of all effort")

    print("\n" + "=" * 72)
    print("TEST 3  Does the KIND of crisis explain it? (the one that failed)")
    print("=" * 72)
    print("  Hypothesis: volunteers respond to sudden-onset disasters and not to")
    print("  protracted conflict. OCHA's own plan type is the non-circular label.\n")
    print(f"  {'group':<12}{'n':>5}{'% mapped':>10}{'median rate':>13}")
    for g, x in pt.groupby("grp"):
        print(f"  {g:<12}{len(x):>5}{x.mapped.mean():>9.0%}{x.rate.median():>13,.0f}")
    su, pro, ref = (pt[pt.grp == g].rate for g in ("sudden", "protracted", "refugee"))
    print()
    for a, b, na, nb in [(su, pro, "sudden", "protracted"),
                         (su, ref, "sudden", "refugee"),
                         (pro, ref, "protracted", "refugee")]:
        _, p = stats.mannwhitneyu(a, b, alternative="two-sided")
        print(f"    {na:<11} vs {nb:<11} p = {p:.4f}"
              f"  {'significant' if p < 0.05 else 'NOT significant'}")

    print("\n  Now the confound: regional refugee plans include Poland, Hungary and")
    print("  the Baltics, wealthy states whose maps are already complete. Drop all")
    print("  high-income countries and test again.\n")
    lm = pt[pt.income != "High income"]
    print(f"  {'group':<12}{'n':>5}{'% mapped':>10}{'median rate':>13}")
    for g, x in lm.groupby("grp"):
        print(f"  {g:<12}{len(x):>5}{x.mapped.mean():>9.0%}{x.rate.median():>13,.0f}")
    su, pro, ref = (lm[lm.grp == g].rate for g in ("sudden", "protracted", "refugee"))
    print()
    for a, b, na, nb in [(su, pro, "sudden", "protracted"),
                         (pro, ref, "protracted", "refugee")]:
        _, p = stats.mannwhitneyu(a, b, alternative="two-sided")
        print(f"    {na:<11} vs {nb:<11} p = {p:.4f}"
              f"  {'significant' if p < 0.05 else 'NOT significant'}")
    print("\n  Conclusion: sudden-onset versus protracted crisis is not significant")
    print("  either way. The intuitive story is not supported and is not claimed.")

    print("\n" + "=" * 72)
    print("TEST 4  The individual cases, stated plainly")
    print("=" * 72)
    for iso, nm in [("UKR", "Ukraine"), ("PSE", "Palestine"), ("SYR", "Syria"),
                    ("YEM", "Yemen"), ("HND", "Honduras")]:
        x = pr[pr.iso3 == iso]
        usd = ap[ap.iso3 == iso].usd.sum()
        yrs = ", ".join(f"{y}:{n}" for y, n in x.groupby("year").size().items())
        print(f"  {nm:<10} {len(x):>4} projects ever, {x.participations.sum():>7,} "
              f"participations, ${usd/1e9:5.1f}B appealed")
        print(f"             by year: {yrs if yrs else 'none'}")


if __name__ == "__main__":
    main()
