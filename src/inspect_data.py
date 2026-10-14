from collections import Counter
from pathlib import Path

RAW = Path("data/raw")
files = [p for p in RAW.rglob("*") if p.is_file()]
print(f"{len(files)} files under {RAW}")
print("by extension:", dict(Counter(p.suffix.lower() for p in files)))
for p in sorted(files):
    print(f"  {p.relative_to(RAW)}   {p.stat().st_size / 1e6:.2f} MB")

for p in sorted(files):
    if p.name.lower().startswith("readme"):
        print("\n=== README:", p.name)
        print(p.read_text(errors="ignore"))

for ext, n in [(".pos", 14), (".kml", 18)]:
    hits = sorted(p for p in files if p.suffix.lower() == ext)
    if hits:
        print(f"\n=== first {n} lines of {hits[0].name}")
        print("\n".join(hits[0].read_text(errors="ignore").splitlines()[:n]))