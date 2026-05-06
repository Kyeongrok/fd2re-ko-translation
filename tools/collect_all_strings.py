"""
Collect every unique Chinese source string from:
- StringTable bundles (UnitName/Career/Item/Magic)
- Dialogue XMLs (B001/B002/B003/S001) - dialogue text + speaker + scene/node descriptions
- Assembly-CSharp.dll for hardcoded UI strings (Chinese literals)
Output a single all_chinese.json with categorized entries.
"""
import json
import os
import re
import xml.etree.ElementTree as ET

EXTRACTED = r"C:\Users\ocean\git\fd2\fd2re\extracted"
DLL = r"C:\Users\ocean\git\fd2\fd2re\FD2Re_Data\Managed\Assembly-CSharp.dll"
OUT = r"C:\Users\ocean\git\fd2\fd2re\all_chinese.json"

result = {
    "unit_names": [],
    "career_names": [],
    "item_names": [],
    "magic_names": [],
    "dialogues": [],         # full dialogue lines
    "speakers": [],          # speaker= names from XML
    "scene_descriptions": [], # description= attrs
    "dll_strings": [],       # hardcoded chinese literals from .dll
}

def load_table(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    out = []
    for entry in data.get("m_TableData", []):
        s = entry.get("m_Localized", "").strip()
        if s:
            out.append(s)
    return out

result["unit_names"] = load_table(os.path.join(EXTRACTED, "UnitNameTable_zh.json"))
result["career_names"] = load_table(os.path.join(EXTRACTED, "CareerNameTable_zh.json"))
result["item_names"] = load_table(os.path.join(EXTRACTED, "ItemNameTable_zh.json"))
result["magic_names"] = load_table(os.path.join(EXTRACTED, "MagicNameTable_zh.json"))

# Parse XMLs
xml_files = ["B001.xml", "B002.xml", "B003.xml", "S001.xml"]
speakers_set = set()
dialogues_set = set()
desc_set = set()
for xf in xml_files:
    path = os.path.join(EXTRACTED, xf)
    tree = ET.parse(path)
    root = tree.getroot()
    for el in root.iter():
        if el.tag == "Dialogue":
            txt = (el.text or "").strip()
            if txt:
                dialogues_set.add(txt)
            sp = el.get("speaker")
            if sp:
                speakers_set.add(sp.strip())
        # description attribute on StoryNode/BattleNode
        d = el.get("description")
        if d:
            desc_set.add(d.strip())
        # name attributes (TalkCondition name=, AddPartyMember name=, etc.)
        n = el.get("name")
        if n and re.search(r"[一-鿿]", n):
            speakers_set.add(n.strip())  # name fields often refer to characters
        # weapon/armor attributes can also contain item names
        for attr in ("weapon", "armor"):
            v = el.get(attr)
            if v and re.search(r"[一-鿿]", v):
                speakers_set.add(v.strip())  # treat as names — will dedupe with item table later
        # element text that isn't dialogue but contains Chinese (rare)
        if el.text and el.tag != "Dialogue":
            t = el.text.strip()
            if re.search(r"[一-鿿]", t):
                dialogues_set.add(t)

result["dialogues"] = sorted(dialogues_set)
result["speakers"] = sorted(speakers_set)
result["scene_descriptions"] = sorted(desc_set)

# Scan Assembly-CSharp.dll for Chinese literals (UTF-16LE)
print("Scanning DLL for Chinese strings...")
with open(DLL, "rb") as f:
    raw = f.read()
# Try UTF-16LE: each Chinese char = 2 bytes, low byte 0x00-0xFF, high byte 0x4E-0x9F
chinese_strings = set()
i = 0
while i < len(raw) - 4:
    # Look for a Chinese char in UTF-16LE: byte i+1 in 0x4E..0x9F
    if 0x4E <= raw[i+1] <= 0x9F and 0x00 <= raw[i] <= 0xFF:
        # extend run while CJK or common punctuation
        start = i
        end = i
        while end < len(raw) - 1:
            lo = raw[end]
            hi = raw[end+1]
            cp = lo | (hi << 8)
            # CJK Unified, plus common punctuation/whitespace
            if (0x4E00 <= cp <= 0x9FFF) or cp in (0x3001, 0x3002, 0xFF01, 0xFF0C, 0xFF1A, 0xFF1B, 0xFF1F, 0x2026, 0x300C, 0x300D, 0x300E, 0x300F, 0xFF08, 0xFF09, 0x0020, 0x000A, 0xFF5E) or (0x30 <= cp <= 0x39) or (0x41 <= cp <= 0x5A) or (0x61 <= cp <= 0x7A):
                end += 2
            else:
                break
        if end - start >= 4:  # at least 2 chinese chars
            try:
                s = raw[start:end].decode("utf-16le")
                # require at least one Chinese char and reasonable length
                if re.search(r"[一-鿿]", s) and len(s) <= 200:
                    chinese_strings.add(s.strip())
            except:
                pass
            i = end
            continue
    i += 1

result["dll_strings"] = sorted(chinese_strings)

# Build a flat unique-string master list across all categories
all_unique = set()
for k in result:
    for s in result[k]:
        if s:
            all_unique.add(s)
result["_all_unique_count"] = len(all_unique)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

# Also write a flat list for convenience
flat = os.path.join(os.path.dirname(OUT), "all_chinese_flat.txt")
with open(flat, "w", encoding="utf-8") as f:
    for s in sorted(all_unique):
        f.write(s + "\n")

print(f"\n=== TOTALS ===")
for k, v in result.items():
    if isinstance(v, list):
        print(f"  {k}: {len(v)}")
print(f"  TOTAL UNIQUE: {len(all_unique)}")
print(f"\n  -> {OUT}")
print(f"  -> {flat}")
