"""
build_history.py
----------------
Reads every sunshineYYYY.csv in this folder and builds:

  history.json        (published) per-employer headcount/avg salary by year,
                      leaderboards, inflation-indexed threshold, badge stats
  person_badges.json  (local only) badges per person, read by
                      build_map_data.py and build_search_index.py

Badges (current year, people matched by name + employer):
  1  highest paid at their employer       T  top 1% province-wide
  I  above $100k in 1996 dollars          U  salary paid up 20%+ vs last year
  N  not on last year's list here         V  on every list since the first year
  B  $10k+ taxable benefits               A  acting/interim title at $180k+

Run this FIRST, then build_map_data.py, then build_search_index.py.

Usage:
    python build_history.py
"""

import csv, glob, io, json, os, re, sys, time, urllib.request, zipfile

OUTPUT          = "history.json"
BADGES_OUT      = "person_badges.json"
CPI_CACHE       = "cpi_ontario.json"
CPI_URL         = "https://www150.statcan.gc.ca/n1/tbl/csv/18100005-eng.zip"
THRESHOLD       = 100_000
THRESHOLD_YEAR  = 1996      # year the $100k threshold was set in law
TOP_N           = 50
JUMP_PCT        = 20        # "U" badge: salary paid up at least this much
PERKS_MIN       = 10_000    # "B" badge: taxable benefits at least this much
INTERIM_MIN     = 180_000   # "A" badge salary floor
MIN_MATCH_RATE  = 0.30      # below this, assume the employer was renamed and skip N/U


# ── helpers ──────────────────────────────────────────────────────────────────
def norm(s):
    s = (s or "").lower().replace("’", "'")
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def money(s):
    try:
        return round(float(str(s).replace("$", "").replace(",", "").strip()), 2)
    except ValueError:
        return None


FIELD_ALIASES = {
    "sector": "sector", "lastname": "last", "firstname": "first",
    "salary": "salary", "salarypaid": "salary",
    "benefits": "benefits", "taxablebenefits": "benefits",
    "employer": "employer", "jobtitle": "title",
}


def field_map(header):
    out = {}
    for i, h in enumerate(header):
        key = re.sub(r"[^a-z]", "", h.lower())
        if key in FIELD_ALIASES:
            out[FIELD_ALIASES[key]] = i
    missing = {"last", "first", "salary", "employer", "title"} - set(out)
    if missing:
        sys.exit(f"  ✗ Could not find columns {missing} in header {header}")
    return out


def progress(label, n, total, start):
    pct = n / total if total else 1
    bar = "█" * int(pct * 30) + "░" * (30 - int(pct * 30))
    rate = n / max(time.time() - start, 0.01)
    sys.stdout.write(f"\r  {label} {bar} {pct*100:5.1f}%  {n:,}/{total:,}  ({rate:,.0f} rows/s)")
    sys.stdout.flush()


def count_lines(path):
    with open(path, "rb") as f:
        return max(sum(1 for _ in f) - 1, 1)


