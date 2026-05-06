import UnityPy
import os
import json

BASE = r"C:\Users\ocean\git\fd2\fd2re\FD2Re_Data\StreamingAssets\aa\StandaloneWindows64"
OUT = r"C:\Users\ocean\git\fd2\fd2re\extracted"
os.makedirs(OUT, exist_ok=True)

bundles = {
    "stringtables": "localization-string-tables-chinese(simplified)(zh)_assets_all.bundle",
    "assets": "localization-assets-chinese(simplified)(zh)_assets_all.bundle",
    "shared": "localization-assets-shared_assets_all.bundle",
    "assettables": "localization-asset-tables-chinese(simplified)(zh)_assets_all.bundle",
}

# 1. Dump TextAssets (the dialogue scenarios)
print("=== TextAssets (B001/B002/B003/S001) ===")
env = UnityPy.load(os.path.join(BASE, bundles["assets"]))
for obj in env.objects:
    if obj.type.name == "TextAsset":
        data = obj.read()
        name = data.m_Name
        # m_Script can be bytes or str
        script = data.m_Script
        if isinstance(script, str):
            content = script
        else:
            try:
                content = script.decode("utf-8")
            except:
                content = script.decode("utf-8", errors="replace")
        out = os.path.join(OUT, f"{name}.xml")
        with open(out, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  {name}: {len(content)} chars -> {out}")

# 2. Dump StringTables (typetree)
print("\n=== StringTables ===")
env = UnityPy.load(os.path.join(BASE, bundles["stringtables"]))
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        try:
            tree = obj.read_typetree()
        except Exception as e:
            print(f"  PathID={obj.path_id} typetree fail: {e}")
            continue
        name = tree.get("m_Name", f"path{obj.path_id}")
        out = os.path.join(OUT, f"{name}.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(tree, f, ensure_ascii=False, indent=2, default=str)
        # show entry count if visible
        entries = None
        for k in ("m_TableData", "m_Entries", "TableData"):
            if k in tree:
                entries = tree[k]
                break
        n = len(entries) if isinstance(entries, list) else "?"
        print(f"  {name}: {n} entries -> {out}")

# 3. Dump Shared (key definitions)
print("\n=== Shared (key definitions) ===")
env = UnityPy.load(os.path.join(BASE, bundles["shared"]))
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        try:
            tree = obj.read_typetree()
        except Exception as e:
            continue
        name = tree.get("m_Name", f"path{obj.path_id}")
        out = os.path.join(OUT, f"shared_{name}.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(tree, f, ensure_ascii=False, indent=2, default=str)
        print(f"  {name} -> {out}")
