import UnityPy
import json
import os
import sys

BASE = r"C:\Users\ocean\git\fd2\fd2re\FD2Re_Data\StreamingAssets\aa\StandaloneWindows64"
OUT = r"C:\Users\ocean\git\fd2\fd2re\strings_dump"
os.makedirs(OUT, exist_ok=True)

bundles = [
    "localization-string-tables-chinese(simplified)(zh)_assets_all.bundle",
    "localization-asset-tables-chinese(simplified)(zh)_assets_all.bundle",
    "localization-assets-chinese(simplified)(zh)_assets_all.bundle",
    "localization-assets-shared_assets_all.bundle",
    "localization-locales_assets_all.bundle",
]

summary = {}

for bname in bundles:
    bpath = os.path.join(BASE, bname)
    print(f"\n=== {bname} ===")
    env = UnityPy.load(bpath)
    entries = []
    for obj in env.objects:
        try:
            data = obj.read()
        except Exception as e:
            entries.append({"path_id": obj.path_id, "type": obj.type.name, "error": str(e)})
            continue
        info = {
            "path_id": obj.path_id,
            "type": obj.type.name,
            "name": getattr(data, "m_Name", getattr(data, "name", "")),
        }
        if obj.type.name == "MonoBehaviour":
            try:
                tree = obj.read_typetree()
                info["typetree_keys"] = list(tree.keys())
                info["typetree"] = tree
            except Exception as e:
                info["typetree_error"] = str(e)
        entries.append(info)
        print(f"  PathID={obj.path_id} Type={obj.type.name} Name={info['name']}")

    out_file = os.path.join(OUT, bname.replace(".bundle", ".json"))
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2, default=str)
    summary[bname] = len(entries)
    print(f"  -> wrote {out_file}")

print("\n=== SUMMARY ===")
for k, v in summary.items():
    print(f"  {k}: {v} objects")
