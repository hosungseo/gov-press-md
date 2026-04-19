#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from collections import Counter
import csv
import html
import re

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
QUALITY_DIR = ROOT / 'docs' / 'quality'
QUALITY_DIR.mkdir(parents=True, exist_ok=True)

ALIAS_MAP = {
    '산업부': '산업통상자원부',
    '산자부': '산업통상자원부',
    '복지부': '보건복지부',
    '방통위': '방송통신위원회',
    '여가부': '여성가족부',
    '공정위': '공정거래위원회',
    '기재부': '기획재정부',
    '고용부': '고용노동부',
    '국토부': '국토교통부',
    '행안부': '행정안전부',
    '문체부': '문화체육관광부',
    '농식품부': '농림축산식품부',
    '해수부': '해양수산부',
    '중기부': '중소벤처기업부',
    '과기정통부': '과학기술정보통신부',
    '식약처': '식품의약품안전처',
    '질병청': '질병관리청',
    '인사처': '인사혁신처',
    '국조실': '국무조정실',
    '국표원': '국가기술표준원',
    '행복청': '행정중심복합도시건설청',
    '원안위': '원자력안전위원회',
    '개보위': '개인정보보호위원회',
    '권익위': '국민권익위원회',
    '금융위': '금융위원회',
    '공수처': '고위공직자범죄수사처',
    '농진청': '농촌진흥청',
    '해경청': '해양경찰청',
    '방사청': '방위사업청',
    '보훈부': '국가보훈부',
    '보훈처': '국가보훈처',
}

NOISE_VALUES = {
    '정부', '지원', '일부', '위원', '온실', '당부', '신청', '요청', '자원', '조원', '세부', '사실',
    '시청', '손실', '복원', '대부', '소부', '고부', '천원', '현실', '공청', '항원', '강원', '회원',
    '여부', '출처', '부처', '관계부', '공공부', '범정부', '억원', '년부', '월부', '불확실', '창원',
    '내년부', '국립공원', '국립생물자원', '고병원', '소재·부', '한부', '다부', '피부', '서부',
}


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


records = []
ministry_counts = Counter()
for path in sorted(DATA_DIR.rglob('*.md')):
    if path.name == 'README.md':
        continue
    text, meta, body_lines = load_record(path)
    ministry = meta.get('ministry', '')
    ministry_counts[ministry] += 1
    records.append({
        'path': path,
        'text': text,
        'meta': meta,
        'body_lines': body_lines,
    })

canonical_names = set(ALIAS_MAP.values())
for name, count in ministry_counts.items():
    if not name or name in NOISE_VALUES:
        continue
    if count >= 20 and len(name) >= 3:
        canonical_names.add(ALIAS_MAP.get(name, name))

search_terms = sorted(set(list(canonical_names) + list(ALIAS_MAP.keys())), key=lambda x: (-len(x), x))


def infer_from_text(title: str, body_lines):
    haystack = (title or '') + '\n' + '\n'.join(body_lines[:80])
    best = None
    for term in search_terms:
        idx = haystack.find(term)
        if idx == -1:
            continue
        canonical = ALIAS_MAP.get(term, term)
        score = (idx, -len(term), canonical)
        if best is None or score < best[0]:
            best = (score, canonical)
    return best[1] if best else ''


def replace_line_prefix(lines, prefix, new_line):
    out = []
    replaced = False
    for line in lines:
        if line.startswith(prefix):
            out.append(new_line)
            replaced = True
        else:
            out.append(line)
    return out, replaced

changes = []
for rec in records:
    meta = rec['meta']
    current = meta.get('ministry', '')
    title = meta.get('title', '')
    news_id = meta.get('news_item_id', '')
    if current not in NOISE_VALUES and current not in ALIAS_MAP:
        continue

    inferred = infer_from_text(title, rec['body_lines'])
    if current in ALIAS_MAP:
        new_ministry = ALIAS_MAP[current]
        reason = 'alias'
    elif inferred:
        new_ministry = inferred
        reason = 'inferred'
    else:
        new_ministry = '미분류'
        reason = 'fallback-unclassified'

    if new_ministry == current:
        continue

    lines = rec['text'].splitlines()
    lines, _ = replace_line_prefix(lines, 'ministry: ', f'ministry: "{new_ministry.replace(chr(34), chr(39))}"')
    lines, _ = replace_line_prefix(lines, '- 부처: ', f'- 부처: {new_ministry}')
    new_text = '\n'.join(lines) + ('\n' if rec['text'].endswith('\n') else '')
    rec['path'].write_text(new_text, encoding='utf-8')

    old_path = rec['path']
    prefix = old_path.stem.split('_', 1)[0] if '_' in old_path.stem else old_path.stem
    new_name = f"{prefix}_{slugify(new_ministry)}_{slugify(title)}.md"
    new_path = old_path.with_name(new_name)
    if new_path != old_path:
        if new_path.exists():
            suffix = news_id or 'dup'
            new_path = old_path.with_name(f"{prefix}_{slugify(new_ministry)}_{slugify(title)}_{slugify(suffix)}.md")
        old_path.rename(new_path)

    changes.append({
        'old_ministry': current,
        'new_ministry': new_ministry,
        'reason': reason,
        'title': title,
        'news_item_id': news_id,
        'old_path': old_path.relative_to(ROOT).as_posix(),
        'new_path': new_path.relative_to(ROOT).as_posix(),
    })

manifest_path = QUALITY_DIR / 'ministry-normalization-manifest.csv'
with manifest_path.open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['old_ministry', 'new_ministry', 'reason', 'news_item_id', 'title', 'old_path', 'new_path'])
    for row in changes:
        writer.writerow([
            row['old_ministry'], row['new_ministry'], row['reason'], row['news_item_id'], row['title'], row['old_path'], row['new_path']
        ])

summary_counts = Counter((row['old_ministry'], row['new_ministry'], row['reason']) for row in changes)
summary_lines = [
    '# gov-press-md ministry normalization summary',
    '',
    '- 규칙: 약칭은 정식 기관명으로 통일, 노이즈 값은 제목/본문에서 기관명을 추론, 실패 시 `미분류`',
    f'- 변경 파일 수: {len(changes):,}',
    f'- manifest: `{manifest_path.relative_to(ROOT).as_posix()}`',
    '',
    '## 변경 상위 유형',
    '',
]
for (old_m, new_m, reason), count in summary_counts.most_common(40):
    summary_lines.append(f'- {old_m} → {new_m} ({reason}): {count}건')
summary_path = QUALITY_DIR / 'ministry-normalization-summary.md'
summary_path.write_text('\n'.join(summary_lines) + '\n', encoding='utf-8')

print(f'CHANGED_FILES {len(changes)}')
print(f'WROTE {manifest_path.relative_to(ROOT)}')
print(f'WROTE {summary_path.relative_to(ROOT)}')
