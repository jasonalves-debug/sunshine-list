import csv, glob, os

files = sorted(glob.glob("*.csv"))
if not files:
    print("No CSV files found in this folder.")

for path in files:
    print("=" * 70)
    print(f"FILE: {path}  ({os.path.getsize(path)/1024/1024:.1f} MB)")
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with open(path, newline="", encoding=enc) as f:
                reader = csv.reader(f)
                header = next(reader)
                first = next(reader, [])
                rows = 1 + sum(1 for _ in reader)
            print(f"  encoding: {enc}")
            print(f"  rows:     {rows:,}")
            print(f"  headers:  {header}")
            print(f"  first:    {first}")
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"  ERROR ({enc}): {e}")
            break
print("=" * 70)
