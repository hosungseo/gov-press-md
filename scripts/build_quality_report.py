#!/usr/bin/env python3
from collections import Counter, defaultdict
from pathlib import Path
import csv
import html

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
OUT_DIR = ROOT / 'docs' / 'quality'
OUT_DIR.mkdir(parents=True, exist_ok=True)


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
day_counts = Counter()
for md in sorted(DATA_DIR.rglob('*.md')):
    if md.name == 'README.md':
        continue
    rel = md.relative_to(ROOT).as_posix()
    meta = parse_frontmatter(md)
    day = rel.split('/')[3]
    day_counts[day] += 1
    meta['path'] = rel
    meta['day'] = day
    records.append(meta)

# Duplicate analysis
by_id = defaultdict(list)
for rec in records:
    nid = rec['news_item_id']
    if nid:
        by_id[nid].append(rec)

duplicate_groups = {nid: rows for nid, rows in by_id.items() if len(rows) > 1}
duplicate_rows = []
for nid, rows in duplicate_groups.items():
    days = sorted({row['day'] for row in rows})
    titles = sorted({row['title'] for row in rows})
    ministries = sorted({row['ministry'] for row in rows})
    duplicate_rows.append({
        'news_item_id': nid,
        'copies': len(rows),
        'unique_days': len(days),
        'first_day': days[0],
        'last_day': days[-1],
        'title': titles[0] if titles else '',
        'ministry': ministries[0] if ministries else '',
        'paths': [row['path'] for row in rows],
    })

duplicate_rows.sort(key=lambda row: (-row['copies'], row['first_day'], row['news_item_id']))

csv_path = OUT_DIR / 'duplicate-news-item-ids.csv'
with csv_path.open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['news_item_id', 'copies', 'unique_days', 'first_day', 'last_day', 'ministry', 'title', 'paths'])
    for row in duplicate_rows:
        writer.writerow([
            row['news_item_id'], row['copies'], row['unique_days'], row['first_day'], row['last_day'], row['ministry'], row['title'], ' | '.join(row['paths'])
        ])

low_days = sorted((day, count) for day, count in day_counts.items() if count <= 5)
zero_days = [day for day, count in sorted(day_counts.items()) if count == 0]
# zero_days will be empty because only existing dirs are counted, keep explicit placeholder logic in report.

report_lines = [
    '# gov-press-md 품질 진단 리포트',
    '',
    f'- 총 레코드: {len(records):,}건',
    f'- 총 날짜 디렉터리: {len(day_counts):,}일',
    f'- news_item_id 중복 그룹: {len(duplicate_rows):,}개',
    f'- news_item_id 중복 초과본(그룹 내 추가 사본 합계): {sum(row["copies"] - 1 for row in duplicate_rows):,}건',
    f'- 저건수 날짜(<=5건): {len(low_days):,}일',
    '',
    '## 1. 중복 그룹 상위 20개',
    '',
]

for row in duplicate_rows[:20]:
    report_lines.append(
        f'- `{row["news_item_id"]}` ({row["copies"]}건, {row["first_day"]} ~ {row["last_day"]}) — {row["ministry"]} / {row["title"]}'
    )
report_lines += [
    '',
    f'전체 목록 CSV: `{csv_path.relative_to(ROOT).as_posix()}`',
    '',
    '## 2. 저건수 날짜(<=5건) 샘플',
    '',
]
for day, count in low_days[:40]:
    report_lines.append(f'- {day}: {count}건')
report_lines += [
    '',
    '## 3. 주의가 필요한 날짜',
    '',
    '- `2020-08-21`: 원본 API 응답 truncation으로 salvage 처리되어 1건만 회수됨',
    '- `2020-08-20`: truncation 응답에서 완전한 item만 salvage 처리해 94건 회수됨',
    '- 인접 날짜 중복이 많아 날짜 완전성과 canonical record 정책을 분리해 다뤄야 함',
    '',
    '## 4. 권장 다음 작업',
    '',
    '1. `news_item_id` 기준 canonical 정책 결정 (첫 게시일 유지 vs 날짜별 재노출 보존)',
    '2. 중복 그룹을 날짜 차이 기준으로 분류한 후, 인접일 재노출과 진짜 중복을 구분',
    '3. `2020-08-21`은 원문 truncation 예외일로 별도 플래그 유지',
]

report_path = OUT_DIR / 'quality-report.md'
report_path.write_text('\n'.join(report_lines) + '\n', encoding='utf-8')
print(f'WROTE {report_path.relative_to(ROOT)}')
print(f'WROTE {csv_path.relative_to(ROOT)}')
print(f'DUP_GROUPS {len(duplicate_rows)}')
print(f'LOW_DAYS {len(low_days)}')
