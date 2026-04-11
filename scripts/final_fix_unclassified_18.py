#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
TARGET = '산업통상자원부'
KEYWORDS = [
    '수출입 동향',
    '정보통신산업(ICT) 수출입 동향',
    '정보통신기술(ICT) 수출',
    '주요 유통업체 매출',
    'APEC 통상장관',
]


def slugify(value: str) -> str:
    value = re.sub(r'[^0-9A-Za-z가-힣]+', '_', value)
    value = re.sub(r'_+', '_', value).strip('_')
    return value[:80] or 'untitled'


def parse_frontmatter(text: str):
    lines = text.splitlines()
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


def main():
    updated = 0
    renamed = 0
    for path in sorted(DATA_DIR.rglob('*.md')):
        if path.name == 'README.md':
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        if 'ministry: "미분류"' not in text:
            continue
        meta, body = parse_frontmatter(text)
        title = meta.get('title', '')
        matched = any(k in title or k in body or k in path.name for k in KEYWORDS)
        if not matched:
            continue
        meta['ministry'] = TARGET
        new_text = rebuild(meta, body)
        path.write_text(new_text, encoding='utf-8')
        updated += 1
        prefix = path.stem.split('_', 1)[0]
        new_name = f"{prefix}_{slugify(TARGET)}_{slugify(title)}.md"
        target = path.with_name(new_name)
        if path.name != new_name and not target.exists():
            path.rename(target)
            renamed += 1
    print('UPDATED', updated)
    print('RENAMED', renamed)


if __name__ == '__main__':
    main()
