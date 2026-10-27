"""
build_search_index.py
---------------------
Builds a static person-search index for the map: the search/ folder,
one small JSON file per two-letter name prefix (search/sm.json, search/jo.json, ...).
Works on any static host (GitHub Pages, python -m http.server). No server needed.

Each person is filed under the first two letters of every part of their
first and last name, so "smith", "john" or "john smith" all find John Smith.

Usage:
    python build_search_index.py
"""

import csv, json, os, re, shutil, sys, time, unicodedata

INPUT  = "sunshine2025.csv"
COORDS = "employer_coords.json"
OUTDIR = "search"


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]+", " ", s)).strip()


def keys_for(first, last):
    toks = [t for t in norm(first + " " + last).split(" ") if len(t) >= 2]
    return {t[:2] for t in toks} or {"00"}


def badge_key(first, last, employer):
    """Must match norm() in build_history.py."""
    def norm(s):
        s = (s or "").lower().replace("\u2019", "'")
        s = re.sub(r"[^a-z0-9' ]+", " ", s)
        return re.sub(r"\s+", " ", s).strip()
    return norm(first) + "|" + norm(last) + "|" + norm(employer)


def load_badges(path="person_badges.json"):
    if not os.path.exists(path):
        print(f"  ! {path} not found — run build_history.py first to get badges. Continuing without.")
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    print(f"  Loaded badges for {len(data):,} people")
    return data


def money(s):
    try:
        return round(float(str(s).replace("$", "").replace(",", "").strip()), 2)
    except ValueError:
        return None


def main():
    with open(COORDS, encoding="utf-8") as f:
        mapped = {k for k, v in json.load(f).items() if v}
    badges = load_badges()

    with open(INPUT, "rb") as f:
        total = max(sum(1 for _ in f) - 1, 1)

    chunks = {}    # key -> {"e": [employers], "ei": {employer: idx}, "p": [rows]}
    count = skipped = 0
    start = time.time()

    with open(INPUT, newline="", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.DictReader(f), 1):
            if i % 20000 == 0 or i == total:
                pct = i / total
                bar = "█" * int(pct * 30) + "░" * (30 - int(pct * 30))
                sys.stdout.write(f"\r  {bar} {pct*100:5.1f}%  {i:,}/{total:,}")
                sys.stdout.flush()
            emp = row.get("Employer", "").strip()
            if emp not in mapped:
                skipped += 1
                continue
            fn = row.get("First Name", "").strip()
            ln = row.get("Last Name", "").strip()
            t  = row.get("Job Title", "").strip()
            s  = money(row.get("Salary", ""))
            b  = badges.get(badge_key(fn, ln, emp))
            for k in keys_for(fn, ln):
                c = chunks.setdefault(k, {"e": [], "ei": {}, "p": []})
                if emp not in c["ei"]:
                    c["ei"][emp] = len(c["e"])
                    c["e"].append(emp)
                rec = [fn, ln, t, c["ei"][emp], s]
                if b:
                    rec.append(b)
                c["p"].append(rec)
            count += 1

    if os.path.isdir(OUTDIR):
        shutil.rmtree(OUTDIR)
    os.makedirs(OUTDIR)
    size = 0
    for k, c in chunks.items():
        path = os.path.join(OUTDIR, k + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"e": c["e"], "p": c["p"]}, f, separators=(",", ":"), ensure_ascii=False)
        size += os.path.getsize(path)

    biggest = max(chunks, key=lambda k: len(chunks[k]["p"]))
    print(f"\n\nDone in {time.time()-start:.0f}s.")
    print(f"  People indexed:  {count:,}  (skipped {skipped:,} with no map location)")
    print(f"  Files:           {len(chunks)} in {OUTDIR}/  ({size/1024/1024:.0f} MB total)")
    print(f"  Largest file:    {biggest}.json  ({len(chunks[biggest]['p']):,} people)")


if __name__ == "__main__":
    main()
