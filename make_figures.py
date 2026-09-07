#!/usr/bin/env python3
"""Figures for the humanitarian mapping gap. Equal Earth throughout."""
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.colors import TwoSlopeNorm
from figures import world, choropleth, label, NEED, MAP, DIV, INK, PAPER, GREY, RULE
from analyze import projects, appeals

import os
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
FIGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")

pr = projects()
ap = appeals()
g = world()

need = ap.groupby("iso3").usd.sum().rename("appeal_usd")
eff = pr.groupby("iso3").participations.sum().rename("participations")

# ------------------------------------------------------------------ fig 1
# The gap itself: volunteer effort measured against the size of the appeal.
# Only countries that actually had an appeal are in the question at all.
# Appeals under $100M make the ratio meaningless: they are 0.13% of all appeal
# dollars but 12% of all mapping, so the denominator is near zero and the score
# explodes. Indonesia is the clearest case, a $50M appeal against 77,265
# participations, because middle-income countries handle their own disasters
# without asking the UN. Those countries are held out of the shading.
FLOOR = 1e8
d = pd.concat([need, eff], axis=1)
d = d[d.appeal_usd >= FLOOR].copy()
d["participations"] = d.participations.fillna(0)
d["per_bn"] = d.participations / (d.appeal_usd / 1e9)
d["score"] = np.log10(d.per_bn.clip(lower=1))
mid = d.score.median()

gg = g.merge(d[["score", "per_bn", "appeal_usd", "participations"]],
             left_on="iso3", right_index=True, how="left")
has = gg[gg.score.notna()]
non = gg[gg.score.isna()]

fig, ax = plt.subplots(figsize=(10.6, 5.95))
norm = TwoSlopeNorm(vmin=d.score.min(), vcenter=mid, vmax=d.score.max())
non.plot(ax=ax, color=GREY, edgecolor=PAPER, linewidth=0.3)
has.plot(ax=ax, color=[DIV(norm(s)) for s in has.score],
         edgecolor=PAPER, linewidth=0.35)
ax.set_axis_off()
# title and subtitle live in figure coordinates: the map axes has a large,
# projection-dependent top margin, so set_title padding cannot be trusted
# to clear the subtitle
fig.text(0.022, 0.965, "Volunteer mapping does not follow the size of the emergency",
         fontsize=21, fontweight="600", color=INK, va="top")
fig.text(0.022, 0.918,
         "The 89 countries whose UN appeals since 2014 total $100 million or more, shaded by "
         "how much volunteer\nmapping each drew per billion dollars requested.",
         fontsize=13, color="#5c5750", va="top", linespacing=1.5)

cax = ax.inset_axes([0.03, 0.135, 0.27, 0.036])
sm = plt.cm.ScalarMappable(cmap=DIV, norm=norm); sm.set_array([])
cb = plt.colorbar(sm, cax=cax, orientation="horizontal")
cb.set_ticks([d.score.min(), mid, d.score.max()])
cb.set_ticklabels(["least mapped", "median", "most mapped"])
cb.ax.tick_params(labelsize=11, length=0)
cb.outline.set_visible(False)
ax.text(0.03, 0.175, "mapping per $1B appealed", transform=ax.transAxes,
        fontsize=11.5, color="#5c5750")
ax.text(0.03, 0.028, "grey: no UN appeal, or one too small to compare",
        transform=ax.transAxes, fontsize=11, color="#8a857d")

# offsets in projected metres, to pull apart labels that sit on top of
# each other at this scale (Sudan against Yemen, Syria against Jordan)
NUDGE = {"SYR": (-2.6e5, 3.4e5), "JOR": (3.0e5, -2.2e5),
         "SDN": (-3.4e5, 1.0e5), "YEM": (5.2e5, -3.4e5),
         "KEN": (4.4e5, -1.0e5), "NGA": (-2.0e5, 0)}
for iso, t in [("SYR", "Syria"), ("YEM", "Yemen"), ("UKR", "Ukraine"),
               ("JOR", "Jordan"), ("AFG", "Afghanistan"), ("SDN", "Sudan"),
               ("COL", "Colombia"), ("MOZ", "Mozambique"), ("KEN", "Kenya"),
               ("NGA", "Nigeria")]:
    dx, dy = NUDGE.get(iso, (0, 0))
    label(ax, g, iso, t, dx=dx, dy=dy, size=11.5)

