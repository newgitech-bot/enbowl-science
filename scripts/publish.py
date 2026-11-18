#!/usr/bin/env python3
"""posts/EPxx 폴더의 카드(cards/*.jpg)와 caption.txt 를 인스타그램 캐러셀로 게시한다.

GitHub Actions 에서 실행된다. 필요한 환경변수:
  IG_TOKEN        Meta 시스템 사용자 토큰 (Secrets)
  IG_USER_ID      인스타 비즈니스 계정 ID (Secrets)
  GITHUB_REPOSITORY, GITHUB_SHA  (Actions 가 자동 제공)
선택: IG_API_HOST (기본 graph.facebook.com), IG_API_VERSION (기본 v24.0)

사용법: python scripts/publish.py posts/EP03 [--dry-run]
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HOST = os.environ.get("IG_API_HOST", "graph.facebook.com")
VERSION = os.environ.get("IG_API_VERSION", "v24.0")
BASE = f"https://{HOST}/{VERSION}"


def call(method, path, **params):
    params["access_token"] = os.environ["IG_TOKEN"]
    data = urllib.parse.urlencode(params).encode()
    url = f"{BASE}/{path}"
    if method == "GET":
        req = urllib.request.Request(f"{url}?{data.decode()}")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise SystemExit(f"API 오류 {e.code} ({method} {path}): {body}")


def wait_ready(container_id, label):
    for _ in range(30):
        status = call("GET", container_id, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise SystemExit(f"{label} 컨테이너 처리 실패: {status}")
        time.sleep(5)
    raise SystemExit(f"{label} 컨테이너 대기 시간 초과")


def image_urls(post_dir, cards):
    repo = os.environ["GITHUB_REPOSITORY"]
    ref = os.environ.get("GITHUB_SHA", "main")
    rel = post_dir.as_posix()
    return [f"https://raw.githubusercontent.com/{repo}/{ref}/{rel}/cards/{c.name}" for c in cards]


def validate(post_dir):
    cards = sorted((post_dir / "cards").glob("*.jpg"))
    caption = (post_dir / "caption.txt").read_text(encoding="utf-8").strip()
    errors = []
    if not 2 <= len(cards) <= 10:
        errors.append(f"카드 수는 2~10장이어야 합니다 (현재 {len(cards)})")
    if len(caption) > 2200:
        errors.append(f"캡션은 2200자 이하여야 합니다 (현재 {len(caption)})")
    if caption.count("#") > 30:
        errors.append("해시태그는 30개 이하여야 합니다")
    if errors:
        raise SystemExit("\n".join(errors))
    return cards, caption


def publish(post_dir, dry_run=False):
    post_dir = Path(post_dir)
    if (post_dir / "published.json").exists():
        print(f"{post_dir} 는 이미 게시됨, 건너뜀")
        return
    cards, caption = validate(post_dir)
    urls = image_urls(post_dir, cards)
    if dry_run:
        print("검증 통과:", len(urls), "장")
        for u in urls:
            print(" ", u)
        return

    ig = os.environ["IG_USER_ID"]
    children = []
    for i, url in enumerate(urls, 1):
        cid = call("POST", f"{ig}/media", image_url=url, is_carousel_item="true")["id"]
        wait_ready(cid, f"{i}번 카드")
        children.append(cid)
        print(f"{i}/{len(urls)} 업로드 완료")

    parent = call("POST", f"{ig}/media", media_type="CAROUSEL",
                  children=",".join(children), caption=caption)["id"]
    wait_ready(parent, "캐러셀")
    media_id = call("POST", f"{ig}/media_publish", creation_id=parent)["id"]
    link = call("GET", media_id, fields="permalink").get("permalink", "")
    print("게시 완료:", link)

    (post_dir / "published.json").write_text(json.dumps({
        "media_id": media_id,
        "permalink": link,
        "published_at": datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    publish(args[0], dry_run="--dry-run" in sys.argv)