# ── CPI ──────────────────────────────────────────────────────────────────────
def load_cpi():
    """Ontario all-items CPI annual averages {year: value}. Cached after first download."""
    if os.path.exists(CPI_CACHE):
        with open(CPI_CACHE, encoding="utf-8") as f:
            data = {int(k): v for k, v in json.load(f).items()}
        print(f"CPI: loaded {len(data)} years from {CPI_CACHE}")
        return data

    print("CPI: downloading Statistics Canada table 18-10-0005-01 ...")
    try:
        req = urllib.request.Request(CPI_URL, headers={"User-Agent": "SunshineListMap/1.0"})
        raw = urllib.request.urlopen(req, timeout=120).read()
    except Exception as e:
        print(f"  ✗ CPI download failed ({e}). Inflation features will be skipped.")
        print(f"    Fix: check your connection and re-run, or delete {CPI_CACHE} if it is stale.")
        return None

    z = zipfile.ZipFile(io.BytesIO(raw))
    name = next(n for n in z.namelist() if n.endswith(".csv") and "MetaData" not in n)
    data = {}
    with z.open(name) as f:
        reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
        prod_col = next(c for c in reader.fieldnames if c.lower().startswith("products"))
        for row in reader:
            if row["GEO"] == "Ontario" and row[prod_col] == "All-items" and row["VALUE"]:
                data[int(row["REF_DATE"][:4])] = float(row["VALUE"])

    if THRESHOLD_YEAR not in data:
        print(f"  ✗ No Ontario CPI for {THRESHOLD_YEAR} in table. Inflation features skipped.")
        return None

    with open(CPI_CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print(f"  ✓ Ontario CPI {min(data)}–{max(data)} saved to {CPI_CACHE}")
    return data


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    files = {}
    for p in glob.glob("sunshine*.csv"):
        m = re.search(r"(\d{4})", os.path.basename(p))
        if m:
            files[int(m.group(1))] = p
    if len(files) < 2:
        sys.exit("Need at least two sunshineYYYY.csv files in this folder.")

    years = sorted(files)
    first_y, prev_y, cur_y = years[0], years[-2], years[-1]
    print(f"Years found: {', '.join(map(str, years))}")

    cpi = load_cpi()
    thresholds = {}
    if cpi:
        base = cpi[THRESHOLD_YEAR]
        for y in years:
            if y in cpi:
                thresholds[y] = round(THRESHOLD * cpi[y] / base)
        missing = [y for y in years if y not in thresholds]
        if missing:
            print(f"  ! No CPI yet for {missing} — inflation shown only for years that have it.")

    emp_stats   = {}   # norm employer -> {year: [count, payroll]}
    emp_display = {}   # norm employer -> current-year display name
    totals      = {}
    people      = {first_y: {}, prev_y: {}, cur_y: {}}   # person key -> salary
    presence    = {}   # person key -> number of years on the list
    bad         = set()  # person keys that are ambiguous in any year
    cur_info    = {}   # person key -> (first, last, title, employer, benefits)
    adj_by_emp  = {}

    for y in years:
        path = files[y]
        total_rows = count_lines(path)
        start = time.time()
        seen = set()
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            fm = field_map(next(reader))
            count = payroll = above = 0
            thr = thresholds.get(y)
            for i, row in enumerate(reader, 1):
                if i % 20000 == 0:
                    progress(str(y), i, total_rows, start)
                if len(row) <= max(fm.values()):
                    continue
                sal = money(row[fm["salary"]])
                if sal is None:
                    continue
                emp_raw = row[fm["employer"]].strip()
                ek = norm(emp_raw)
                stats = emp_stats.setdefault(ek, {}).setdefault(y, [0, 0.0])
                stats[0] += 1
                stats[1] += sal
                count += 1
                payroll += sal
                if thr and sal >= thr:
                    above += 1

                pk = norm(row[fm["first"]]) + "|" + norm(row[fm["last"]]) + "|" + ek
                if pk in seen:
                    bad.add(pk)
                else:
                    seen.add(pk)
                    presence[pk] = presence.get(pk, 0) + 1
                if y in people:
                    people[y][pk] = sal

                if y == cur_y:
                    emp_display[ek] = emp_raw
                    if thr and sal >= thr:
                        adj_by_emp[ek] = adj_by_emp.get(ek, 0) + 1
                    ben = money(row[fm["benefits"]]) if "benefits" in fm else None
                    if ben is not None and ben == float(cur_y):   # known data-entry glitch
                        ben = None
                    cur_info[pk] = (row[fm["first"]].strip(), row[fm["last"]].strip(),
                                    row[fm["title"]].strip(), emp_raw, ben)
        progress(str(y), total_rows, total_rows, start)
        print(f"\n   ✓ {count:,} people, ${payroll/1e9:,.2f}B paid")
        totals[y] = {"count": count, "payroll": round(payroll)}
        if thr:
            totals[y]["above_adj"] = above

    # ── person matching ──────────────────────────────────────────────────────
    print("Matching people across years ...")

    def changes(old_year):
        rows = []
        for pk, s_now in people[cur_y].items():
            if pk in bad or pk not in people[old_year]:
                continue
            s_old = people[old_year][pk]
            fn, ln, t, e, _ = cur_info[pk]
            rows.append({"fn": fn, "ln": ln, "t": t, "e": e, "p": s_old, "s": s_now,
                         "d": round(s_now - s_old, 2), "pc": round((s_now / s_old - 1) * 100, 1)})
        return rows

    recent = changes(prev_y)
    span   = changes(first_y)

    # Per employer: share of this year's people who were also here last year.
    # A very low share usually means the employer was renamed, so N/U badges would be wrong.
    cur_count, matched_prev, new_by_emp = {}, {}, {}
    for pk in people[cur_y]:
        ek = pk.rsplit("|", 1)[1]
        cur_count[ek] = cur_count.get(ek, 0) + 1
        if pk in people[prev_y]:
            matched_prev[ek] = matched_prev.get(ek, 0) + 1
        else:
            new_by_emp[ek] = new_by_emp.get(ek, 0) + 1
    reliable = {ek for ek, n in cur_count.items() if matched_prev.get(ek, 0) / n >= MIN_MATCH_RATE}

    print(f"  ✓ {len(recent):,} matched {prev_y}→{cur_y}, {len(span):,} matched {first_y}→{cur_y}, "
          f"{len(bad):,} ambiguous names skipped, "
          f"{len(cur_count) - len(reliable):,} employers look renamed (no New/Up badges)")

    # ── badges ───────────────────────────────────────────────────────────────
    print("Assigning badges ...")
    cur_sal = sorted(people[cur_y].values())
    top1_cut = cur_sal[int(len(cur_sal) * 0.99)] if cur_sal else None
    emp_max = {}
    for pk, s in people[cur_y].items():
        ek = pk.rsplit("|", 1)[1]
        if s > emp_max.get(ek, 0):
            emp_max[ek] = s
    thr_cur = thresholds.get(cur_y)
    interim_rx = re.compile(r"\b(acting|interim)\b", re.I)

    person_badges = {}
    badge_counts = {k: 0 for k in "1TIUNVBA"}
    for pk, s in people[cur_y].items():
        if pk in bad:
            continue
        ek = pk.rsplit("|", 1)[1]
        _, _, title, _, ben = cur_info[pk]
        b = []
        if s >= emp_max[ek] and cur_count[ek] >= 3:
            b.append("1")
        if top1_cut and s >= top1_cut:
            b.append("T")
        if thr_cur and s >= thr_cur:
            b.append("I")
        if ek in reliable:
            prev = people[prev_y].get(pk)
            if prev is None:
                b.append("N")
            elif prev > 0:
                pct = round((s / prev - 1) * 100)
                if pct >= JUMP_PCT:
                    b.append(f"U{pct}")
        if presence.get(pk) == len(years):
            b.append("V")
        if ben and ben >= PERKS_MIN:
            b.append(f"B{round(ben / 1000)}")
        if s >= INTERIM_MIN and interim_rx.search(title):
            b.append("A")
        if b:
            person_badges[pk] = ",".join(b)
            for code in b:
                badge_counts[code[0]] += 1

    with open(BADGES_OUT, "w", encoding="utf-8") as f:
        json.dump(person_badges, f, separators=(",", ":"), ensure_ascii=False)

    # ── output ───────────────────────────────────────────────────────────────
    employers = {}
    for ek, disp in emp_display.items():
        s = emp_stats[ek]
        employers[disp] = {
            "c": [s[y][0] if y in s else 0 for y in years],
            "a": [round(s[y][1] / s[y][0]) if y in s else None for y in years],
            "n": new_by_emp.get(ek, 0) if ek in reliable else 0,
        }
        if thresholds.get(cur_y):
            employers[disp]["adj"] = adj_by_emp.get(ek, 0)

    out = {
        "years": years,
        "current_year": cur_y,
        "previous_year": prev_y,
        "first_year": first_y,
        "inflation": None if not thresholds else {
            "base_year": THRESHOLD_YEAR,
            "source": "Statistics Canada table 18-10-0005-01, Ontario all-items CPI (annual average)",
            "thresholds": {str(y): v for y, v in thresholds.items()},
        },
        "badges": {
            "top1_cut": top1_cut,
            "jump_pct": JUMP_PCT,
            "perks_min": PERKS_MIN,
            "interim_min": INTERIM_MIN,
            "counts": badge_counts,
        },
        "totals": {str(y): v for y, v in totals.items()},
        "employers": employers,
        "leaders": {
            "change_dollar": sorted(recent, key=lambda r: -r["d"])[:TOP_N],
            "change_pct":    sorted(recent, key=lambda r: -r["pc"])[:TOP_N],
            "gain_span":     sorted(span,   key=lambda r: -r["d"])[:TOP_N],
        },
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"), ensure_ascii=False)

    print(f"\nDone → {OUTPUT} ({os.path.getsize(OUTPUT)/1024:,.0f} KB), "
          f"{BADGES_OUT} ({os.path.getsize(BADGES_OUT)/1024/1024:,.1f} MB, local only)")
    print("  Badges: " + ", ".join(f"{k}={v:,}" for k, v in badge_counts.items()))
    if thr_cur:
        a = totals[cur_y]["above_adj"]
        c = totals[cur_y]["count"]
        print(f"  $100k in {THRESHOLD_YEAR} dollars = ${thr_cur:,} in {cur_y}. "
              f"{a:,} of {c:,} ({a/c*100:.0f}%) would still be on the list.")
    print("\nNext: python build_map_data.py, then python build_search_index.py")


if __name__ == "__main__":
    main()
