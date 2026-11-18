# enbowl-science

@enbowl_korea 의 BOWLING SCIENCE 자동화 저장소. 볼링 논문, 연구, 새 소식을 주 2회 올린다.

- 화요일 19:00 캐러셀, 금요일 19:00 릴스
- Claude 가 전날 밤 소재를 조사해 원고와 결과물을 만들어 PR 로 올린다 (`GUIDE.md`)
- PR 을 확인하고 머지하면, 게시일 19:00 에 GitHub Actions 가 인스타그램에 올린다
- 바로 올리려면 Actions → Publish to Instagram → Run workflow 에 폴더 입력

## 구조
- `posts/YYYY-MM-DD-EPNN/` 원고(`content.json`), 결과물(`cards/` 또는 `reel.mp4`), `caption.txt`, 게시 기록 `published.json`
- `scripts/render.py` 캐러셀, `scripts/reel.py` 릴스, `scripts/publish.py` 게시, `scripts/brand.py` 브랜드 공통
- `sources.md` 사용한 소재 기록

## 수정하는 법
PR 에 코멘트를 남기거나, `content.json` 을 고친 뒤 렌더 스크립트를 다시 실행한다.

## Secrets
`IG_TOKEN` (Meta 시스템 사용자 토큰), `IG_USER_ID`
