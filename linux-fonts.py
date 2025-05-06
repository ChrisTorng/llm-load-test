#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列出 Linux 系統上可用的常見中文字型
"""
from matplotlib.font_manager import fontManager
import platform

# 常見中文字型清單
chinese_fonts = [
    'Noto Sans CJK TC',
    'WenQuanYi Zen Hei',
    'AR PL UMing CN',
    'AR PL UKai CN',
    'SimSun',
    'SimHei',
    'Microsoft YaHei',
    'PingFang TC',
    'Heiti TC',
    'STHeitiTC-Light',
    'Source Han Sans TW',
    'Source Han Serif TW',
    'TW-Kai',
    'TW-Sung',
]

# 取得系統所有字型名稱
sys_fonts = set(f.name for f in fontManager.ttflist)
print("系統所有字型名稱：")
for font in sorted(sys_fonts):
    print(f"  {font}")
print()
print("偵測到的中文字型：")
found = False
for font in chinese_fonts:
    if font in sys_fonts:
        print(f"  ✔ {font}")
        found = True
    else:
        print(f"    {font}")
if not found:
    print("未偵測到常見中文字型，請安裝 Noto Sans CJK TC 或 WenQuanYi Zen Hei 以避免中文顯示異常。")
