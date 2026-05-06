"""
Scan resources.assets and sharedassets*.assets for embedded Chinese strings
(typically TextMeshPro / UGUI text component values stored in MonoBehaviours).
"""
import UnityPy
import os
import re
import json
import glob

DATA = r"C:\Users\ocean\git\fd2\fd2re\FD2Re_Data"
OUT = r"C:\Users\ocean\git\fd2\fd2re\assets_strings.json"

asset_files = sorted(glob.glob(os.path.join(DATA, "resources.assets"))) + \
              sorted(glob.glob(os.path.join(DATA, "sharedassets*.assets"))) + \
              sorted(glob.glob(os.path.join(DATA, "level*")))

CN_RE = re.compile(r"[一-鿿]")

def has_cn(s):
    return bool(CN_RE.search(s))

found = {}  # string -> [source files]

for af in asset_files:
    try:
        env = UnityPy.load(af)
    except Exception as e:
        print(f"skip {af}: {e}")
        continue
    base = os.path.basename(af)
    count = 0
    for obj in env.objects:
        if obj.type.name not in ("MonoBehaviour", "TextAsset", "GameObject"):
            continue
        try:
            if obj.type.name == "TextAsset":
                d = obj.read()
                txt = d.m_Script if isinstance(d.m_Script, str) else d.m_Script.decode("utf-8", errors="ignore")
                # Look for chinese substrings
                for m in re.findall(r"[一-鿿][一-鿿　-〿＀-￯\w\s\.,\?!:;\-]{0,200}", txt):
                    s = m.strip()
                    if len(s) >= 2 and has_cn(s):
                        found.setdefault(s, set()).add(base)
                        count += 1
            else:
                # Try typetree
                tree = obj.read_typetree()
                # Walk recursively for string values containing Chinese
                stack = [tree]
                while stack:
                    cur = stack.pop()
                    if isinstance(cur, dict):
                        for k, v in cur.items():
                            stack.append(v)
                    elif isinstance(cur, list):
                        stack.extend(cur)
                    elif isinstance(cur, str):
                        if has_cn(cur):
                            s = cur.strip()
                            if 1 <= len(s) <= 500:
                                found.setdefault(s, set()).add(base)
                                count += 1
        except Exception:
            continue
    if count:
        print(f"  {base}: {count} chinese refs")

# Convert sets to lists
out = {s: sorted(list(srcs)) for s, srcs in found.items()}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print(f"\nUnique chinese strings in assets: {len(out)}")
print(f"-> {OUT}")
