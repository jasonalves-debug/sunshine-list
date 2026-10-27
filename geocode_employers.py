"""
geocode_employers.py  (v2 — city fallback)
-------------------------------------------
Pass 1: tries full employer name as before.
Pass 2: for failures, extracts a city hint from the employer string
        and geocodes to that city in Ontario.

Run with --resume to skip already-geocoded employers.

Requirements:
    pip install requests

Usage:
    python geocode_employers.py --input sunshine2025.csv --output employer_coords.json --resume
"""

import csv
import json
import time
import re
import argparse
import sys

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "SunshineListMapApp/1.0 (jason@youremail.com)"}  # ← keep your real email
DELAY = 1.1

# Ontario cities / regions to scan for in employer names
ONTARIO_CITIES = [
    "Toronto", "Ottawa", "Mississauga", "Brampton", "Hamilton", "London",
    "Markham", "Vaughan", "Kitchener", "Windsor", "Richmond Hill", "Oakville",
    "Burlington", "Greater Sudbury", "Sudbury", "Oshawa", "Barrie", "St. Catharines",
    "Cambridge", "Kingston", "Whitby", "Guelph", "Thunder Bay", "Waterloo",
    "Brantford", "Pickering", "Niagara Falls", "Peterborough", "Sault Ste. Marie",
    "Kawartha Lakes", "Sarnia", "Norfolk", "Welland", "North Bay", "Belleville",
    "Chatham", "Timmins", "Cornwall", "Ajax", "Halton Hills", "Newmarket",
    "Georgina", "Aurora", "Orangeville", "Orillia", "Cobourg", "Woodstock",
    "Stratford", "Bowmanville", "Innisfil", "Collingwood", "Midland", "Owen Sound",
    "Brockville", "Pembroke", "Kenora", "Elliot Lake", "Temiskaming", "Haliburton",
    "Parry Sound", "Bancroft", "Huntsville", "Gravenhurst", "Bracebridge",
    "Dryden", "Fort Frances", "Kapuskasing", "Kirkland Lake", "Cochrane",
    "Renfrew", "Perth", "Carleton Place", "Kanata", "Nepean", "Gloucester",
    "Scarborough", "North York", "Etobicoke", "York", "East York",
    "Halton", "Durham", "York Region", "Peel", "Simcoe",
    "Muskoka", "Haldimand", "Lambton", "Huron", "Bruce", "Grey",
    "Dufferin", "Wellington", "Northumberland", "Hastings", "Prince Edward",
    "Lennox", "Frontenac", "Leeds", "Lanark", "Nipissing",
    "Timiskaming", "Algoma", "Rainy River", "Manitoulin",
]

# Sort longest first so "St. Catharines" matches before "Catharines"
ONTARIO_CITIES.sort(key=len, reverse=True)


def extract_city(employer: str) -> str | None:
    """Try to find an Ontario city name inside the employer string."""
    for city in ONTARIO_CITIES:
        if re.search(re.escape(city), employer, re.IGNORECASE):
            return city
    # Last resort: look for "Of <Word>" patterns
    m = re.search(r'\bOf\s+([A-Z][a-zA-Z\s\-]+?)(?:,|\s+And|\s+Area|$)', employer)
    if m:
        candidate = m.group(1).strip()
        if len(candidate) > 3:
            return candidate
    return None


def geocode_query(query: str) -> dict | None:
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1, "countrycodes": "ca"},
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
        if results:
            r = results[0]
            return {
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
                "display_name": r.get("display_name", ""),
                "query_used": query,
            }
    except Exception as e:
        print(f"  ⚠ Error: {e}", file=sys.stderr)
    return None


def geocode(employer: str) -> dict | None:
    """Pass 1: try full name variations."""
    attempts = [
        f"{employer}, Ontario, Canada",
        f"{employer}, Canada",
        employer,
    ]
    for query in attempts:
        result = geocode_query(query)
        time.sleep(DELAY)
        if result:
            return result
    return None


def geocode_city_fallback(employer: str) -> dict | None:
    """Pass 2: extract city from name, geocode that."""
    city = extract_city(employer)
    if not city:
        return None
    query = f"{city}, Ontario, Canada"
    result = geocode_query(query)
    time.sleep(DELAY)
    if result:
        result["query_used"] = f"[CITY FALLBACK] {query}"
        result["city_fallback"] = True
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="sunshine2025.csv")
    parser.add_argument("--output", default="employer_coords.json")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--fallback-only", action="store_true",
                        help="Only re-process failed (None) entries — skip already geocoded")
    args = parser.parse_args()

    # Load existing
    existing = {}
    if args.resume or args.fallback_only:
        try:
            with open(args.output, "r", encoding="utf-8") as f:
                existing = json.load(f)
            already = sum(1 for v in existing.values() if v is not None)
            failed_count = sum(1 for v in existing.values() if v is None)
            print(f"Loaded {len(existing)} employers — {already} geocoded, {failed_count} failed.")
        except FileNotFoundError:
            print("No existing file found, starting fresh.")

    # Extract unique employers
    print(f"Reading {args.input} ...")
    employers = set()
    with open(args.input, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=",")
        for row in reader:
            emp = row.get("Employer", "").strip()
            if emp:
                employers.add(emp)

    employers = sorted(employers)
    print(f"Found {len(employers)} unique employers.")

    results = dict(existing)
    geocoded = 0
    fallback_hit = 0
    failed = 0
    skipped = 0

    for i, employer in enumerate(employers, 1):
        # Skip if already successfully geocoded
        if employer in results and results[employer] is not None:
            skipped += 1
            continue

        print(f"[{i}/{len(employers)}] {employer}")

        coord = None

        # Pass 1 — skip if fallback-only mode
        if not args.fallback_only:
            coord = geocode(employer)
            if coord:
                results[employer] = coord
                geocoded += 1
                print(f"  ✓ {coord['lat']:.4f}, {coord['lon']:.4f}")

        # Pass 2 — city fallback
        if not coord:
            coord = geocode_city_fallback(employer)
            if coord:
                results[employer] = coord
                fallback_hit += 1
                print(f"  ~ {coord['query_used']} → {coord['lat']:.4f}, {coord['lon']:.4f}")
            else:
                results[employer] = None
                failed += 1
                print(f"  ✗ Not found")

        if (i % 10) == 0:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nDone.")
    print(f"  Geocoded (exact):   {geocoded}")
    print(f"  Geocoded (city ~):  {fallback_hit}")
    print(f"  Skipped (cached):   {skipped}")
    print(f"  Failed:             {failed}")
    print(f"  Output: {args.output}")


if __name__ == "__main__":
    main()
