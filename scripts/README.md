# scripts

수집/정제/인덱스 생성 스크립트 모음.

## 포함된 스크립트

### `fetch_press_releases.py`
정책브리핑 보도자료 API를 호출해 날짜별 Markdown 문서를 생성합니다.

예시:
```bash
python3 scripts/fetch_press_releases.py --start 2026-04-01 --end 2026-04-08
python3 scripts/fetch_press_releases.py --start 2026-04-08
```

### `build_day_index.py`
`data/YYYY/YYYY-MM/YYYY-MM-DD/README.md`를 재생성합니다.

예시:
```bash
python3 scripts/build_day_index.py
```

### `build_ministry_index.py`
생성된 Markdown을 읽어 `docs/ministry-index.md`와 `docs/ministries/*.md`를 만듭니다.

예시:
```bash
python3 scripts/build_ministry_index.py
```

### `normalize_html.py`
본문 HTML을 읽기 좋은 텍스트로 바꾸고 링크를 추출하는 유틸입니다.

## 권장 실행 순서
```bash
python3 scripts/fetch_press_releases.py --start 2026-04-08
python3 scripts/build_day_index.py
python3 scripts/build_ministry_index.py
```
