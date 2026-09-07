#!/usr/bin/env python3
"""Rebuild wordtangible/resources/concreteness_ratings.csv from source data.

Downloads the three source datasets (cached in data/raw/, which is
gitignored — the MRC database's terms are "for research purposes", so the
raw files are not committed) and writes a merged ratings CSV with one row
per word and one column per source:

    Word,Concreteness,Brysbaert,Muraki,Glasgow,MRC

- Brysbaert: raw Conc.M from Brysbaert et al. (2014), 1-5 scale.
- Glasgow:   raw CNC mean from the Glasgow Norms (Scott et al., 2019),
             1-7 scale, keyed by bare lowercase word. Where Glasgow rates
             both a bare word and disambiguated senses ("toast" alongside
             "toast (bread)"), the bare entry — Glasgow's own rating of
             the ambiguous string — wins; senses are averaged only for
             the rare base with no bare entry.
- MRC:       raw CNC from the MRC Psycholinguistic Database (Wilson,
             1988 machine-usable dictionary), 100-700 scale. First
             occurrence wins for words with several part-of-speech
             entries (their CNC values are identical in practice).
- Muraki:    raw Mean_C from Muraki et al. (2023), concreteness ratings
             for 62,889 multiword expressions (bigrams through long
             idioms, plus ~1,100 hyphenated single words), natively 1-5
             like Brysbaert — same lab lineage and method, but only ~10
             raters per expression vs Brysbaert's ~30. Rows with no
             rating (NA) are dropped.
- Concreteness: the package's default rating — a quality-ordered
             fallback. The raw Brysbaert value when the word is in
             Brysbaert (the largest, most recent source, whose 1-5 scale
             is the package's scale); otherwise Muraki (same scale and
             lineage, fewer raters); otherwise Glasgow, otherwise MRC,
             the latter two linearly rescaled to 1-5 and rounded to two
             decimals.
             Fallback is deliberate: the sources' normalized
             distributions have systematically different means (3.04 /
             3.38 / 3.25), so averaging them would inject a scale-mixing
             offset into multi-source words rather than reduce noise —
             each value returned is a real published rating instead.
             MRC comes last because its CNC field is itself an
             aggregation of 1960s-70s norms collected under an older
             definition of concreteness.

Usage:
    python scripts/build_ratings.py [--diff-against OLD_CSV]

--diff-against summarizes how the generated Concreteness column differs
from an existing merged CSV (e.g. the previous release's file) — useful
for changelog notes; it does not fail the build.
"""

import argparse
import csv
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
OUT_CSV = REPO_ROOT / "wordtangible" / "resources" / "concreteness_ratings.csv"

# The official hosts have moved or gone away over the years (the Ghent CRR
# lab link for Brysbaert and the UWA page for MRC both 404 as of 2026-09),
# so these point at stable, widely used mirrors; the Glasgow URL is the
# journal's own supplementary material.
SOURCES = {
    "brysbaert.txt": (
        "https://raw.githubusercontent.com/ArtsEngine/concreteness/master/"
        "Concreteness_ratings_Brysbaert_et_al_BRM.txt"
    ),
    "glasgow.csv": (
        "https://static-content.springer.com/esm/"
        "art%3A10.3758%2Fs13428-018-1099-3/MediaObjects/"
        "13428_2018_1099_MOESM2_ESM.csv"
    ),
    "mrc2.dct": (
        "https://raw.githubusercontent.com/samzhang111/"
        "mrc-psycholinguistics/master/mrc2.dct"
    ),
    # Muraki et al. (2023) multiword-expression concreteness ratings,
    # from the paper's OSF repository (osf.io/ksypa)
    "muraki_mwe.csv": "https://osf.io/download/he4dv/",
}


def download_sources() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url in SOURCES.items():
        dest = RAW_DIR / filename
        if dest.exists() and dest.stat().st_size > 100_000:
            print(f"  {filename}: cached")
            continue
        print(f"  {filename}: downloading {url}")
        with urllib.request.urlopen(url, timeout=300) as resp:
            data = resp.read()
        if len(data) < 100_000:
            raise RuntimeError(
                f"{url} returned only {len(data)} bytes; "
                "expected a full dataset (did the mirror move?)"
            )
        dest.write_bytes(data)


