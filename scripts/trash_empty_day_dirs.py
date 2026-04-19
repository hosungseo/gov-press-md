#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
TRASH_ROOT = Path.home() / '.Trash' / f'gov-press-md-empty-days-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
TRASH_ROOT.mkdir(parents=True, exist_ok=True)

empty_days = []
for day in sorted(DATA_DIR.glob('*/*/*')):
    if not day.is_dir():
        continue
    files = [p for p in day.glob('*.md') if p.name != 'README.md']
    if not files:
        empty_days.append(day)

for day in empty_days:
    dst = TRASH_ROOT / day.relative_to(ROOT)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(day), str(dst))

# clean up now-empty month/year dirs inside repo
for path in sorted(DATA_DIR.glob('*/*'), reverse=True):
    if path.is_dir() and not any(path.iterdir()):
        path.rmdir()
for path in sorted(DATA_DIR.glob('*'), reverse=True):
    if path.is_dir() and not any(path.iterdir()):
        path.rmdir()

print(f'TRASH {TRASH_ROOT}')
print(f'EMPTY_DAY_DIRS_MOVED {len(empty_days)}')
for day in empty_days[:50]:
    print(day.relative_to(ROOT).as_posix())
