#!/usr/bin/env python3
"""posts/<폴더> 를 인스타그램에 게시한다. content.json 의 format 에 따라
  carousel: cards/*.jpg 를 캐러셀로 (이미지는 GitHub raw URL 로 전달)
  reel:     reel.mp4 를 릴스로 (resumable 업로드로 파일을 직접 전송)
  image:    image.jpg 1장을 단일 이미지 게시물로 (BOWLING SUNDAY)

환경변수: IG_TOKEN, IG_USER_ID (Secrets), GITHUB_REPOSITORY
선택: IMAGE_REF (raw URL 에 쓸 커밋, 기본 GITHUB_SHA 또는 main),
      IG_API_HOST (기본 graph.facebook.com), IG_API_VERSION (기본 v24.0)

사용법:
  python scripts/publish.py posts/2026-11-24-EP04            게시
  python scripts/publish.py posts/2026-11-24-EP04 --dry-run  검사만
  python scripts/publish.py --due                             publish_date 가 지난(당일은 19시 이후) 미게시 폴더 전부
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOST = os.environ.get("IG_API_HOST", "graph.facebook.com")
VERSION = os.environ.get("IG_API_VERSION", "v24.0")
BASE = f"https://{HOST}/{VERSION}"
KST = timezone(timedelta(hours=9))


def _open(req):
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise SystemExit(f"API 오류 {e.code} ({req.get_method()} {req.full_url.split('?')[0]}): {body}")


def call(method, path, **params):
    params["access_token"] = os.environ["IG_TOKEN"]
    data = urllib.parse.urlencode(params)
    url = f"{BASE}/{path}"
    if method == "GET":
        return _open(urllib.request.Request(f"{url}?{data}"))
    return _open(urllib.request.Request(url, data=data.encode(), method="POST"))


def wait_ready(container_id, label, tries=60, delay=5):
    for _ in range(tries):
        res = call("GET", container_id, fields="status_code,status")
        status = res.get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise SystemExit(f"{label} 처리 실패: {res}")
        time.sleep(delay)
    raise SystemExit(f"{label} 대기 시간 초과")


def load(post_dir):
    c = json.loads((post_dir / "content.json").read_text(encoding="utf-8"))
    caption = (post_dir / "caption.txt").read_text(encoding="utf-8").strip()
    errors = []
    if len(caption) > 2200:
        errors.append(f"캡션은 2200자 이하여야 합니다 (현재 {len(caption)})")
    if caption.count("#") > 30:
        errors.append("해시태그는 30개 이하여야 합니다")
    fmt = c.get("format", "carousel")
    if fmt == "carousel":
        cards = sorted((post_dir / "cards").glob("*.jpg"))
        if not 2 <= len(cards) <= 10:
            errors.append(f"카드 수는 2~10장이어야 합니다 (현재 {len(cards)})")
    elif fmt == "image":
        if not (post_dir / "image.jpg").exists():
            errors.append("image.jpg 가 없습니다")
    elif fmt == "reel":
        video = post_dir / "reel.mp4"
        if not video.exists():
            errors.append("reel.mp4 가 없습니다")
        elif video.stat().st_size > 300 * 1024 * 1024:
            errors.append("영상은 300MB 이하여야 합니다")
    else:
        errors.append(f"알 수 없는 format: {fmt}")
    if errors:
        raise SystemExit(f"[{post_dir}]\n" + "\n".join(errors))
    return c, fmt, caption


def publish_carousel(post_dir, caption, dry_run):
    repo = os.environ.get("GITHUB_REPOSITORY", "newgitech-bot/enbowl-science")
    ref = os.environ.get("IMAGE_REF") or os.environ.get("GITHUB_SHA") or "main"
    cards = sorted((post_dir / "cards").glob("*.jpg"))
    urls = [f"https://raw.githubusercontent.com/{repo}/{ref}/{post_dir.as_posix()}/cards/{p.name}" for p in cards]
    if dry_run:
        print(f"캐러셀 {len(urls)}장 검사 통과")
        return None
    ig = os.environ["IG_USER_ID"]
    children = []
    for i, url in enumerate(urls, 1):
        cid = call("POST", f"{ig}/media", image_url=url, is_carousel_item="true")["id"]
        wait_ready(cid, f"{i}번 카드")
        children.append(cid)
        print(f"카드 {i}/{len(urls)} 업로드")
    parent = call("POST", f"{ig}/media", media_type="CAROUSEL", children=",".join(children),
                  caption=caption)["id"]
    wait_ready(parent, "캐러셀")
    return parent


def publish_image(post_dir, caption, dry_run):
    repo = os.environ.get("GITHUB_REPOSITORY", "newgitech-bot/enbowl-science")
    ref = os.environ.get("IMAGE_REF") or os.environ.get("GITHUB_SHA") or "main"
    url = f"https://raw.githubusercontent.com/{repo}/{ref}/{post_dir.as_posix()}/image.jpg"
    if dry_run:
        print("이미지 1장 검사 통과")
        return None
    ig = os.environ["IG_USER_ID"]
    cid = call("POST", f"{ig}/media", image_url=url, caption=caption)["id"]
    wait_ready(cid, "이미지")
    return cid


def publish_reel(post_dir, caption, c, dry_run):
    video = post_dir / "reel.mp4"
    if dry_run:
        print(f"릴스 {video.stat().st_size / 1e6:.1f}MB 검사 통과")
        return None
    ig = os.environ["IG_USER_ID"]
    common = dict(media_type="REELS", caption=caption, share_to_feed="true",
                  thumb_offset=str(c.get("thumb_offset_ms", 1600)))
    # 1) 캐러셀 이미지처럼 GitHub raw URL 을 인스타그램이 직접 가져가게 한다
    repo = os.environ.get("GITHUB_REPOSITORY", "newgitech-bot/enbowl-science")
    ref = os.environ.get("IMAGE_REF") or os.environ.get("GITHUB_SHA") or "main"
    url = f"https://raw.githubusercontent.com/{repo}/{ref}/{video.as_posix()}"
    try:
        cid = call("POST", f"{ig}/media", video_url=url, **common)["id"]
        wait_ready(cid, "릴스(video_url)", tries=120, delay=5)
        print("영상 업로드: video_url 방식")
        return cid
    except SystemExit as e:
        print(f"video_url 방식 실패, 직접 업로드로 재시도: {e}")
    # 2) resumable 업로드로 파일을 직접 전송
    res = call("POST", f"{ig}/media", upload_type="resumable", **common)
    cid, uri = res["id"], res.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{VERSION}/{res['id']}"
    data = video.read_bytes()
    req = urllib.request.Request(uri, data=data, method="POST", headers={
        "Authorization": f"OAuth {os.environ['IG_TOKEN']}",
        "offset": "0",
        "file_size": str(len(data)),
        "Content-Type": "application/octet-stream",
    })
    print("영상 업로드:", _open(req))
    wait_ready(cid, "릴스", tries=120, delay=5)
    return cid


def publish(post_dir, dry_run=False):
    post_dir = Path(post_dir)
    if (post_dir / "published.json").exists():
        print(f"{post_dir}: 이미 게시됨")
        return
    c, fmt, caption = load(post_dir)
    if fmt == "carousel":
        creation = publish_carousel(post_dir, caption, dry_run)
    elif fmt == "image":
        creation = publish_image(post_dir, caption, dry_run)
    else:
        creation = publish_reel(post_dir, caption, c, dry_run)
    if dry_run:
        return
    ig = os.environ["IG_USER_ID"]
    media_id = call("POST", f"{ig}/media_publish", creation_id=creation)["id"]
    link = call("GET", media_id, fields="permalink").get("permalink", "")
    print(f"{post_dir}: 게시 완료 {link}")
    (post_dir / "published.json").write_text(json.dumps({
        "media_id": media_id, "permalink": link, "format": fmt,
        "published_at": datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


PUBLISH_HOUR = 19  # 당일 게시물은 KST 19시 이후에만


def due_posts():
    now = datetime.now(KST)
    today = now.date().isoformat()
    out = []
    for d in sorted(Path("posts").iterdir()):
        cj = d / "content.json"
        if not cj.exists() or (d / "published.json").exists():
            continue
        date = json.loads(cj.read_text(encoding="utf-8")).get("publish_date", "")
        if date and (date < today or (date == today and now.hour >= PUBLISH_HOUR)):
            out.append(d)
    return out


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--due" in sys.argv:
        targets = due_posts()
        print("게시 대상:", [str(t) for t in targets] or "없음")
    elif "--all" in sys.argv:
        targets = [d for d in sorted(Path("posts").iterdir()) if (d / "content.json").exists()
                   and not (d / "published.json").exists()]
    else:
        targets = [Path(args[0])]
    for t in targets:
        publish(t, dry_run=dry)
