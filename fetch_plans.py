#!/usr/bin/env python3
"""
OCHA humanitarian response plans, 2014-2026, with their plan type.

Plan type matters for this analysis. OCHA distinguishes a Flash Appeal (sudden
onset, usually a natural disaster) from a Humanitarian Response Plan (a
protracted crisis) from a Regional Refugee Response Plan (money spent hosting
people who fled somewhere else). Those are different kinds of need, and only
some of them describe a place where a map of buildings and roads would help.
Lumping them together is what makes a dollar-per-map comparison misleading.
"""
import json, os, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "bergstromgis.com research (contact dulcetberg@gmail.com)"

out = []
for yr in range(2014, 2027):
    req = urllib.request.Request(f"https://api.hpc.tools/v1/public/plan/year/{yr}",
                                 headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.load(r)["data"]
    except Exception as e:
        print(f"  {yr}: FAILED {str(e)[:60]}", flush=True)
        continue
    n = 0
    for p in data:
        isos = sorted({l.get("iso3") for l in (p.get("locations") or []) if l.get("iso3")})
        if not isos:
            continue
        cats = p.get("categories") or []
        ptype = next((c.get("code") for c in cats if c.get("group") == "planType"), None)
        tname = next((c.get("name") for c in cats if c.get("group") == "planType"), None)
        out.append({
            "year": yr, "iso3": isos,
            "name": (p.get("planVersion") or {}).get("name"),
            "requirements": p.get("origRequirements"),
            "plan_type": ptype, "plan_type_name": tname,
        })
        n += 1
    print(f"  {yr}: {n} plans", flush=True)
    time.sleep(0.3)

json.dump(out, open(os.path.join(HERE, "data", "ocha_plans.json"), "w"))
import collections
print(f"\nsaved {len(out)} plans")
print("plan types:", dict(collections.Counter(p["plan_type"] for p in out).most_common()))
for code in sorted({p["plan_type"] for p in out if p["plan_type"]}):
    nm = next(p["plan_type_name"] for p in out if p["plan_type"] == code)
    print(f"  {code:<6} {nm}")
