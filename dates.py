#!/usr/bin/env python3
"""
Give every HOT project a creation date.

The Tasking Manager only returns creation dates from its per-project endpoint,
at roughly 90KB a call. Fetching 14,702 of those would pull well over a
gigabyte off a nonprofit's API to read one field, so instead this leans on the
fact that project IDs are handed out sequentially: sample real dates across the
ID range, confirm the relationship never goes backwards, and interpolate.

calibrate() writes the sample. estimate() reads it back and dates everything.
Anything derived this way is an estimate and is labelled as one.
"""
import json, os, time, urllib.request
from datetime import datetime, timezone
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://tasking-manager-tm4-production-api.hotosm.org/api/v2/projects/{}/?abbreviated=true"
UA = "bergstromgis.com research (HOT volunteer, contact dulcetberg@gmail.com)"
CAL = os.path.join(HERE, "data", "id_date_calibration.json")


def _ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=timezone.utc).timestamp()


def fetch_created(pid):
    req = urllib.request.Request(API.format(pid), headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r).get("created")
        except Exception:
            if attempt == 2:
                return None
            time.sleep(2)


def calibrate(ids, n=220, delay=0.35):
    """Sample n ids spread evenly across the range and fetch their real dates."""
    ids = sorted(set(ids))
    have = {}
    if os.path.exists(CAL):
        have = {int(k): v for k, v in json.load(open(CAL))}
    step = max(len(ids) // n, 1)
    want = sorted(set(ids[::step] + ids[:1] + ids[-1:]) - set(have))
    print(f"calibrating: {len(have)} cached, fetching {len(want)} more")
    for i, pid in enumerate(want):
        c = fetch_created(pid)
        if c:
            have[pid] = c
        if i and i % 25 == 0:
            print(f"  {i}/{len(want)}", flush=True)
        time.sleep(delay)
    pairs = sorted(have.items())
    json.dump(pairs, open(CAL, "w"))
    bad = sum(1 for a, b in zip(pairs, pairs[1:]) if _ts(b[1]) < _ts(a[1]))
    print(f"{len(pairs)} calibration points, {bad} monotonic violations")
    return pairs, bad


def estimate(pids):
    """Interpolate creation timestamps for any list of project ids."""
    pairs = sorted((int(k), v) for k, v in json.load(open(CAL)))
    xs = np.array([p for p, _ in pairs], float)
    ys = np.array([_ts(d) for _, d in pairs], float)
    ys = np.maximum.accumulate(ys)          # enforce monotonic, tiny nudges only
    est = np.interp(np.asarray(pids, float), xs, ys)
    return [datetime.fromtimestamp(t, timezone.utc) for t in est]


def accuracy(k=40, delay=0.35):
    """Hold out real dates the interpolation never saw and measure the error."""
    pairs = sorted((int(a), b) for a, b in json.load(open(CAL)))
    lo, hi = pairs[0][0], pairs[-1][0]
    known = {p for p, _ in pairs}
    rng = np.random.default_rng(11)
    test = []
    while len(test) < k:
        c = int(rng.integers(lo, hi))
        if c not in known:
            test.append(c)
    errs = []
    for pid in test:
        real = fetch_created(pid)
        time.sleep(delay)
        if not real:
            continue
        pred = estimate([pid])[0].timestamp()
        errs.append(abs(pred - _ts(real)) / 86400.0)
    errs = np.array(errs)
    print(f"\nheld-out accuracy on {len(errs)} projects the fit never saw:")
    print(f"  median error {np.median(errs):.1f} days, "
          f"90th pct {np.percentile(errs,90):.1f} days, max {errs.max():.1f} days")
    return errs
