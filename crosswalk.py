#!/usr/bin/env python3
"""
HOT records country as a free-text name, OCHA records it as an ISO3 code.
Nothing joins until those agree, so this builds a name -> ISO3 lookup out of
every name field Natural Earth carries, then adds the HOT spellings that
Natural Earth has never heard of.
"""
import re, unicodedata
import geopandas as gpd

import os
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

NAME_FIELDS = ("NAME", "NAME_LONG", "BRK_NAME", "NAME_SORT", "NAME_CIAWF",
               "ADMIN", "FORMAL_EN", "GEOUNIT", "SUBUNIT")

# HOT spellings, historical names and disputed-territory labels that no
# Natural Earth name field matches. Hand-checked one at a time.
MANUAL = {
    "dem rep congo": "COD", "democratic republic of the congo": "COD",
    "dr congo": "COD", "congo kinshasa": "COD", "congo brazzaville": "COG",
    "rep congo": "COG", "republic of congo": "COG",
    "cote divoire": "CIV", "ivory coast": "CIV",
    "cabo verde": "CPV", "cape verde": "CPV",
    "swaziland": "SWZ", "eswatini": "SWZ",
    "burma": "MMR", "myanmar burma": "MMR",
    "east timor": "TLS", "timor leste": "TLS",
    "macedonia": "MKD", "north macedonia": "MKD",
    "czech republic": "CZE", "czechia": "CZE",
    "palestine": "PSE", "palestinian territory": "PSE",
    "west bank": "PSE", "gaza": "PSE", "west bank and gaza": "PSE",
    "occupied palestinian territory": "PSE",
    "syria": "SYR", "syrian arab republic": "SYR",
    "laos": "LAO", "lao pdr": "LAO",
    "vietnam": "VNM", "viet nam": "VNM",
    "south korea": "KOR", "north korea": "PRK",
    "korea dem peoples rep": "PRK", "dem peoples rep korea": "PRK",
    "russia": "RUS", "russian federation": "RUS",
    "iran": "IRN", "iran islamic rep": "IRN",
    "tanzania": "TZA", "united rep of tanzania": "TZA",
    "moldova": "MDA", "rep of moldova": "MDA",
    "bolivia": "BOL", "venezuela": "VEN",
    "brunei": "BRN", "bosnia and herz": "BIH", "bosnia herzegovina": "BIH",
    "central african rep": "CAF", "dominican rep": "DOM",
    "eq guinea": "GNQ", "equatorial guinea": "GNQ",
    "s sudan": "SSD", "south sudan": "SSD",
    "solomon is": "SLB", "solomon islands": "SLB",
    "st vincent and the grenadines": "VCT",
    "st vincent grenadines": "VCT", "saint vincent and the grenadines": "VCT",
    "st lucia": "LCA", "saint lucia": "LCA",
    "st kitts and nevis": "KNA", "saint kitts and nevis": "KNA",
    "antigua and barb": "ATG", "antigua and barbuda": "ATG",
    "trinidad and tobago": "TTO", "turks and caicos is": "TCA",
    "british virgin is": "VGB", "us virgin is": "VIR",
    "sint maarten": "SXM", "st martin": "MAF", "st barthelemy": "BLM",
    "curacao": "CUW", "aruba": "ABW", "anguilla": "AIA",
    "bahamas the": "BHS", "the bahamas": "BHS", "gambia the": "GMB",
    "united states": "USA", "united states of america": "USA",
    "usa": "USA", "united kingdom": "GBR", "uk": "GBR",
    "turkey": "TUR", "turkiye": "TUR",
    "kyrgyzstan": "KGZ", "kyrgyz republic": "KGZ",
    "somaliland": "SOM",   # HOT maps it; OCHA counts it inside Somalia
    "kosovo": "XKX", "n cyprus": "CYP", "northern cyprus": "CYP",
    "w sahara": "ESH", "western sahara": "ESH",
    "sao tome and principe": "STP", "micronesia": "FSM",
    "marshall is": "MHL", "marshall islands": "MHL",
    "cayman is": "CYM", "faeroe is": "FRO", "fr polynesia": "PYF",
    "new caledonia": "NCL", "papua new guinea": "PNG",
    "s geo and the is": "SGS", "hong kong": "HKG", "macao": "MAC",
    "united arab emirates": "ARE", "uae": "ARE",
    "french guiana": "GUF",
    "netherlands antilles": "CUW",   # dissolved 2010; HOT holds one legacy project
}


def norm(s):
    """Fold case, accents and punctuation so 'Côte d'Ivoire' == 'cote divoire'."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def build(ne_path=None):
    ne_path = ne_path or os.path.join(DATA, "ne50.geojson")
    g = gpd.read_file(ne_path)
    # ISO_A3 is -99 for France, Norway and others; ISO_A3_EH fixes those
    g["iso3"] = g["ISO_A3_EH"].where(g["ISO_A3_EH"].str.len() == 3, g["ADM0_A3"])
    lut = {}
    for _, row in g.iterrows():
        for f in NAME_FIELDS:
            n = norm(row.get(f))
            if n and n not in lut:
                lut[n] = row["iso3"]
    lut.update(MANUAL)      # hand entries win over anything inferred
    return g, lut


def to_iso3(name, lut):
    return lut.get(norm(name))


if __name__ == "__main__":
    import json, collections
    g, lut = build()
    print(f"lookup holds {len(lut):,} name spellings for {g['iso3'].nunique()} countries\n")

    projects = json.load(open("projects.json"))
    names = collections.Counter(
        c for p in projects for c in (p.get("country") or []))
    miss = {n: k for n, k in names.items() if not to_iso3(n, lut)}
    print(f"HOT uses {len(names)} distinct country names, "
          f"{len(names)-len(miss)} resolve, {len(miss)} do not")
    if miss:
        print("\nunresolved:")
        for n, k in sorted(miss.items(), key=lambda x: -x[1]):
            print(f"  {k:>5} projects  {n!r}")
