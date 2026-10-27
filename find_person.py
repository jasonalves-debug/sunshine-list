import csv, sys

query = " ".join(sys.argv[1:]).strip().lower()
if not query:
    print("Usage: python find_person.py <name>")
    print("Example: python find_person.py smith john")
    sys.exit(1)

found = 0
with open('sunshine2025.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        first = row.get('First Name','').strip().lower()
        last  = row.get('Last Name','').strip().lower()
        full  = f"{first} {last}"
        if query in full or query in first or query in last:
            print(f"{row['First Name']} {row['Last Name']}  |  {row['Job Title']}  |  {row['Employer']}  |  ${row['Salary']}")
            found += 1

print(f"\n{found} result(s) found in CSV.")
