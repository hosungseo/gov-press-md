#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import csv
import html
import re
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
QUALITY_DIR = ROOT / 'docs' / 'quality'
QUALITY_DIR.mkdir(parents=True, exist_ok=True)


def slugify(value: str) -> str:
    value = html.unescape(value or '')
    value = re.sub(r'&[a-zA-Z]+;', ' ', value)
    value = re.sub(r'[^0-9A-Za-z가-힣]+', '_', value)
    value = re.sub(r'_+', '_', value).strip('_')
    return value[:80] or 'untitled'


def load_record(path: Path):
    text = path.read_text(encoding='utf-8', errors='ignore')
    meta = {}
    body_lines = []
    in_body = False
    for line in text.splitlines():
        if line.strip() == '## 본문':
            in_body = True
            continue
        if in_body:
            body_lines.append(line)
        elif ': ' in line and not line.startswith('- '):
            k, v = line.split(': ', 1)
            meta[k] = html.unescape(v.strip().strip('"'))
    return text, meta, body_lines


def classify(title: str, body_lines):
    hay = (title or '') + '\n' + '\n'.join(body_lines[:40])

    trade_trend_terms = ['수출입 동향', '외국인직접투자 동향', '주요유통업체 매출', '자동차산업 동향']
    if any(term in hay for term in trade_trend_terms):
        return '산업통상자원부', 'economic-trend'

    trade_terms = ['WTO', '세이프가드', '반덤핑', 'FTA', 'CEPA', 'IPEF', '통상', '무역위원회']
    if any(term in hay for term in trade_terms):
        return '산업통상자원부', 'trade-policy'

    committee_title = ('위원회 결과' in (title or '')) or ('위원회(' in (title or '') and '결과' in (title or ''))
    kcc_terms = ['방송광고', '시청자', '지상파방송', '종편', '보도전문', '방송사업자', '전기통신사업', '부가통신서비스', '방송채널사용사업자']
    if committee_title and any(term in hay for term in kcc_terms):
        return '방송통신위원회', 'kcc-committee-broadened'

    return None, None


def replace_line_prefix(lines, prefix, new_line):
    out = []
    for line in lines:
        if line.startswith(prefix):
            out.append(new_line)
        else:
            out.append(line)
    return out


changes = []
for path in sorted(DATA_DIR.rglob('*.md')):
    if path.name == 'README.md':
        continue
    text, meta, body_lines = load_record(path)
    if meta.get('ministry') != '미분류':
        continue
    title = meta.get('title', '')
    news_id = meta.get('news_item_id', '')
    new_ministry, reason = classify(title, body_lines)
    if not new_ministry:
        continue

    lines = text.splitlines()
    lines = replace_line_prefix(lines, 'ministry: ', f'ministry: "{new_ministry}"')
    lines = replace_line_prefix(lines, '- 부처: ', f'- 부처: {new_ministry}')
    new_text = '\n'.join(lines) + ('\n' if text.endswith('\n') else '')
    path.write_text(new_text, encoding='utf-8')

    old_path = path
    prefix = old_path.stem.split('_', 1)[0] if '_' in old_path.stem else old_path.stem
    new_name = f"{prefix}_{slugify(new_ministry)}_{slugify(title)}.md"
    new_path = old_path.with_name(new_name)
    if new_path != old_path:
        if new_path.exists():
            suffix = news_id or 'dup'
            new_path = old_path.with_name(f"{prefix}_{slugify(new_ministry)}_{slugify(title)}_{slugify(suffix)}.md")
        old_path.rename(new_path)

    changes.append({
        'reason': reason,
        'new_ministry': new_ministry,
        'title': title,
        'news_item_id': news_id,
        'old_path': old_path.relative_to(ROOT).as_posix(),
        'new_path': new_path.relative_to(ROOT).as_posix(),
    })

manifest_path = QUALITY_DIR / 'unclassified-pattern-pack2-manifest.csv'
with manifest_path.open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['reason', 'new_ministry', 'news_item_id', 'title', 'old_path', 'new_path'])
    for row in changes:
        writer.writerow([row['reason'], row['new_ministry'], row['news_item_id'], row['title'], row['old_path'], row['new_path']])

summary = Counter((row['reason'], row['new_ministry']) for row in changes)
summary_path = QUALITY_DIR / 'unclassified-pattern-pack2-summary.md'
lines = [
    '# gov-press-md unclassified pattern pack 2 summary',
    '',
    '- 규칙: 미분류 중 제목/문맥이 명확한 경제통계·통상·방통위 위원회 결과만 업그레이드',
    f'- 변경 파일 수: {len(changes):,}',
    f'- manifest: `{manifest_path.relative_to(ROOT).as_posix()}`',
    '',
    '## 적용 유형',
    '',
]
for (reason, ministry), count in summary.most_common():
    lines.append(f'- {reason} → {ministry}: {count}건')
summary_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

print(f'CHANGED_FILES {len(changes)}')
print(f'WROTE {manifest_path.relative_to(ROOT)}')
print(f'WROTE {summary_path.relative_to(ROOT)}')
