#!/usr/bin/env python3
"""
Where humanitarian mapping happens, against where humanitarian need is.

Two sources, joined on country:
  HOT Tasking Manager  - every public volunteer mapping project, 2013 to 2026
  OCHA HPC             - every UN humanitarian response plan, 2014 to 2026

Volunteer attention is finite. This asks where it landed, and how closely that
tracks the places the humanitarian system itself says are in crisis.

Counting note: totalContributors is recorded per project, so a volunteer who
maps five projects is counted five times. The honest unit is a project
participation, not a person, and it is called that throughout.
"""
import json, collections
import numpy as np
import pandas as pd
from crosswalk import build, to_iso3
from dates import estimate

import os
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

G, LUT = build()


def projects(path=None):
    path = path or os.path.join(DATA, "projects.json")
    rows = []
    for p in json.load(open(path)):
        cs = p.get("country") or []
        if not cs:
            continue
        iso = to_iso3(cs[0], LUT)
        if not iso:
            continue
        camps = [c["name"] for c in (p.get("campaigns") or [])]
        rows.append({
            "pid": p["projectId"], "iso3": iso, "country": cs[0],
            "participations": p.get("totalContributors") or 0,
            "mapped": p.get("percentMapped"),
            "validated": p.get("percentValidated"),
            "urgent": p.get("priority") == "URGENT",
            "status": p.get("status"),
            "org": p.get("organisationName"),
            "campaign": camps[0] if camps else None,
        })
    df = pd.DataFrame(rows)
    df["created"] = pd.to_datetime(estimate(df.pid.tolist()), utc=True)
    df["year"] = df.created.dt.year
    return df


def appeals(path=None):
    path = path or os.path.join(DATA, "ocha_plans.json")
    """Regional plans are split evenly across member countries."""
    rows = []
    for p in json.load(open(path)):
        share = (p.get("requirements") or 0) / len(p["iso3"])
        for i in p["iso3"]:
            rows.append({"iso3": i, "year": p["year"], "usd": share})
    return pd.DataFrame(rows)


def main():
    pr = projects()
    ap = appeals()
    pr.to_csv(os.path.join(DATA, "projects_dated.csv"), index=False)

    print(f"HOT: {len(pr):,} projects, {pr.iso3.nunique()} countries, "
          f"{pr.year.min()}-{pr.year.max()}, "
          f"{pr.participations.sum():,} project participations")
    print(f"OCHA: {len(ap):,} country-plan rows, {ap.iso3.nunique()} countries, "
          f"${ap.usd.sum()/1e9:.0f}B requested\n")

    # ---- country level -------------------------------------------------
    hot = pr.groupby("iso3").agg(
        projects=("pid", "size"), participations=("participations", "sum"),
        mapped=("mapped", "mean"), first_year=("year", "min"),
        name=("country", "first")).reset_index()
    apc = ap.groupby("iso3").agg(
        appeal_usd=("usd", "sum"), appeal_years=("year", "nunique")).reset_index()
    df = hot.merge(apc, on="iso3", how="outer")
    for c in ("projects", "participations", "appeal_usd", "appeal_years"):
        df[c] = df[c].fillna(0)
    df["appealed"] = df.appeal_years > 0
    df["any_mapping"] = df.projects > 0
    df.to_csv(os.path.join(DATA, "country_join.csv"), index=False)

    tot = df.participations.sum()
    print("=" * 72)
    print("1. HOW CONCENTRATED IS VOLUNTEER MAPPING?")
    print("=" * 72)
    s = df.sort_values("participations", ascending=False)
    for n in (5, 10, 20, 50):
        print(f"  top {n:>2} countries hold {s.head(n).participations.sum()/tot:6.1%} "
              f"of all project participations")
    print(f"\n  countries with any HOT project: {df.any_mapping.sum()}")
    print(f"  countries with an OCHA appeal:  {df.appealed.sum()}")

    print("\n" + "=" * 72)
    print("2. DID APPEAL COUNTRIES GET MAPPED AT ALL?")
    print("=" * 72)
    a = df[df.appealed]
    none = a[~a.any_mapping].sort_values("appeal_usd", ascending=False)
    print(f"  {len(none)} of {len(a)} appeal countries have zero HOT projects")
    print(f"  they account for ${none.appeal_usd.sum()/1e9:.1f}B of appeals\n")
    for _, r in none.head(15).iterrows():
        print(f"    {r.iso3}  ${r.appeal_usd/1e9:6.2f}B  {r.appeal_years:>2.0f} appeal-years")

    print("\n" + "=" * 72)
    print("3. THE COUNTRY-YEAR TEST: WAS THERE MAPPING DURING THE APPEAL?")
    print("=" * 72)
    have = set(map(tuple, pr[["iso3", "year"]].drop_duplicates().values))
    ap["mapped_that_year"] = [(i, y) in have for i, y in zip(ap.iso3, ap.year)]
    cov = ap.groupby("year").mapped_that_year.agg(["mean", "size"])
    print("  share of active appeal country-years with any HOT mapping:")
    for y, r in cov.iterrows():
        bar = "#" * int(r["mean"] * 40)
        print(f"    {y}  {r['mean']:5.1%}  ({r['size']:>3} appeals)  {bar}")
    print(f"\n  overall {ap.mapped_that_year.mean():.1%} of "
          f"{len(ap)} appeal country-years saw any mapping")

    print("\n" + "=" * 72)
    print("4. WHERE THE EFFORT ACTUALLY WENT")
    print("=" * 72)
    for _, r in s.head(20).iterrows():
        tag = f"${r.appeal_usd/1e9:5.1f}B appeal" if r.appealed else "  no appeal  "
        print(f"    {r.iso3} {tag} {r.participations:8,.0f} part. "
              f"{r.projects:5.0f} proj  {str(r['name'])[:22]}")
    print(f"\n  {df[~df.appealed].participations.sum()/tot:.1%} of all effort went to "
          f"countries that never had an OCHA appeal")

    print("\n" + "=" * 72)
    print("5. EFFORT PER $B OF APPEAL, AMONG COUNTRIES ASKING FOR >$1B")
    print("=" * 72)
    big = a[a.appeal_usd > 1e9].copy()
    big["per_bn"] = big.participations / (big.appeal_usd / 1e9)
    big = big.sort_values("per_bn")
    print("  least mapped for what they asked:")
    for _, r in big.head(12).iterrows():
        print(f"    {r.iso3} ${r.appeal_usd/1e9:6.1f}B {r.participations:8,.0f} part. "
              f"{r.per_bn:7.0f}/$B  {str(r['name'])[:20]}")
    print("\n  most mapped for what they asked:")
    for _, r in big.tail(8).iloc[::-1].iterrows():
        print(f"    {r.iso3} ${r.appeal_usd/1e9:6.1f}B {r.participations:8,.0f} part. "
              f"{r.per_bn:7.0f}/$B  {str(r['name'])[:20]}")

    print("\n" + "=" * 72)
    print("6. GROWTH OF THE TASKING MANAGER")
    print("=" * 72)
    g = pr.groupby("year").agg(projects=("pid", "size"),
                               participations=("participations", "sum"),
                               countries=("iso3", "nunique"))
    for y, r in g.iterrows():
        print(f"    {y}  {r.projects:>5,} projects  {r.participations:>9,} part.  "
              f"{r.countries:>3} countries")
    return df, pr, ap


if __name__ == "__main__":
    main()
