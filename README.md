# gov-press-md

정부 보도자료를 **git-backed public document database**처럼 수집·정리하는 저장소입니다.

이 저장소는 앱이 아니라 **데이터 레이어**입니다.
보도자료 1건을 1개 Markdown 파일로 저장하고, 날짜별 / 부처별 인덱스를 함께 생성해
검색·요약·브리핑·에이전트 처리의 기반 DB처럼 사용합니다.

## 저장소 역할
- 정책브리핑 보도자료를 Markdown 레코드로 보존
- 날짜별 / 부처별 browse index 제공
- AI/에이전트가 읽기 좋은 public document DB 역할 수행
- 상위 리더 프로젝트(`ai-readable-government`)에 source layer 제공

## 연결된 제품군
- Press DB: `gov-press-md` (현재 저장소)
- Gazette DB: `gov-gazette-md`
- Reader/UI: `ai-readable-government`

즉 구조는 다음과 같습니다.

> `gov-press-md` / `gov-gazette-md` = git-backed document DB
> `ai-readable-government` = 그 DB를 읽는 public reader

## 현재 포함된 것
- 날짜 범위 수집 스크립트
- 날짜별 Markdown 파일 생성 (`1건 1파일`)
- 일자별 `README.md` 인덱스
- 부처별 인덱스 문서 생성
- 2025년~2026년 누적 수집 데이터

## 디렉터리 구조
```text
gov-press-md/
  README.md
  data/
    YYYY/
      YYYY-MM/
        YYYY-MM-DD/
          README.md
          001_부처명_제목.md
  docs/
    ministry-index.md
    ministries/
  scripts/
    fetch_press_releases.py
    build_ministry_index.py
    build_day_index.py
    normalize_html.py
```

## 파일 = 레코드 규칙
이 저장소에서는 **Markdown 파일 1개를 문서 레코드 1건**으로 취급합니다.

예:
- `data/2026/2026-04/2026-04-08/001_부처명_제목.md`
  - 특정 날짜의 특정 보도자료 1건

이 파일 자체가 사람이 읽는 원문 레코드이면서,
동시에 인덱스 생성기와 리더가 읽는 데이터 단위입니다.

## Markdown 레코드 형식
각 보도자료 파일에는 보통 다음 정보가 들어갑니다.
- 제목
- 부처 (`ministry`)
- 배포일 (`approve_date`)
- `NewsItemId`
- `GroupingCode`
- 원문 링크 (`original_url`)
- 첨부/본문 링크 수 (`attachment_count`)
- 본문 정리본
- 출처 (`source`)

## 인덱스 = materialized view
이 저장소에서 인덱스 파일은 원본 문서를 덮어쓰는 것이 아니라,
원본 레코드를 빠르게 browse하기 위한 **materialized view**처럼 취급합니다.

- 전체 부처 인덱스: `docs/ministry-index.md`
- 부처별 상세 목록: `docs/ministries/*.md`
- 일자별 목록: `data/YYYY/YYYY-MM/YYYY-MM-DD/README.md`

## 빠른 시작
```bash
cd gov-press-md
python3 scripts/fetch_press_releases.py --start 2026-04-08
python3 scripts/build_day_index.py
python3 scripts/build_ministry_index.py
```

## 수집 규칙
- 정책브리핑 보도자료 API는 `3일 초과 범위` 조회 시 오류가 날 수 있어 일 단위 또는 짧은 구간 수집을 권장
- 기본 서비스키는 로컬 실험용으로 스크립트에 들어있지만, 장기적으로는 환경변수/개인키 분리가 바람직
- 원문 HTML은 가능한 한 읽기 좋은 본문으로 정제하고, 본문 내 링크는 `첨부/링크` 섹션으로 분리 저장

## 이 저장소를 DB처럼 쓴다는 뜻
이 저장소는 전통적인 SQL DB는 아니지만, 다음 특성을 가집니다.
- Git history = 변경 이력
- Markdown 파일 = 레코드
- 인덱스 문서 = browse view
- GitHub repo = 공개 가능한 데이터 저장소

즉 **versioned document store / git-backed content DB**로 이해하면 됩니다.

## 다음 우선순위
1. GitHub Actions로 일일 수집 자동화
2. 첨부파일 메타데이터 / 보도자료 유형 필드 확장
3. 검색용 경량 JSON 인덱스 생성
4. 부처명 정규화 사전 도입
