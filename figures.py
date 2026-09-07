#!/usr/bin/env python3
"""
Maps and charts for the humanitarian mapping gap.

Everything is drawn on Equal Earth (EPSG:8857). A map about where humanitarian
need is concentrated should not use a projection that inflates the rich
northern latitudes and shrinks the tropics, which is most of the subject.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
import matplotlib.patheffects as pe
import numpy as np
import geopandas as gpd

import os
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

INK   = "#1a1a1a"
PAPER = "#faf8f5"
GREY  = "#e4e0d9"      # countries with no data at all
RULE  = "#c8c2b8"

# warm = humanitarian need, cool = volunteer mapping effort
NEED = LinearSegmentedColormap.from_list("need", ["#fdeee4", "#f6b98d", "#e3743c", "#b03a1a", "#6d1b0a"])
MAP  = LinearSegmentedColormap.from_list("map",  ["#e8eef2", "#a9c6d6", "#5b93b5", "#2b6489", "#123a56"])
DIV  = LinearSegmentedColormap.from_list("div",  ["#8c2d10", "#d98356", "#f2ece4", "#7aa8c4", "#1d4e70"])

plt.rcParams.update({
    "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "axes.edgecolor": RULE, "text.color": INK,
    "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
    "figure.facecolor": PAPER, "axes.facecolor": PAPER, "savefig.facecolor": PAPER,
})


def world(ne_path=None):
    ne_path = ne_path or os.path.join(DATA, "ne50.geojson")
    g = gpd.read_file(ne_path)
    g = g[(g.NAME != "Antarctica") & (g.geometry.notna())].copy()
    g["iso3"] = g["ISO_A3_EH"].where(g["ISO_A3_EH"].str.len() == 3, g["ADM0_A3"])
    return g.to_crs("EPSG:8857")


def choropleth(ax, g, col, cmap, title, sub, log=True, fmt=None):
    """Countries with no value are drawn grey, not white, so absence reads as a value."""
    has = g[g[col].notna() & (g[col] > 0)]
    non = g[~g.index.isin(has.index)]
    v = has[col].astype(float)
    vals = np.log10(v) if log else v
    norm = Normalize(vals.min(), vals.max())

    non.plot(ax=ax, color=GREY, edgecolor=PAPER, linewidth=0.3)
    has.plot(ax=ax, color=[cmap(norm(x)) for x in vals], edgecolor=PAPER, linewidth=0.3)
    ax.set_axis_off()
    ax.set_title(title, loc="left", fontsize=20, fontweight="600", pad=6)
    ax.text(0, 1.005, sub, transform=ax.transAxes, fontsize=13,
            color="#5c5750", va="bottom", ha="left")

    # colourbar drawn inside the empty Pacific, where the map has nothing to say
    cax = ax.inset_axes([0.02, 0.06, 0.20, 0.028])
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm); sm.set_array([])
    cb = plt.colorbar(sm, cax=cax, orientation="horizontal")
    lo, hi = v.min(), v.max()
    cb.set_ticks([norm(vals.min()), norm(vals.max())] if not log else [vals.min(), vals.max()])
    f = fmt or (lambda x: f"{x:,.0f}")
    cb.set_ticklabels([f(lo), f(hi)])
    cb.ax.tick_params(labelsize=11, length=0)
    cb.outline.set_visible(False)
    return ax


def label(ax, g, iso, text, dx=0, dy=0, size=11.5):
    row = g[g.iso3 == iso]
    if row.empty:
        return
    c = row.geometry.iloc[0].representative_point()
    ax.annotate(text, (c.x + dx, c.y + dy), fontsize=size, ha="center",
                color=INK, fontweight="600",
                path_effects=[pe.withStroke(linewidth=3.4, foreground=PAPER)])
