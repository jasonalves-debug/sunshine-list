"""
build_map_data.py  (v2 — employer aggregation)
------------------------------------------------
One GeoJSON feature per employer location.
Each feature contains:
  - employee_count
  - avg_salary
  - max_salary
  - sector
  - top50 / bottom50: earners [{first_name, last_name, job_title, salary, benefits, b}]
    where b = badge codes from person_badges.json (run build_history.py first)

Usage:
    python build_map_data.py --input sunshine2025.csv --coords employer_coords.json --output sunshine_map.json
"""

import csv
import json
import os
import re
import argparse
from collections import defaultdict


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


def clean_salary(val):
    try:
        return round(float(val.replace(",", "").strip()), 2)
    except:
        return None


def clean_benefits(val):
    try:
        f = float(val.replace(",", "").strip())
        return None if f == 2025.0 else round(f, 2)
    except:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="sunshine2025.csv")
    parser.add_argument("--coords", default="employer_coords.json")
    parser.add_argument("--output", default="sunshine_map.json")
    args = parser.parse_args()

    print(f"Loading coords...")
    with open(args.coords, encoding="utf-8") as f:
        coords = json.load(f)

    badges = load_badges()

    print(f"Reading {args.input}...")
    employers = defaultdict(lambda: {"employees": [], "sector": ""})

    with open(args.input, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=",")
        for row in reader:
            emp = row.get("Employer", "").strip()
            if not emp or not coords.get(emp):
                continue
            salary = clean_salary(row.get("Salary", ""))
            employers[emp]["sector"] = row.get("Sector", "").strip()
            fn = row.get("First Name", "").strip()
            ln = row.get("Last Name", "").strip()
            person = {
                "first_name": fn,
                "last_name":  ln,
                "job_title":  row.get("Job Title", "").strip(),
                "salary":     salary,
                "benefits":   clean_benefits(row.get("Benefits", "")),
            }
            b = badges.get(badge_key(fn, ln, emp))
            if b:
                person["b"] = b
            employers[emp]["employees"].append(person)

    print(f"Building GeoJSON for {len(employers)} employer locations...")
    features = []

    for employer, data in employers.items():
        coord = coords[employer]
        employees = data["employees"]
        salaries = [e["salary"] for e in employees if e["salary"]]

        avg_salary = round(sum(salaries) / len(salaries), 2) if salaries else None
        max_salary = max(salaries) if salaries else None

        sorted_employees = sorted(
            [e for e in employees if e["salary"]],
            key=lambda x: x["salary"],
            reverse=True
        )

        top50    = sorted_employees[:50]
        bottom50 = sorted_employees[-50:] if len(sorted_employees) > 50 else []

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [coord["lon"], coord["lat"]],
            },
            "properties": {
                "employer":       employer,
                "sector":         data["sector"],
                "employee_count": len(employees),
                "avg_salary":     avg_salary,
                "max_salary":     max_salary,
                "min_salary":     min(salaries) if salaries else None,
                "city_fallback":  coord.get("city_fallback", False),
                "top50":          json.dumps(top50),
                "bottom50":       json.dumps(bottom50),
            }
        })

    geojson = {
        "type": "FeatureCollection",
        "metadata": {
            "total_employers": len(features),
            "year": 2025,
        },
        "features": features,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(geojson, f, separators=(",", ":"), ensure_ascii=False)

    print(f"\nDone.")
    print(f"  Employer locations: {len(features)}")
    print(f"  Output: {args.output}")


if __name__ == "__main__":
    main()
