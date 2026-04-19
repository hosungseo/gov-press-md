#!/usr/bin/env python3
from collections import defaultdict
from pathlib import Path
from datetime import datetime
import csv
import html
import shutil

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
QUALITY_DIR = ROOT / 'docs' / 'quality'
QUALITY_DIR.mkdir(parents=True, exist_ok=True)

TRASH_ROOT = Path.home() / '.Trash' / f'gov-press-md-dedupe-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
TRASH_ROOT.mkdir(parents=True, exist_ok=True)


def parse_frontmatter(md: Path):
    text = md.read_text(encoding='utf-8', errors='ignore')
    meta = {
        'title': '',
        'ministry': '',
        'approve_date': '',
        'news_item_id': '',
        'grouping_code': '',
        'original_url': '',
    }
    for line in text.splitlines()[:20]:
        for key in list(meta.keys()):
            prefix = f'{key}: '
            if line.startswith(prefix):
                meta[key] = html.unescape(line[len(prefix):].strip().strip('"'))
    return meta


records = []
for md in sorted(DATA_DIR.rglob('*.md')):
    if md.name == 'README.md':
        continue
    meta = parse_frontmatter(md)
    meta['path'] = md
    rel = md.relative_to(ROOT).as_posix()
    meta['rel'] = rel
    parts = rel.split('/')
    meta['day'] = parts[3]
    records.append(meta)

by_id = defaultdict(list)
for rec in records:
    nid = rec['news_item_id']
    if nid:
        by_id[nid].append(rec)

removed_rows = []
kept_count = 0
removed_count = 0
for nid, rows in by_id.items():
    if len(rows) <= 1:
        continue
    rows_sorted = sorted(rows, key=lambda r: (r['day'], r['approve_date'], r['rel']))
    keeper = rows_sorted[0]
    kept_count += 1
    for rec in rows_sorted[1:]:
        src = rec['path']
        dst = TRASH_ROOT / src.relative_to(ROOT)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        removed_rows.append([
            nid,
            keeper['day'],
            keeper['rel'],
            rec['day'],
            rec['rel'],
            rec['title'],
            rec['ministry'],
        ])
        removed_count += 1

manifest = QUALITY_DIR / 'dedupe-removed-manifest.csv'
with manifest.open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['news_item_id', 'kept_day', 'kept_path', 'removed_day', 'removed_path', 'title', 'ministry'])
    writer.writerows(removed_rows)

summary = QUALITY_DIR / 'dedupe-summary.md'
summary.write_text(
    '\n'.join([
        '# gov-press-md dedupe summary',
        '',
        f'- dedupe 기준: `news_item_id` 동일 시 가장 이른 날짜 1건만 유지',
        f'- 중복 그룹 처리 수: {kept_count:,}',
        f'- 제거된 중복 파일 수: {removed_count:,}',
        f'- 이동 위치: `{TRASH_ROOT}`',
        f'- manifest: `{manifest.relative_to(ROOT).as_posix()}`',
    ]) + '\n',
    encoding='utf-8',
)

print(f'TRASH {TRASH_ROOT}')
print(f'DEDUPE_GROUPS {kept_count}')
print(f'REMOVED_FILES {removed_count}')
print(f'WROTE {manifest.relative_to(ROOT)}')
print(f'WROTE {summary.relative_to(ROOT)}')
