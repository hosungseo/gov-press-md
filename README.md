# gov-press-md

정책브리핑 보도자료를 **Markdown 기반 공개 문서 DB**로 수집, 정리, 버전관리하는 저장소입니다.

이 저장소는 앱이 아니라 **데이터 레이어**입니다. 보도자료 1건을 1개 Markdown 파일로 저장하고, 날짜별 및 부처별 인덱스를 함께 생성해 검색, 요약, 브리핑, 에이전트 처리의 기반 코퍼스로 사용합니다.

## 현재 상태
- 커버 범위: **2020-01-01 ~ 2026-04-30**
- 총 레코드: **165,938건**
- 날짜 디렉터리: **2,287일**
- `news_item_id` 중복 그룹: **0개**
- 공개 품질 리포트: `docs/quality/quality-report.md`

## 이 저장소가 하는 일
- 정책브리핑 보도자료를 `1 파일 = 1 레코드` 구조로 보존
- 날짜별 `README.md` 인덱스 생성
- 부처별 browse index 생성
- AI와 사람이 함께 읽기 쉬운 문서 코퍼스 제공
- 상위 리더 프로젝트 `ai-readable-government`의 source layer 역할 수행

## 연결된 저장소
- `gov-press-md`: 보도자료 문서 DB
- `gov-gazette-md`: 관보 문서 DB
- `ai-readable-government`: 위 두 DB를 읽는 리더/UI

즉 구조는 다음과 같습니다.

> `gov-press-md` / `gov-gazette-md` = source repositories
> `ai-readable-government` = public reader

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
    quality/
  scripts/
    fetch_press_releases.py
    build_day_index.py
    build_ministry_index.py
    build_quality_report.py
    normalize_html.py
```

## 레코드 단위
이 저장소에서는 **Markdown 파일 1개가 문서 레코드 1건**입니다.

예:
- `data/2026/2026-04/2026-04-08/001_부처명_제목.md`

이 파일은 사람이 읽는 원문 기록이면서, 동시에 인덱서와 리더가 읽는 데이터 단위입니다.

## 레코드에 담기는 정보
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

## 인덱스와 파생 산출물
원본 레코드를 덮어쓰지 않고, browse를 돕는 **materialized view** 성격의 문서를 함께 만듭니다.

- 전체 부처 인덱스: `docs/ministry-index.md`
- 부처별 상세 목록: `docs/ministries/*.md`
- 일자별 목록: `data/YYYY/YYYY-MM/YYYY-MM-DD/README.md`
- 품질 진단 및 manifest: `docs/quality/*`

## 빠른 시작
```bash
cd gov-press-md
python3 scripts/fetch_press_releases.py --start 2026-04-08 --end 2026-04-08
python3 scripts/build_day_index.py
python3 scripts/build_ministry_index.py
python3 scripts/build_quality_report.py
```

## 수집 및 정리 원칙
- 정책브리핑 API는 넓은 날짜 범위에서 오류가 날 수 있어 **일 단위 또는 짧은 구간 수집**을 권장합니다.
- 원문 HTML은 가능한 한 읽기 좋은 본문으로 정제합니다.
- 본문 내 링크는 별도 섹션으로 분리해 보존합니다.
- 중복 제거, 부처명 정규화, `미분류` 축소 같은 품질 작업은 별도 스크립트와 manifest로 추적합니다.

## 알려진 주의점
- 일부 날짜는 upstream 응답 truncation 때문에 salvage 처리 이력이 있습니다.
  - 예: `2020-08-20`, `2020-08-21`
- 부처 인덱스에는 여전히 장기 꼬리(long tail) 성격의 라벨 노이즈가 일부 남아 있습니다.
- 이 저장소는 원문 보존과 공개 browse를 우선하며, 완전한 의미 정규화는 아직 진행 중입니다.

## 왜 git-backed document DB인가
이 저장소는 전통적인 SQL DB는 아니지만, 다음 특성을 갖습니다.
- Git history = 변경 이력
- Markdown 파일 = 레코드
- 인덱스 문서 = browse view
- GitHub repo = 공개 가능한 데이터 저장소

즉 **versioned document store / git-backed content DB**로 이해하면 됩니다.

## 다음 우선순위
1. 일일 수집 자동화
2. 첨부파일 메타데이터와 보도자료 유형 필드 확장
3. 검색용 경량 JSON 인덱스 생성
4. 부처명 정규화 사전과 canonical 정책 보강