fig.text(0.5, 0.02,
         "Sources: UN OCHA Humanitarian Programme Cycle; HOT Tasking Manager. "
         "Equal Earth projection.  bergstromgis.com",
         ha="center", fontsize=10.5, color="#6b665e")
fig.subplots_adjust(top=0.845, bottom=0.07, left=0.02, right=0.98)
fig.savefig(os.path.join(FIGS, "fig1-gap-map.jpg"), dpi=155)
plt.close(fig)
print("fig1 done")

# ------------------------------------------------------------------ fig 2
# Mapping does track the size of the appeal, but only up to a point. Below $1B
# the relationship is real and positive; above it, among the largest emergencies
# in the world, it disappears entirely. The figure has to show both regimes or
# it misstates the finding.
from scipy import stats

OFF = {"SYR": (9, 4), "YEM": (9, -16), "UKR": (-35, -13), "PSE": (9, 4),
       "AFG": (12, -18), "IRQ": (-33, -14), "SDN": (7, 9), "SOM": (-37, 4),
       "LBN": (-37, -13), "JOR": (10, -6), "ETH": (10, 8), "COD": (9, 5),
       "HND": (9, 1), "NPL": (7, -18), "PHL": (1, 10), "MOZ": (10, -5),
       "COL": (-37, 6)}

s = d.copy()
s["y"] = s.participations.clip(lower=1.0)
lo = s[s.appeal_usd < 1e9]
hi = s[s.appeal_usd >= 1e9]
r_lo, p_lo = stats.pearsonr(np.log10(lo.appeal_usd), np.log10(lo.y))
r_hi, p_hi = stats.pearsonr(np.log10(hi.appeal_usd), np.log10(hi.y))

fig, ax = plt.subplots(figsize=(9.6, 6.4))
ax.axvspan(1.0, 60, color="#f0e7e0", alpha=0.55, zorder=0)
ax.scatter(lo.appeal_usd / 1e9, lo.y, s=58, c="#7aa8c4", edgecolor=PAPER,
           linewidth=0.7, zorder=3, label="appeal under $1B")
ax.scatter(hi.appeal_usd / 1e9, hi.y, s=96, c="#b03a1a", edgecolor=PAPER,
           linewidth=0.8, zorder=4, label="appeal of $1B or more")

# fitted trend within each regime, drawn only across that regime's own range
for sub, col, ls in ((lo, "#2b6489", "-"), (hi, "#8c2d10", "-")):
    lx, ly = np.log10(sub.appeal_usd / 1e9), np.log10(sub.y)
    m, c0 = np.polyfit(lx, ly, 1)
    xs = np.linspace(lx.min(), lx.max(), 40)
    ax.plot(10 ** xs, 10 ** (m * xs + c0), ls, color=col, linewidth=2.2,
            zorder=5, alpha=0.9)

for iso in ("SYR", "YEM", "UKR", "PSE", "JOR", "AFG", "COD", "SDN", "SOM",
            "HND", "NPL", "PHL", "MOZ", "COL", "IRQ", "LBN", "ETH"):
    if iso in s.index:
        r = s.loc[iso]
        ax.annotate(iso, (r.appeal_usd / 1e9, r.y), fontsize=11.5,
                    xytext=OFF.get(iso, (8, 5)), textcoords="offset points",
                    color="#3f3a34", fontweight="700", zorder=6,
                    path_effects=[pe.withStroke(linewidth=3.2, foreground=PAPER)])

ax.set_xscale("log"); ax.set_yscale("log")
ax.set_ylim(0.6, 2.4e5)
ax.set_xlabel("UN appeal requirements, 2014 to 2026 (US$ billions, log scale)", fontsize=13)
ax.set_ylabel("HOT project participations (log scale)", fontsize=13)
ax.tick_params(labelsize=11.5)
ax.grid(alpha=0.22, linewidth=0.6, color=RULE)
ax.set_axisbelow(True)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)

ax.text(0.055, 0.055, f"under $1B\nr = {r_lo:+.2f}, p = {p_lo:.3f}",
        transform=ax.transAxes, fontsize=12, color="#2b6489", fontweight="600",
        linespacing=1.5)