def parse_brysbaert() -> dict[str, float]:
    """Word (original casing) -> Conc.M on a 1-5 scale."""
    ratings = {}
    with open(RAW_DIR / "brysbaert.txt", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row["Word"]:
                ratings[row["Word"]] = float(row["Conc.M"])
    return ratings


def parse_glasgow() -> dict[str, float]:
    """Lowercase base word -> CNC (1-7).

    The bare entry wins when Glasgow rates one ("toast" alongside
    "toast (bread)"); sense entries are averaged only for bases with no
    bare entry.
    """
    bare: dict[str, float] = {}
    senses: dict[str, list[float]] = {}
    with open(RAW_DIR / "glasgow.csv", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        subheader = next(reader)
        cnc_col = header.index("CNC")
        assert subheader[cnc_col] == "M", "unexpected Glasgow CSV layout"
        for row in reader:
            if not row or not row[0]:
                continue
            value = float(row[cnc_col])
            if " (" in row[0]:
                base = row[0].split(" (")[0].strip().lower()
                senses.setdefault(base, []).append(value)
            else:
                bare[row[0].strip().lower()] = value
    for base, vals in senses.items():
        bare.setdefault(base, round(sum(vals) / len(vals), 3))
    return bare


def parse_muraki() -> dict[str, float]:
    """Expression (original casing) -> Mean_C on a 1-5 scale, 2 decimals."""
    ratings = {}
    with open(RAW_DIR / "muraki_mwe.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["Mean_C"] != "NA":
                ratings[row["Expression"]] = round(float(row["Mean_C"]), 2)
    return ratings


def parse_mrc() -> dict[str, int]:
    """Lowercase word -> CNC (100-700); 0 means unrated and is skipped.

    mrc2.dct is fixed-width: CNC occupies columns 29-31 (1-based), and the
    word starts at column 52, "|"-delimited from its phonetic transcriptions.
    """
    ratings: dict[str, int] = {}
    with open(RAW_DIR / "mrc2.dct", encoding="ascii") as f:
        for line in f:
            conc = int(line[28:31])
            if conc > 0:
                word = line[51:].split("|")[0].strip().lower()
                ratings.setdefault(word, conc)
    return ratings


def normalize_glasgow(conc: float) -> float:
    """Linearly rescale Glasgow's 1-7 CNC to the 1-5 scale."""
    return 1 + (conc - 1) * 4 / 6


def normalize_mrc(conc: int) -> float:
    """Linearly rescale MRC's 100-700 CNC to the 1-5 scale."""
    return 1 + (conc - 100) * 4 / 600


def build_rows(
    brysbaert: dict[str, float],
    glasgow: dict[str, float],
    mrc: dict[str, int],
    muraki: dict[str, float],
) -> list[dict[str, str]]:
    # Brysbaert (then Muraki) entries keep their original casing; everything
    # else is keyed lowercase. Join across sources case-insensitively.
    display = {expr.lower(): expr for expr in muraki}
    display.update({word.lower(): word for word in brysbaert})
    muraki_by_key = {expr.lower(): value for expr, value in muraki.items()}
    all_words = sorted(
        set(display) | set(glasgow) | set(mrc),
        key=lambda w: (display.get(w, w).lower(), display.get(w, w)),
    )

    rows = []
    for key in all_words:
        word = display.get(key, key)
        brys_val = brysbaert.get(word)
        muraki_val = muraki_by_key.get(key)
        glas_val = glasgow.get(key)
        mrc_val = mrc.get(key)

        # Quality-ordered fallback: Brysbaert > Muraki > Glasgow > MRC
        if brys_val is not None:
            default = brys_val
        elif muraki_val is not None:
            default = muraki_val
        elif glas_val is not None:
            default = round(normalize_glasgow(glas_val), 2)
        else:
            default = round(normalize_mrc(mrc_val), 2)

        rows.append(
            {
                "Word": word,
                "Concreteness": str(default),
                "Brysbaert": "" if brys_val is None else str(brys_val),
                "Muraki": "" if muraki_val is None else str(muraki_val),
                "Glasgow": "" if glas_val is None else str(glas_val),
                "MRC": "" if mrc_val is None else str(mrc_val),
            }
        )
    return rows


def diff_against(rows: list[dict[str, str]], old_csv: Path) -> None:
    old = {}
    with open(old_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["Concreteness"]:
                old[row["Word"]] = float(row["Concreteness"])

    new = {
        row["Word"]: float(row["Concreteness"])
        for row in rows
        if row["Concreteness"] != ""
    }

    added = sorted(new.keys() - old.keys())
    removed = sorted(old.keys() - new.keys())
    changed = sorted(
        (w, old[w], new[w])
        for w in old.keys() & new.keys()
        if abs(old[w] - new[w]) > 1e-9
    )
    big = [c for c in changed if abs(c[1] - c[2]) > 0.1]
    print(f"  vs {old_csv}:")
    print(f"    words added: {len(added)} (e.g. {', '.join(added[:5])})")
    print(f"    words removed: {len(removed)} (e.g. {', '.join(removed[:5])})")
    print(f"    values changed: {len(changed)}, of which >0.1: {len(big)}")
    for w, o, n in big[:10]:
        print(f"      {w}: {o} -> {n}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--diff-against",
        type=Path,
        metavar="OLD_CSV",
        help="summarize how the Concreteness column differs from this "
        "previously generated merged CSV (informational; never fails)",
    )
    args = parser.parse_args()

    print("Downloading sources...")
    download_sources()

    print("Parsing...")
    brysbaert = parse_brysbaert()
    glasgow = parse_glasgow()
    mrc = parse_mrc()
    muraki = parse_muraki()
    print(
        f"  brysbaert: {len(brysbaert)} words, "
        f"glasgow: {len(glasgow)} words, mrc: {len(mrc)} words, "
        f"muraki: {len(muraki)} expressions"
    )

    rows = build_rows(brysbaert, glasgow, mrc, muraki)
    if args.diff_against:
        diff_against(rows, args.diff_against)

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Word", "Concreteness", "Brysbaert", "Muraki", "Glasgow", "MRC"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT_CSV}")


if __name__ == "__main__":
    main()
