#!/usr/bin/env python3
import argparse
import html
import re
import time
import urllib.request
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


def fetch_day(day: date, service_key: str) -> bytes:
    day_str = day.strftime("%Y%m%d")
    url = f"{API_URL}?serviceKey={service_key}&startDate={day_str}&endDate={day_str}"
    last_err = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=40) as resp:
                return resp.read()
        except Exception as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))
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
        news_id = (item.findtext('NewsItemId') or '').strip()
        title = (item.findtext('Title') or '').strip()
        minister = (item.findtext('MinisterCode') or '').strip()
        approve = (item.findtext('ApproveDate') or '').strip()
        original = (item.findtext('OriginalUrl') or '').strip()
        grouping = (item.findtext('GroupingCode') or '').strip()
        subtitle1 = (item.findtext('SubTitle1') or '').strip()
        subtitle2 = (item.findtext('SubTitle2') or '').strip()
        subtitle3 = (item.findtext('SubTitle3') or '').strip()
        raw_html = item.findtext('DataContents') or ''
        body = clean_html(raw_html)
        links = extract_links(raw_html)
        fname = f"{idx:03d}_{slugify(minister)}_{slugify(title)}.md"
        lines = [
            '---',
            f'title: "{title.replace(chr(34), chr(39))}"',
            f'ministry: "{minister.replace(chr(34), chr(39))}"',
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
        if minister:
            lines.append(f'- 부처: {minister}')
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
        index_lines.append(f'- [{title}]({fname}) — {minister}')
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
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end) if args.end else start

    total = 0
    for d in daterange(start, end):
        xml = fetch_day(d, args.service_key)
        root = ET.fromstring(xml)
        code = root.findtext('./header/resultCode')
        msg = root.findtext('./header/resultMsg')
        if code != '0':
            raise RuntimeError(f'{d.isoformat()}: API {code} {msg}')
        count = write_day(d, root)
        print(f'{d.isoformat()}: {count}')
        total += count
        time.sleep(0.6)
    print(f'TOTAL {total}')


if __name__ == '__main__':
    main()
