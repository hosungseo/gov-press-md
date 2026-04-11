#!/usr/bin/env python3
from pathlib import Path
import html

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'


def read_title(path: Path) -> str:
    for line in path.read_text(encoding='utf-8', errors='ignore').splitlines()[:20]:
        if line.startswith('title: '):
            return html.unescape(line.split(': ', 1)[1].strip().strip('"'))
    return path.stem.split('_', 2)[-1].replace('_', ' ')


def build_day_readme(day_dir: Path) -> int:
    day = day_dir.name
    files = sorted(p for p in day_dir.glob('*.md') if p.name != 'README.md')
    lines = [f'# {day} 정부 보도자료', '', f'- 건수: {len(files)}', '']
    for path in files:
        title = read_title(path)
        lines.append(f'- [{title}]({path.name})')
    (day_dir / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return len(files)


def main():
    total_days = 0
    total_docs = 0
    for day_dir in sorted(DATA_DIR.glob('*/*/*')):
        if not day_dir.is_dir():
            continue
        total_days += 1
        total_docs += build_day_readme(day_dir)
    print(f'WROTE {total_days} day readmes / {total_docs} docs')


if __name__ == '__main__':
    main()
