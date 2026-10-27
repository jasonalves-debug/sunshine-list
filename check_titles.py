import json

with open('sunshine_map.json', encoding='utf-8') as f:
    data = json.load(f)

# Collect all titles from top50 across health/hospital sector
hospital_titles = set()
school_titles = set()
university_titles = set()
college_titles = set()
govt_titles = set()
police_titles = set()

for f in data['features']:
    sector = (f['properties'].get('sector') or '').lower()
    top50 = json.loads(f['properties'].get('top50') or '[]')
    
    for e in top50:
        t = (e.get('job_title') or '').strip()
        if not t: continue
        tl = t.lower()
        
        if 'hospital' in sector or 'health' in sector:
            if any(w in tl for w in ['president', 'chief executive', 'ceo']):
                hospital_titles.add(t)
        
        if 'school' in sector or 'district' in sector:
            if 'director' in tl and 'education' in tl:
                school_titles.add(t)
        
        if 'universit' in sector:
            if 'president' in tl or 'chancellor' in tl:
                university_titles.add(t)
        
        if 'college' in sector:
            if 'president' in tl and 'vice' not in tl:
                college_titles.add(t)
        
        if 'government' in sector or 'ontario public' in sector:
            if 'deputy minister' in tl:
                govt_titles.add(t)
        
        if 'police' in tl or 'chief' in tl:
            if 'police' in (f['properties'].get('employer') or '').lower() or 'police' in sector:
                police_titles.add(t)

print("=== HOSPITAL CEO/PRESIDENT TITLES ===")
for t in sorted(hospital_titles)[:30]: print(f"  {t}")

print("\n=== SCHOOL DIRECTOR TITLES ===")
for t in sorted(school_titles)[:20]: print(f"  {t}")

print("\n=== UNIVERSITY PRESIDENT TITLES ===")
for t in sorted(university_titles)[:20]: print(f"  {t}")

print("\n=== COLLEGE PRESIDENT TITLES ===")
for t in sorted(college_titles)[:20]: print(f"  {t}")

print("\n=== DEPUTY MINISTER TITLES ===")
for t in sorted(govt_titles)[:20]: print(f"  {t}")

print("\n=== POLICE CHIEF TITLES ===")
for t in sorted(police_titles)[:20]: print(f"  {t}")
