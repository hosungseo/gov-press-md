#!/usr/bin/env python3
import argparse
import html
import re
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from pathlib import Path

from normalize_html import clean_html, extract_links

DEFAULT_SERVICE_KEY = "aIjg7oEO5AacryP2v03u06r4%2B9magi7FWC4EdjePS7YyuJpNCi1e8V3sZtAiUMH%2FuBwLHspSb%2FlnHtmGS0GYjg%3D%3D"
API_URL = "https://apis.data.go.kr/1371000/pressReleaseService/pressReleaseList"
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def slugify(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"&[a-zA-Z]+;", " ", value)
    value = re.sub(r"[^0-9A-Za-z가-힣]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value[:80] or "untitled"


def normalize_text(value: str) -> str:
    value = html.unescape(value or "")
    value = value.replace('\xa0', ' ')
    value = re.sub(r'\s+', ' ', value)
    return value.strip()


MINISTRY_PATTERNS = [
    r'([가-힣A-Za-z·]+부)',
    r'([가-힣A-Za-z·]+청)',
    r'([가-힣A-Za-z·]+처)',
    r'([가-힣A-Za-z·]+위원회)',
    r'([가-힣A-Za-z·]+원)',
    r'([가-힣A-Za-z·]+실)',
]


def infer_ministry(title: str, body: str) -> str:
    title = normalize_text(title)
    body = body or ''
    for pattern in MINISTRY_PATTERNS:
        m = re.search(pattern, title)
        if m:
            return m.group(1)
    for line in body.splitlines()[:12]:
        line = normalize_text(line)
        if not line:
            continue
        for pattern in MINISTRY_PATTERNS:
            m = re.search(pattern, line)
            if m:
                return m.group(1)
    return ''


def fetch_day(day: date, service_key: str) -> bytes:
    day_str = day.strftime("%Y%m%d")
    url = f"{API_URL}?serviceKey={service_key}&startDate={day_str}&endDate={day_str}"
    last_err = None
    backoffs = [5, 15, 30, 60, 120, 300]
    for attempt, delay in enumerate(backoffs, 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=40) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code == 429 and attempt < len(backoffs):
                retry_after = e.headers.get('Retry-After')
                sleep_for = int(retry_after) if retry_after and retry_after.isdigit() else delay
                print(f"429 {day.isoformat()}: sleep {sleep_for}s (attempt {attempt}/{len(backoffs)})")
                time.sleep(sleep_for)
                continue
            time.sleep(delay)
        except Exception as e:
            last_err = e
            time.sleep(delay)
    raise RuntimeError(f"failed to fetch {day.isoformat()}: {last_err}")


def write_day(day: date, root: ET.Element) -> int:
    items = root.findall('.//NewsItem')
    month_dir = DATA_DIR / str(day.year) / day.strftime('%Y-%m')
    out_dir = month_dir / day.isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)

    index_lines = [
        f"# {day.isoformat()} 정부 보도자료",
        "",
        f"- 수집일: {datetime.now().isoformat(timespec='seconds')}",
        f"- 건수: {len(items)}",
        "",
    ]

    count = 0
    for idx, item in enumerate(items, 1):
        news_id = normalize_text(item.findtext('NewsItemId') or '')
        title = normalize_text(item.findtext('Title') or '')
        minister = normalize_text(item.findtext('MinisterCode') or '')
        approve = normalize_text(item.findtext('ApproveDate') or '')
        original = normalize_text(item.findtext('OriginalUrl') or '')
        grouping = normalize_text(item.findtext('GroupingCode') or '')
        subtitle1 = normalize_text(item.findtext('SubTitle1') or '')
        subtitle2 = normalize_text(item.findtext('SubTitle2') or '')
        subtitle3 = normalize_text(item.findtext('SubTitle3') or '')
        raw_html = item.findtext('DataContents') or ''
        body = clean_html(raw_html)
        minister = minister or infer_ministry(title, body)
        display_ministry = minister or '미분류'
        fname = f"{idx:03d}_{slugify(display_ministry)}_{slugify(title)}.md"
        links = extract_links(raw_html)
        lines = [
            '---',
            f'title: "{title.replace(chr(34), chr(39))}"',
            f'ministry: "{display_ministry.replace(chr(34), chr(39))}"',
            f'approve_date: "{approve}"',
            f'news_item_id: "{news_id}"',
            f'grouping_code: "{grouping}"',
            f'original_url: "{original}"',
            f'attachment_count: {len(links)}',
            'source: "policy-briefing-api"',
            '---',
            '',
            f'# {title}',
            '',
        ]
        if display_ministry:
            lines.append(f'- 부처: {display_ministry}')
        if approve:
            lines.append(f'- 배포일: {approve}')
        if news_id:
            lines.append(f'- NewsItemId: {news_id}')
        if original:
            lines.append(f'- 원문: {original}')
        lines.append('')
        for sub in [subtitle1, subtitle2, subtitle3]:
            if sub:
                lines += [f'> {sub}', '']
        lines += ['## 본문', '', body if body else '(본문 없음)', '']
        if links:
            lines += ['## 첨부/링크', '']
            for label, href in links:
                lines.append(f'- [{label}]({href})')
            lines.append('')
        lines += ['## 출처', '', '- 정책브리핑 보도자료 API']
        (out_dir / fname).write_text('\n'.join(lines), encoding='utf-8')
        index_lines.append(f'- [{title}]({fname}) — {display_ministry}')
        count += 1

    (out_dir / 'README.md').write_text('\n'.join(index_lines) + '\n', encoding='utf-8')
    return count


def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', required=True, help='YYYY-MM-DD')
    parser.add_argument('--end', help='YYYY-MM-DD; defaults to start')
    parser.add_argument('--service-key', default=DEFAULT_SERVICE_KEY)
    parser.add_argument('--skip-existing', action='store_true', help='Skip days that already have a README.md')
    parser.add_argument('--continue-on-error', action='store_true', help='Log errors and continue with next day')
    parser.add_argument('--sleep-seconds', type=float, default=0.6, help='Delay between day requests')
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end) if args.end else start

    total = 0
    errors = 0
    for d in daterange(start, end):
        out_dir = DATA_DIR / str(d.year) / d.strftime('%Y-%m') / d.isoformat()
        if args.skip_existing and (out_dir / 'README.md').exists():
            print(f'{d.isoformat()}: SKIP')
            continue
        try:
            xml = fetch_day(d, args.service_key)
            root = ET.fromstring(xml)
            code = root.findtext('./header/resultCode')
            msg = root.findtext('./header/resultMsg')
            if code != '0':
                raise RuntimeError(f'{d.isoformat()}: API {code} {msg}')
            count = write_day(d, root)
            print(f'{d.isoformat()}: {count}')
            total += count
        except Exception as e:
            errors += 1
            print(f'ERROR {d.isoformat()}: {e}')
            if not args.continue_on_error:
                raise
        time.sleep(args.sleep_seconds)
    print(f'TOTAL {total}')
    print(f'ERRORS {errors}')


if __name__ == '__main__':
    main()
