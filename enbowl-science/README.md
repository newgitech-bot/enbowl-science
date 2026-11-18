# enbowl-science

@enbowl_korea 의 BOWLING SCIENCE 카드뉴스 자동화 저장소.

- 주 2회 Claude 가 새 에피소드를 만들어 PR 로 올린다 (`GUIDE.md`, `topics.md`).
- PR 을 확인하고 머지하면 GitHub Actions 가 인스타그램에 캐러셀로 게시한다.
- 수정이 필요하면 PR 에 코멘트를 남기거나 `content.json` 을 고친 뒤 `python scripts/render.py posts/EPNN` 을 다시 실행한다.

## 구조
- `posts/EPNN/content.json` 원고, `cards/` 렌더된 카드, `caption.txt` 캡션, `published.json` 게시 기록
- `scripts/render.py` 카드 렌더러 (Pillow, Pretendard)
- `scripts/publish.py` 인스타그램 게시 (Graph API)
- `.github/workflows/publish.yml` main 머지 시 게시, `check.yml` PR 검사

## 필요한 Secrets
- `IG_TOKEN` Meta 시스템 사용자 토큰
- `IG_USER_ID` 인스타그램 계정 ID

## 수동 게시
Actions → Publish to Instagram → Run workflow → 폴더 입력 (예: `posts/EP03`)
