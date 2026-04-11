#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'

MINISTRY_PATTERNS = [
    r'([가-힣A-Za-z·]+부)',
    r'([가-힣A-Za-z·]+청)',
    r'([가-힣A-Za-z·]+처)',
    r'([가-힣A-Za-z·]+위원회)',
    r'([가-힣A-Za-z·]+원)',
    r'([가-힣A-Za-z·]+실)',
    r'([가-힣A-Za-z·]+본부)',
]

KNOWN_HINTS = {
    '방문규 장관': '산업통상자원부',
    '이주호': '교육부',
    '김주현 금융위원회 위원장': '금융위원회',
    '금융감독원': '금융위원회',
    '해양경찰청장': '해양경찰청',
    '질병관리청장': '질병관리청',
    '국토교통부': '국토교통부',
    '행정안전부': '행정안전부',
    '산업통상자원부': '산업통상자원부',
    '교육부': '교육부',
    '금융위원회': '금융위원회',
    '해양경찰청': '해양경찰청',
    '농림축산식품부': '농림축산식품부',
    '기획재정부': '기획재정부',
    '국무조정실': '국무조정실',
    '보건복지부': '보건복지부',
    '고용노동부': '고용노동부',
    '문화체육관광부': '문화체육관광부',
    '환경부': '환경부',
    '법무부': '법무부',
    '외교부': '외교부',
    '병무청': '병무청',
    '조달청': '조달청',
    '관세청': '관세청',
    '산림청': '산림청',
    '소방청': '소방청',
    '통계청': '통계청',
}


def normalize_text(value: str) -> str:
    value = html.unescape(value or '')
    value = value.replace('\xa0', ' ')
    value = re.sub(r'\s+', ' ', value)
    return value.strip()


def slugify(value: str) -> str:
    value = normalize_text(value)
    value = re.sub(r'[^0-9A-Za-z가-힣]+', '_', value)
    value = re.sub(r'_+', '_', value).strip('_')
    return value[:80] or 'untitled'


def parse_frontmatter(text: str):
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        return {}, text
    meta = {}
    body_start = 0
    for i in range(1, len(lines)):
        line = lines[i]
        if line.strip() == '---':
            body_start = i + 1
            break
        if ': ' in line:
            k, v = line.split(': ', 1)
            meta[k.strip()] = v.strip().strip('"')
    body = '\n'.join(lines[body_start:])
    return meta, body


def rebuild(meta: dict, body: str) -> str:
    ordered = [
        'title', 'ministry', 'approve_date', 'news_item_id',
        'grouping_code', 'original_url', 'attachment_count', 'source'
    ]
    lines = ['---']
    for key in ordered:
        if key not in meta:
            continue
        val = str(meta[key])
        if key == 'attachment_count' and val.isdigit():
            lines.append(f'{key}: {val}')
        else:
            lines.append(f'{key}: "{val.replace(chr(34), chr(39))}"')
    lines += ['---', '', body.strip(), '']
    return '\n'.join(lines)


def infer_from_text(text: str) -> str:
    text = normalize_text(text)
    for hint, ministry in KNOWN_HINTS.items():
        if hint in text:
            return ministry
    for pattern in MINISTRY_PATTERNS:
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    return ''


def main():
    updated = 0
    renamed = 0
    resolved = 0
    for path in sorted(DATA_DIR.rglob('*.md')):
        if path.name == 'README.md':
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        meta, body = parse_frontmatter(text)
        if not meta:
            continue
        ministry = normalize_text(meta.get('ministry', ''))
        if ministry != '미분류':
            continue
        title = normalize_text(meta.get('title', ''))
        original = normalize_text(meta.get('original_url', ''))
        candidate = ''
        for source in [title, body[:1200], original, path.name]:
            candidate = infer_from_text(source)
            if candidate and candidate != '미분류':
                break
        if not candidate:
            continue
        meta['ministry'] = candidate
        new_text = rebuild(meta, body)
        path.write_text(new_text, encoding='utf-8')
        updated += 1
        resolved += 1
        prefix = path.stem.split('_', 1)[0]
        new_name = f"{prefix}_{slugify(candidate)}_{slugify(title)}.md"
        target = path.with_name(new_name)
        if path.name != new_name and not target.exists():
            path.rename(target)
            renamed += 1
    print(f'UPDATED {updated}')
    print(f'RESOLVED {resolved}')
    print(f'RENAMED {renamed}')


if __name__ == '__main__':
    main()
