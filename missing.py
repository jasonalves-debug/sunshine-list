import csv, json

coords = json.load(open('employer_coords.json', encoding='utf-8'))
missing = {k for k, v in coords.items() if v is None}

counts = {}
with open('sunshine2025.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        e = row['Employer'].strip()
        if e in missing:
            counts[e] = counts.get(e, 0) + 1

top = sorted(counts.items(), key=lambda x: -x[1])[:30]
total_missing = sum(counts.values())
print(f"Total employees at missing employers: {total_missing}\n")
for name, n in top:
    print(f"{n:5}  {name}")
