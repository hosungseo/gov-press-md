#!/usr/bin/env python3
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_press_releases import write_day, DEFAULT_SERVICE_KEY, API_URL


def fetch_text(day_str: str) -> str:
    compact = day_str.replace('-', '')
    url = f"{API_URL}?serviceKey={DEFAULT_SERVICE_KEY}&startDate={compact}&endDate={compact}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode('utf-8', 'replace')


def salvage(day_str: str) -> int:
    text = fetch_text(day_str)
    items = re.findall(r'<NewsItem>(.*?)</NewsItem>', text, re.S)
    target_prefix = date.fromisoformat(day_str).strftime('%m/%d/%Y')
    kept = []
    for chunk in items:
        approve = re.search(r'<ApproveDate>(.*?)</ApproveDate>', chunk)
        approve_text = approve.group(1) if approve else ''
        if approve_text.startswith(target_prefix):
            kept.append('<NewsItem>' + chunk + '</NewsItem>')
    xml = '<response><header><resultCode>0</resultCode><resultMsg>SALVAGED_TRUNCATED_XML</resultMsg></header><body>' + ''.join(kept) + '</body></response>'
    root = ET.fromstring(xml)
    return write_day(date.fromisoformat(day_str), root)


for day in ['2020-08-20', '2020-08-21']:
    count = salvage(day)
    print(day, count)
