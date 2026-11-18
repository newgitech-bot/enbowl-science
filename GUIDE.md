# BOWLING SCIENCE 제작 가이드 (자동화 작업용)

@enbowl_korea 에 주 2회 올리는 콘텐츠를 만드는 규칙이다.

| 요일 | 형식 | 게시 시각 | PR 올리는 시점 |
|---|---|---|---|
| 화 | 캐러셀 게시물 (6장, 1080x1350) | 19:00 KST | 월요일 밤 |
| 금 | 릴스 (약 20~25초, 1080x1920) | 19:00 KST | 목요일 밤 |

게시는 GitHub Actions 가 화·금 19:00 에 `publish_date` 가 된 미게시 폴더를 올린다.
PR 이 머지되지 않았으면 게시되지 않는다.

## 1. 소재 찾기
주제는 **볼링 논문, 볼링 연구, 볼링 관련 새 소식**이다. `sources.md` 의 사용 기록과 겹치지 않게 고른다.

- 논문: PubMed, Google Scholar, ISBS Proceedings Archive (commons.nmu.edu/isbs), Sports Biomechanics, Journal of Sports Sciences, Sensors 등. 검색어 예: "ten-pin bowling", "bowling biomechanics", "bowling ball dynamics", "bowling injury".
- 연구·기술: USBC 장비·규정 연구, 볼 모션 연구, 오일 패턴 연구.
- 소식: USBC, PBA, World Bowling, 대한볼링협회, 볼 제조사 신제품·규정 변경. 최근 2주 안 소식 위주.
- 우선순위: 동호인이 바로 써먹을 수 있는 결과가 있는 것 > 숫자가 명확한 것 > 화제성.

## 2. 사실 확인 (가장 중요)
- 원문(초록이 아닌 본문 또는 공식 발표)을 열어 숫자와 결론을 직접 확인한다.
- 숫자는 원문 그대로 쓴다. 반올림하면 원문 값과 함께 확인 가능하게 둔다.
- 통계적으로 유의하지 않은 결과는 "경향", 검정하지 않은 수치는 "(통계 검정 전 수치)" 처럼 표시한다.
- 연구진의 해석과 연구 결과를 구분한다 ("연구진은 ~로 해석했습니다").
- 표본 수가 작으면 캡션이나 본문에 한 번 언급한다.
- 원문의 그림·표·문장을 그대로 옮기지 않는다. 숫자를 우리 디자인으로 다시 그리고, 문장은 새로 쓴다.
- 확인 못 한 내용은 쓰지 않는다.

## 3. 원고 작성
폴더 이름: `posts/YYYY-MM-DD-EPNN` (날짜는 게시일, EP 번호는 직전 번호 + 1, 캐러셀·릴스 공통 번호).
`content.json` 형식은 예시 폴더를 따른다.
- 캐러셀 예시: `posts/2026-11-24-EP04/content.json`
- 릴스 예시: `posts/2026-11-27-EP05/content.json`

### 캐러셀 (format: "carousel")
- cover: badge(가장 센 숫자, 선택), hook(두 줄 안팎), sub(연구 한 줄 소개)
- slides 정확히 4장. 종류:
  - `stats`: 큰 숫자 2~3개 (연구 규모 등)
  - `chart`: 막대 그래프. 축을 0이 아닌 값에서 시작하면 unit 에 "세로축 N부터" 를 적는다
  - `list`: 1~3번 항목 (head 20자 안팎, body 한 줄)
  - `text`: 본문 2~3문장 + callout 한 문장
- takeaway: 지공사 코멘트. headline 두 줄 이내, body 2문장. 현장 적용 위주.
- source: citation(저자, 연도, 제목, 저널), url
- 한 장에 하나의 메시지. 글보다 숫자와 그림을 우선한다.

### 릴스 (format: "reel")
- scenes 5~7개, 총 20~25초. 첫 장면 3초 안에 결론을 던진다.
- 종류: hook, stat, count(숫자가 변하는 장면), list, statement(주황 배경 강조), outro
- 한 장면 글자 수는 30자 이내. 두세 줄로 나눠 크게 보이게 한다.
- source.short 에 짧은 출처 (영상 마지막에 표시)
- 배경음악은 넣지 않는다 (저작권). 무음으로 올린다.

## 4. 렌더링과 검수
- 캐러셀: `python scripts/render.py posts/<폴더>`
- 릴스: `python scripts/reel.py posts/<폴더>` (ffmpeg 필요)
- 결과물을 직접 열어 확인한다. 캐러셀은 6장 모두, 릴스는 각 장면 중간 프레임을 뽑아서 본다.
  - 글자 넘침, 어색한 줄바꿈(한 글자만 다음 줄로), 빈 공간, 겹침이 없어야 한다.
  - 문제 있으면 원고를 줄이거나 고쳐서 다시 렌더링한다.
- `python scripts/publish.py --all --dry-run` 으로 검사한다.

## 5. PR
- 브랜치 `post/epNN`, 제목 `EP.NN (화 캐러셀) <훅>` 또는 `EP.NN (금 릴스) <훅>`.
- PR 본문: 미리보기 이미지(캐러셀 카드, 릴스 장면 캡처), 캡션 전문, 출처 링크, 사실 확인 메모.
- `sources.md` 에 사용 기록 한 줄을 추가한다.
- 머지는 사람이 한다.

## 브랜드 톤
- 존댓말 '~습니다' 체. 쉽고 단정하게. 이모지 쓰지 않는다.
- 슬로건 "Enjoy Bowling." 은 영어 그대로.
- 전문 용어는 처음 나올 때 풀어 쓴다. 독자는 볼링 동호인.
- 캡션: 첫 줄 `BOWLING SCIENCE EP.NN | 논문 리뷰`(또는 연구, 뉴스), 둘째 줄 훅, 본문 3~5줄, 현장 적용 한 줄, 출처, 해시태그 8~12개.
- 해시태그에 항상 `#볼링 #볼링사이언스 #앤볼 #Enbowl #EnjoyBowling` 포함.
