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
    hay = (title or '') + '\n' + ' '.join(x.strip() for x in body_lines[:80] if x.strip())

    if any(k in hay for k in ['본인확인기관', '방송광고판매대행', '방송사업자', '종합편성방송채널사용사업자', 'SBS미디어홀딩스', '결합상품', '전기통신사업', '부가통신서비스', '시청자미디어', '방송채널사용사업자']):
        return '방송통신위원회', 'kcc-pack3'

    if any(k in hay for k in ['청소년', '성평등', '양성평등', '여성의 삶', '한부모', '아이돌봄', '정영애 장관', '여성사박물관', '청소년사이버상담센터', '성적 유인', '청년 성평등', '미혼모', '학교 밖']):
        return '여성가족부', 'family-pack3'

    if any(k in hay for k in ['아프리카돼지열병', 'ASF', '야생멧돼지', '미세먼지', '불법폐기물', '포스트 플라스틱', '플라스틱 오염', '라돈', 'P4G 서울 녹색미래 정상회의', '드론 활용 감시', '녹조', '환경규제', '대기질 공동연구']):
        return '환경부', 'environment-pack3'

    if any(k in hay for k in ['정보통신전략위원회', '디지털 포용 추진계획', '디지털 미디어 생태계 발전방안', '정보통신기술 수출', 'ICT 수출', 'ICT 수출입 동향']):
        return '과학기술정보통신부', 'msit-pack3'

    if any(k in hay for k in [
        '외국인직접투자', '자동차산업 월간 동향', '주요 유통업체 매출', '신재생에너지 금융지원사업', '태양광', '해상풍력',
        '발전소주변지역 지원', '송․변전설비 주변지역', '송주법', '대이란', '첨단산업 세계공장', '소부장', '에너지이용 합리화 기본계획',
        '희소금속', '자유무역지역', '수소경제', '수소선도국가', 'K-조선', '풍력발전', 'ESS', '전력산업발전유공', '전기문화대상',
        '와이어링 하네스', 'LNG 수출입 동향', '정유업계 탄소중립', '이차전지', '무역전략조정회의', '중견기업',
        '경제자유구역내 외국교육기관', '기업인 특별입국절차', '산업교육진흥 및 산학협력촉진', '폐광지역 개발 지원', '전력수급',
        '에너지전환', '수소충전소', '수소경제홍보 T/F', '핵심품목 공급 안정성', '희소금속 산업 발전대책', '전력시장', '한일 기업인',
        '디지털 전환', '강소·중견기업', '철강수급조사단', '국내복귀', '알뜰 주유소', '요소 공급 안정성', '요소수', '원전', 'RE100'
    ]):
        return '산업통상자원부', 'motie-pack3'

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

manifest_path = QUALITY_DIR / 'unclassified-pattern-pack3-manifest.csv'
with manifest_path.open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['reason', 'new_ministry', 'news_item_id', 'title', 'old_path', 'new_path'])
    for row in changes:
        writer.writerow([row['reason'], row['new_ministry'], row['news_item_id'], row['title'], row['old_path'], row['new_path']])

summary = Counter((row['reason'], row['new_ministry']) for row in changes)
summary_path = QUALITY_DIR / 'unclassified-pattern-pack3-summary.md'
lines = [
    '# gov-press-md unclassified pattern pack 3 summary',
    '',
    '- 규칙: 본문/제목 근거가 충분한 산업부·여가부·환경부·방통위·과기정통부 패턴만 업그레이드',
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
