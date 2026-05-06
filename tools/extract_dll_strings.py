"""
Extract user strings from Assembly-CSharp.dll's #US heap.
Also scan resources.assets / sharedassets for any TextAsset XML / config strings.
Write a clean DLL string list.
"""
import dnfile
import re
import json
import os

DLL = r"C:\Users\ocean\git\fd2\fd2re\FD2Re_Data\Managed\Assembly-CSharp.dll"
OUT = r"C:\Users\ocean\git\fd2\fd2re\dll_strings.json"

pe = dnfile.dnPE(DLL)
us = pe.net.user_strings
data = us.__data__

def read_compressed_int(b, p):
    v = b[p]
    if v & 0x80 == 0:
        return v, 1
    if v & 0xC0 == 0x80:
        return ((v & 0x3F) << 8) | b[p+1], 2
    return ((v & 0x1F) << 24) | (b[p+1] << 16) | (b[p+2] << 8) | b[p+3], 4

all_strings = []
pos = 1
while pos < len(data):
    if data[pos] == 0:
        pos += 1
        continue
    L, ll = read_compressed_int(data, pos)
    pos += ll
    if L == 0 or pos + L > len(data):
        break
    blob = data[pos:pos+L-1]
    pos += L
    try:
        s = blob.decode("utf-16le", errors="replace")
        all_strings.append(s)
    except:
        pass

print(f"Total user strings: {len(all_strings)}")
chinese = [s for s in all_strings if re.search(r"[一-鿿]", s)]
print(f"Chinese-containing: {len(chinese)}")

# Classify: UI strings (likely shown to user) vs debug logs
# Heuristic: skip strings containing typical debug prefixes
DEBUG_PREFIXES = (
    "ScriptableObject", "LevelManager:", "ItemSelectionPopup:",
    "LoadAvailableMagic:", "资源加载", "从路径", "未找到名为",
    "存档文件", "保存游戏失败", "加载游戏失败", "删除存档", "读取存档信息",
    "存档槽位索引", "创建存档目录", "保存存档失败"
)
def is_debug(s):
    if any(s.startswith(p) for p in DEBUG_PREFIXES):
        return True
    # Heuristic: strings with multiple {0} {1} {2} but mixing ASCII keywords like "类" "类型"
    # in code paths often debug. We'll keep most though, since "{0}金币" etc. ARE shown to user.
    # Be conservative: don't auto-classify. Just report.
    return False

ui_strings = [s for s in chinese if not is_debug(s)]
debug_strings = [s for s in chinese if is_debug(s)]

print(f"UI candidate: {len(ui_strings)}")
print(f"Debug-only: {len(debug_strings)}")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump({
        "ui_strings": sorted(ui_strings),
        "debug_strings": sorted(debug_strings),
    }, f, ensure_ascii=False, indent=2)

print(f"\nWrote: {OUT}")
print("\n--- ALL UI strings ---")
for s in sorted(ui_strings):
    print(repr(s))