ax.text(0.80, 0.055, f"$1B and over\nr = {r_hi:+.2f}, p = {p_hi:.2f}",
        transform=ax.transAxes, fontsize=12, color="#8c2d10", fontweight="600",
        linespacing=1.5)
ax.legend(frameon=False, fontsize=12, loc="lower left",
          bbox_to_anchor=(0.30, -0.012))

fig.text(0.012, 0.972, "Mapping tracks the emergency, until the emergency gets big",
         fontsize=19.5, fontweight="600", color=INK, va="top")
fig.text(0.012, 0.925,
         "Each dot is a country with a UN humanitarian appeal since 2014. Below $1 billion, bigger "
         "appeals draw more volunteer\nmapping. Among the 36 largest emergencies, shaded, that "
         "relationship disappears.",
         fontsize=12.5, color="#5c5750", va="top", linespacing=1.5)
fig.subplots_adjust(top=0.845, bottom=0.085, left=0.075, right=0.985)
fig.savefig(os.path.join(FIGS, "fig2-scatter.jpg"), dpi=155)
plt.close(fig)
print(f"fig2 done  (lo r={r_lo:+.3f} p={p_lo:.2g}, hi r={r_hi:+.3f} p={p_hi:.2g})")

# ------------------------------------------------------------------ fig 3
# OCHA's own label for each appeal, used as the test of whether the kind of
# crisis predicts the mapping response better than the size of it.
GROUP = {"FA": "Sudden-onset disaster\n(flash appeal)",
         "HRP": "Protracted crisis\n(response plan)",
         "HNRP": "Protracted crisis\n(response plan)",
         "SRP": "Protracted crisis\n(response plan)",
         "REG": "People who fled\n(regional refugee plan)"}
plans = json.load(open(os.path.join(DATA, "ocha_plans.json")))
rows = []
for p in plans:
    grp = GROUP.get(p.get("plan_type"))
    if not grp:
        continue
    share = (p.get("requirements") or 0) / len(p["iso3"])
    for i in p["iso3"]:
        rows.append({"iso3": i, "year": p["year"], "usd": share, "grp": grp})
pt = pd.DataFrame(rows)
peff = pr.groupby(["iso3", "year"]).agg(part=("participations", "sum"),
                                        proj=("pid", "size")).reset_index()
pt = pt.merge(peff, on=["iso3", "year"], how="left")
pt[["part", "proj"]] = pt[["part", "proj"]].fillna(0)
pt = pt[pt.usd > 1e8]                      # same floor as the map

agg = pt.groupby("grp").apply(
    lambda d: pd.Series({"per_bn": d.part.sum() / (d.usd.sum() / 1e9),
                         "share": (d.proj > 0).mean(), "n": len(d)}),
    include_groups=False).sort_values("per_bn")

fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.3))
cols = ["#b03a1a", "#c98a5e", "#2b6489"]
for ax, col, ttl, f in [
        (axes[0], "per_bn", "Mapping drawn per $1B appealed", lambda v: f"{v:,.0f}"),
        (axes[1], "share", "Share of appeals drawing any mapping", lambda v: f"{v:.0%}")]:
    ax.barh(range(len(agg)), agg[col], color=cols, height=0.62)
    ax.set_yticks(range(len(agg)))
    ax.set_yticklabels(agg.index, fontsize=12, linespacing=1.4)
    ax.set_title(ttl, loc="left", fontsize=14, fontweight="600", pad=10)
    for i, v in enumerate(agg[col]):
        ax.text(v, i, "  " + f(v), va="center", fontsize=12.5, color="#4a453e", fontweight="600")
    ax.set_xticks([])
    for sp in ("top", "right", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color(RULE)
    ax.set_xlim(0, agg[col].max() * 1.24)
axes[1].set_yticklabels([])
fig.suptitle("The kind of crisis predicts the response better than its size",
             x=0.012, y=0.985, ha="left", fontsize=18.5, fontweight="600", color=INK)
fig.text(0.012, 0.895,
         f"Country-years with a UN appeal over $100 million, 2014 to 2026 (n = {int(agg.n.sum())}).",
         fontsize=12, color="#5c5750", va="top")
fig.subplots_adjust(top=0.665, bottom=0.06, left=0.20, right=0.985, wspace=0.08)
fig.savefig(os.path.join(FIGS, "fig3-plantype.jpg"), dpi=155)
plt.close(fig)
print("fig3 done")
print(agg.to_string())
