#!/usr/bin/env python3
from collections import defaultdict
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
OUT_DIR = ROOT / 'docs' / 'ministries'
OUT_DIR.mkdir(parents=True, exist_ok=True)

records = defaultdict(list)

for md in sorted(DATA_DIR.rglob('*.md')):
    if md.name == 'README.md':
        continue
    rel = md.relative_to(ROOT)
    text = md.read_text(encoding='utf-8', errors='ignore')
    title = ''
    ministry = ''
    approve_date = ''
    for line in text.splitlines()[:20]:
        if line.startswith('title: '):
            title = line.split(': ', 1)[1].strip().strip('"')
        elif line.startswith('ministry: '):
            ministry = line.split(': ', 1)[1].strip().strip('"')
        elif line.startswith('approve_date: '):
            approve_date = line.split(': ', 1)[1].strip().strip('"')
    ministry = ministry or '미분류'
    records[ministry].append((approve_date, title, rel.as_posix()))

index_lines = ['# 부처별 인덱스', '']
for ministry in sorted(records):
    safe = re.sub(r'[^0-9A-Za-z가-힣]+', '_', ministry).strip('_') or '미분류'
    path = OUT_DIR / f'{safe}.md'
    lines = [f'# {ministry}', '']
    for approve_date, title, rel in sorted(records[ministry], reverse=True):
        lines.append(f'- {approve_date} — [{title}](../../{rel})')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    index_lines.append(f'- [{ministry}](ministries/{safe}.md) — {len(records[ministry])}건')

(ROOT / 'docs' / 'ministry-index.md').write_text('\n'.join(index_lines) + '\n', encoding='utf-8')
print(f'WROTE {len(records)} ministry index files')
