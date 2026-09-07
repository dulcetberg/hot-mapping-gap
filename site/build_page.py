#!/usr/bin/env python3
"""
Build the case study page by patching the previous one, the same way
chicago-heat-1995 was built from chicago-crime-gwr. Keeps the nav, sidebar,
footer and scripts identical to the rest of the site without copying brand.css
out of the portfolio repo.
"""
h = open("_template.html").read()

TITLE = "Where Humanitarian Mapping Happens"
DESC = ("Joining 14,510 volunteer mapping projects against every UN humanitarian appeal since 2014 "
        "shows that volunteer mapping tracks the size of an emergency only up to a point. Among the "
        "36 largest crises, the relationship disappears.")
SLUG = "hot-mapping-gap"
REPO = "https://github.com/dulcetberg/hot-mapping-gap"

OLD_TITLE = "Chicago's Heat Wave, 30 Years On"
OLD_DESC = ("Thirty years after the 1995 Chicago heat wave killed more than 700 people, satellite "
            "thermal imagery and 1995 business records show the neighborhoods that suffered most "
            "were not the hottest by day, but the ones that stayed hot at night and had lost their "
            "gathering places.")

# --- head metadata -----------------------------------------------------------
h = h.replace(f"{OLD_TITLE} &mdash; Brian Bergstrom", f"{TITLE} &mdash; Brian Bergstrom")
h = h.replace(f"{OLD_TITLE} — Brian Bergstrom", f"{TITLE} — Brian Bergstrom")
h = h.replace("https://bergstromgis.com/work/chicago-heat-1995.html",
              f"https://bergstromgis.com/work/{SLUG}.html")
h = h.replace(OLD_DESC, DESC)

# --- project header ----------------------------------------------------------
i = h.index('<header class="project-header">')
j = h.index('</header>', i) + len('</header>')
h = h[:i] + f'''<header class="project-header">
      <span class="tag tag-civic">Humanitarian &mdash; Independent Study</span>
      <h1>{TITLE}</h1>
      <p class="subtitle">I started mapping for the Humanitarian OpenStreetMap Team about 2 months
      ago, mostly in Syria, and wanted to know what I had joined. Joining every project in the
      Tasking Manager against every UN humanitarian appeal shows that volunteer mapping follows the
      size of an emergency up to a point, and then stops.</p>
      <div class="meta-row">
        <span class="stat">14,510 mapping projects, 160 countries, 2013&ndash;2026</span>
        <span class="stat">532 UN appeals worth $400 billion</span>
        <span class="stat">1,405,270 project participations</span>
      </div>
    </header>''' + h[j:]

# --- hero image --------------------------------------------------------------
i = h.index('<div class="project-hero-media">')
j = h.index('<div class="project-body">')
h = h[:i] + f'''<div class="project-hero-media">
    <div class="media-inner">
      <img src="../images/{SLUG}.jpg" alt="World map on the Equal Earth projection showing countries with UN humanitarian appeals shaded by how much volunteer mapping they drew per billion dollars requested. Ukraine, eastern Europe, Syria, Jordan, Afghanistan and Yemen are the least mapped.">
    </div>
  </div>

  ''' + h[j:]

# --- body --------------------------------------------------------------------
BODY = open("body.html").read()
i = h.index('<div class="project-body">')
j = h.index('<div class="evidence-panel">')
h = h[:i] + BODY + "\n    " + h[j:]

# --- evidence panel ----------------------------------------------------------
i = h.index('<div class="evidence-panel">')
j = h.index('</div>', h.index('</a>', h.index('github.com'))) + len('</div>')
h = h[:i] + f'''<div class="evidence-panel">
      <p>The harvest, the statistics including the hypothesis that failed, and the figure code are
      all in the repository.</p>
      <a class="btn btn-primary" href="{REPO}" target="_blank" rel="noopener">
        View the code <span class="visually-hidden">(opens in a new tab)</span>
      </a>
      <a class="btn btn-outline" href="https://tasks.hotosm.org/" target="_blank" rel="noopener">
        HOT Tasking Manager <span class="visually-hidden">(opens in a new tab)</span>
      </a>
    </div>''' + h[j:]

open(f"{SLUG}.html", "w").write(h)
print("wrote", SLUG + ".html", len(h), "chars")
print("em-dashes literal:", h.count("—"), " &mdash; entities:", h.count("&mdash;"))
print("stale references:", h.count("chicago-heat"), h.count("Heat Wave"))
