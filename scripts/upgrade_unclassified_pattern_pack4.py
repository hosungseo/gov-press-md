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
    hay = (title or '') + '\n' + ' '.join(x.strip() for x in body_lines[:120] if x.strip())

    if any(k in hay for k in ['포항지진', '홍수 피해 주민', '지방하천에서 금년 홍수기', '피해구제심의위']):
        return '행정안전부', 'mois-pack4'

    if any(k in hay for k in ['정보통신산업(ICT) 수출', '정보통신기술 수출', '정보통신기술(ICT) 수출', 'ICT 수출입 동향', '디지털 포용 추진계획', '디지털 미디어 생태계 발전방안']):
        return '과학기술정보통신부', 'msit-pack4'

    if any(k in hay for k in ['무역의 날', '반도체 장비 글로벌 기업', '자동차산업 월간 동향', '주요 유통업체 매출', '외국인직접투자', '신재생에너지 금융지원사업', '태양광 시장', '해상풍력 발전', '발전소주변지역 지원', '송․변전설비 주변지역', '송주법', '대이란', '전기문화대상', '와이어링 하네스', '에너지이용 합리화 기본계획', '경제자유구역내 외국교육기관', '기업인 특별입국절차', '폐광지역 개발 지원', '에너지전환 확산', '무역대국 도약', '수소경제홍보 T/F', 'WTO 한-미 세탁기 세이프가드', '한미 자유무역협정']):
        return '산업통상자원부', 'motie-pack4'

    if any(k in hay for k in ['포스트 플라스틱', '플라스틱 오염', '라돈', '불법폐기물', '물새류', '도요새', '동·식물 세밀화', '기후에너지', '환경교육역량', '대기질 공동연구', '미세먼지 계절관리제']):
        return '환경부', 'me-pack4'

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

manifest_path = QUALITY_DIR / 'unclassified-pattern-pack4-manifest.csv'
with manifest_path.open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['reason', 'new_ministry', 'news_item_id', 'title', 'old_path', 'new_path'])
    for row in changes:
        writer.writerow([row['reason'], row['new_ministry'], row['news_item_id'], row['title'], row['old_path'], row['new_path']])

summary = Counter((row['reason'], row['new_ministry']) for row in changes)
summary_path = QUALITY_DIR / 'unclassified-pattern-pack4-summary.md'
lines = [
    '# gov-press-md unclassified pattern pack 4 summary',
    '',
    '- 규칙: 남은 미분류 중 고신뢰 행안부·과기정통부·산업부·환경부 패턴만 업그레이드',
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
