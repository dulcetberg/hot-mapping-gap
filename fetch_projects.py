#!/usr/bin/env python3
"""
Pull every project from the HOT Tasking Manager, published and archived.

Paginates at the API's fixed 14 per page with a deliberate delay. HOT is a
nonprofit running this for free, so it identifies itself and does not hammer.
Caches to disk so it never needs running twice.
"""
import json, os, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://tasking-manager-tm4-production-api.hotosm.org/api/v2/projects/"
UA = "bergstromgis.com research (HOT volunteer, contact dulcetberg@gmail.com)"
DELAY = 0.35
KEEP = ("projectId", "name", "country", "campaigns", "percentMapped",
        "percentValidated", "status", "priority", "difficulty",
        "totalContributors", "activeMappers", "lastUpdated", "dueDate",
        "organisationName")


def page(status, n):
    url = API + "?" + urllib.parse.urlencode({"projectStatuses": status, "page": n})
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as exc:
            if attempt == 3:
                print(f"  page {n} failed: {str(exc)[:60]}", flush=True)
                return None
            time.sleep(2 * (attempt + 1))


def harvest(status):
    out, first = [], page(status, 1)
    if not first:
        return out
    pages = first["pagination"]["pages"]
    total = first["pagination"]["total"]
    print(f"{status}: {total:,} projects over {pages} pages", flush=True)
    out += [{k: p.get(k) for k in KEEP} for p in first["results"]]
    t0 = time.time()
    for n in range(2, pages + 1):
        time.sleep(DELAY)
        d = page(status, n)
        if d:
            out += [{k: p.get(k) for k in KEEP} for p in d["results"]]
        if n % 50 == 0 or n == pages:
            el = time.time() - t0
            print(f"  {n}/{pages} pages, {len(out):,} projects, "
                  f"{el/60:.1f} min elapsed, ~{(pages-n)*(el/max(n-1,1))/60:.1f} min left",
                  flush=True)
    return out


def main():
    all_p = []
    for s in ("PUBLISHED", "ARCHIVED"):
        all_p += harvest(s)
        json.dump(all_p, open(os.path.join(HERE, "data", "projects.json"), "w"))
    print(f"\nsaved {len(all_p):,} projects to projects.json", flush=True)


if __name__ == "__main__":
    main()
