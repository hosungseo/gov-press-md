# gov-press-md

정부 보도자료를 API로 수집해 Markdown 아카이브로 정리하는 프로젝트.

## 무엇을 만드는가
- 정책브리핑 보도자료 API(XML + HTML 혼합 응답)를 재사용 가능한 Markdown으로 변환
- 날짜별 / 부처별 탐색이 가능한 정적 아카이브 구축
- 검색, 요약, 비교, 브리핑, 에이전트 스킬의 기반 데이터셋 제공

## 현재 포함된 것
- 날짜 범위 수집 스크립트
- 날짜별 Markdown 파일 생성 (`1건 1파일`)
- 일자별 `README.md` 인덱스
- 부처별 인덱스 문서 생성
- 2026-04-01 ~ 2026-04-08 수집 데이터

## 디렉터리 구조
```text
gov-press-md/
  README.md
  data/
    2026/
      2026-04/
        2026-04-01/
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

## Markdown 파일 형식
각 보도자료 문서에는 다음 정보가 들어감.
- 제목
- 부처
- 배포일
- `NewsItemId`
- `GroupingCode`
- 원문 링크
- 첨부/본문 링크 수 (`attachment_count`)
- 본문 정리본
- 출처

## 문서 인덱스
- 전체 부처 인덱스: `docs/ministry-index.md`
- 부처별 상세 목록: `docs/ministries/*.md`
- 일자별 목록: `data/YYYY/YYYY-MM/YYYY-MM-DD/README.md`

## 다음 우선순위
1. GitHub Actions로 일일 수집 자동화
2. 첨부파일 메타데이터 / 보도자료 유형 필드 확장
3. 검색용 경량 JSON 인덱스 생성
4. 부처명 정규화 사전 도입
