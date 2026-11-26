"""BOWLING SUNDAY 단편 이미지 (1080x1350).
사용법: python scripts/cards/sun.py posts/<폴더>

2026-11-26부터 두 유형을 번갈아 쓴다 (GUIDE 5-1). sun.kind 로 고른다.
속설 검증 (kind "myth"):
  {"kind": "myth", "type": "속설 검증", "myth": "줄 달린 핀 볼링장도\n스트라이크는 똑같이 난다?",
   "verdict": "아니에요" | "반만 맞아요" | "맞아요", "number": "7.1%", "fact": "스트라이크가 덜 났어요",
   "note": "USBC 기계 투구 시험 (2023)", "art": "assets/gpt/sunNN/x.png", "palette": {...}}
이번 주 숙제 (kind "homework"):
  {"kind": "homework", "type": "이번 주 숙제", "title": "*10번 핀*만 10번 노려 보기",
   "for": "10번 핀을 자주 놓치는 볼러", "steps": ["방법 한 줄", "횟수 한 줄", "확인할 것 한 줄"],
   "art": "...", "palette": {...}}
지도서 한 장 (kind "phases"): 동작 단계별 실루엣 + 한 단계 강조 (앤볼 색: 숯색·주황·흰색)
  {"kind": "phases", "type": "지도서 한 장", "no": 2, "title": "...", "phases": [
     {"pose": "push"|"down"|"back"|"release"|"follow", "name": "푸시어웨이", "muscles": "대둔근 · 대퇴사두근", "hi": ["glute"]}, ...],
   "focus": 3, "focus_title": "4 릴리스", "focus_text": "...", "source": "출처 한 줄"}
kind 가 없으면 예전 형식(SUN01):
  {"type": "공감 한 컷", "headline": "*10번 핀* 하나\\n남았을 때", "sub": "...", "art": "assets/gpt/sun01/main.png",
   "palette": {"main": [R,G,B], "mark": [R,G,B]}}
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from card2 import W, H, font, rich_center  # noqa: E402

INK = (25, 25, 28)
GRAY = (120, 120, 126)


def rounded(im, r):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=r, fill=255)
    im = im.convert("RGBA")
    im.putalpha(m)
    return im


VERDICT = {"아니에요": (226, 72, 72), "반만 맞아요": (236, 146, 28), "맞아요": (28, 150, 90)}


def tint(c, a):
    return tuple(int(255 - (255 - v) * a) for v in c)


def label_pill(d, text, main):
    f = font("Bold", 30)
    tw = d.textlength(text, font=f)
    d.rounded_rectangle((W / 2 - tw / 2 - 26, 56, W / 2 + tw / 2 + 26, 108), radius=26, fill=main)
    d.text((W / 2 - tw / 2, 62), text, font=f, fill=(255, 255, 255))


def paste_art(img, root, path, top, size, r=40):
    art = Image.open(root / path).convert("RGB").resize((size, size), Image.LANCZOS)
    art = rounded(art, r)
    img.paste(art, (int((W - size) / 2), int(top)), art)


def brand(d):
    f = font("SemiBold", 26)
    t = "@enbowl_korea"
    d.text(((W - d.textlength(t, font=f)) / 2, H - 46), t, font=f, fill=(170, 170, 176))


def make_myth(spec, root, main, mark):
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    label_pill(d, f"BOWLING SUNDAY · {spec['type']}", main)
    # 속설 (따옴표 박스)
    f = font("Bold", 26)
    d.text(((W - d.textlength("이런 말, 들어 봤죠?", font=f)) / 2, 138), "이런 말, 들어 봤죠?", font=f, fill=GRAY)
    y = rich_center(d, 180, spec["myth"], font("ExtraBold", 64), 82, INK, mark=mark)
    # 판정 도장
    vc = VERDICT.get(spec["verdict"], main)
    fv = font("ExtraBold", 54)
    vw = d.textlength(spec["verdict"], font=fv)
    top = y + 18
    d.rounded_rectangle((W / 2 - vw / 2 - 40, top, W / 2 + vw / 2 + 40, top + 86), radius=18, outline=vc, width=6)
    d.text((W / 2 - vw / 2, top + 6), spec["verdict"], font=fv, fill=vc)
    # 사실 박스 (아래에서부터 배치)
    box_h = 190
    by = H - 80 - box_h
    d.rounded_rectangle((70, by, W - 70, by + box_h), radius=32, fill=tint(main, 0.12))
    fn = font("ExtraBold", 104)
    nw = d.textlength(spec["number"], font=fn)
    d.text((110, by + 26), spec["number"], font=fn, fill=main)
    tx = 110 + nw + 40
    d.text((tx, by + 46), spec["fact"], font=font("Bold", 38), fill=INK)
    d.text((tx, by + 108), spec["note"], font=font("Medium", 28), fill=GRAY)
    # 그림
    a_top = top + 86 + 30
    size = int(min(by - 30 - a_top, W - 160))
    paste_art(img, root, spec["art"], a_top, size)
    brand(d)
    return img


def make_homework(spec, root, main, mark):
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    label_pill(d, f"BOWLING SUNDAY · {spec['type']}", main)
    f = font("SemiBold", 30)
    t = f"이런 볼러에게: {spec['for']}"
    d.text(((W - d.textlength(t, font=f)) / 2, 140), t, font=f, fill=GRAY)
    y = rich_center(d, 192, spec["title"], font("ExtraBold", 66), 84, INK, mark=mark)
    # 단계 (아래에서부터)
    steps = spec["steps"]
    row = 92
    sy = H - 80 - row * len(steps)
    fs = font("Bold", 34)
    for i, st in enumerate(steps):
        yy = sy + i * row
        d.rounded_rectangle((70, yy, W - 70, yy + row - 14), radius=24, fill=tint(main, 0.12))
        d.ellipse((92, yy + 12, 144, yy + 64), fill=main)
        n = str(i + 1)
        fn = font("ExtraBold", 32)
        d.text((118 - d.textlength(n, font=fn) / 2, yy + 18), n, font=fn, fill=(255, 255, 255))
        d.text((170, yy + 18), st, font=fs, fill=INK)
    a_top = y + 26
    size = int(min(sy - 28 - a_top, W - 160))
    paste_art(img, root, spec["art"], a_top, size)
    brand(d)
    return img


def make_phases(spec, root):
    from brand import ORANGE, INK as BINK, GRAY as BGRAY, LIGHT, WHITE, LINE
    import figure
    img = Image.new("RGB", (W, H), LIGHT)
    d = ImageDraw.Draw(img)
    fn = font("ExtraBold", 28)
    d.text((72, 70), "/", font=fn, fill=ORANGE)
    d.text((72 + d.textlength("/ ", font=fn), 70), f"BOWLING SUNDAY · {spec['type']}", font=fn, fill=BINK)
    if spec.get("no"):
        t = f"No.{spec['no']:02d}"
        d.text((W - 72 - d.textlength(t, font=fn), 70), t, font=fn, fill=BGRAY)
    y = 138
    for line in spec["title"].split("\n"):
        d.text((72, y), line, font=font("ExtraBold", 66), fill=BINK)
        y += 86
    phases = spec["phases"]
    n = len(phases)
    gap = 14
    pw = (W - 144 - gap * (n - 1)) / n
    top = y + 34
    ph = 500
    fh = 300 if n <= 4 else 248
    for i, p in enumerate(phases):
        x = 72 + i * (pw + gap)
        on = i == spec.get("focus")
        d.rounded_rectangle((x, top, x + pw, top + ph), radius=20, fill=WHITE,
                            outline=ORANGE if on else LINE, width=5 if on else 2)
        d.text((x + 16, top + 12), str(i + 1), font=font("ExtraBold", 28), fill=ORANGE if on else BGRAY)
        near = (60, 60, 66) if on else (150, 150, 156)
        far = (150, 150, 156) if on else (205, 205, 208)
        xs = [v[0] for v in figure.POSES[p["pose"]].values() if v]
        cx0 = (min(xs) + max(xs)) / 2
        figure.draw(d, p["pose"], x + pw / 2 - cx0 * fh, top + 40, fh, near, far,
                    hi=p.get("hi") if on else None)
        fy = top + 40 + fh + 14
        fnm = font("Bold", 24)
        d.text((x + (pw - d.textlength(p["name"], font=fnm)) / 2, fy), p["name"], font=fnm, fill=BINK if on else BGRAY)
        fm = font("Medium", 19)
        my = fy + 40
        for ml in p["muscles"].split("\n"):
            d.text((x + (pw - d.textlength(ml, font=fm)) / 2, my), ml, font=fm, fill=BINK if on else BGRAY)
            my += 28
    y = top + ph + 34
    d.text((72, y), spec["focus_title"], font=font("ExtraBold", 34), fill=ORANGE)
    y += 54
    for line in spec["focus_text"].split("\n"):
        d.text((72, y), line, font=font("SemiBold", 31), fill=BINK)
        y += 46
    if spec.get("todo"):
        y += 14
        d.line((72, y, W - 72, y), fill=LINE, width=2)
        y += 22
        for line in spec["todo"].split("\n"):
            d.text((72, y), line, font=font("Medium", 28), fill=BINK)
            y += 42
    d.text((72, H - 100), spec["source"], font=font("Medium", 20), fill=BGRAY)
    d.text((72, H - 64), "@enbowl_korea", font=font("SemiBold", 22), fill=BGRAY)
    return img


def make(spec, root):
    pal = spec.get("palette", {})
    if spec.get("kind") == "phases":
        return make_phases(spec, root)
    if spec.get("kind") == "myth":
        return make_myth(spec, root, tuple(pal.get("main", (88, 60, 160))), tuple(pal.get("mark", (255, 220, 90))))
    if spec.get("kind") == "homework":
        return make_homework(spec, root, tuple(pal.get("main", (88, 60, 160))), tuple(pal.get("mark", (255, 220, 90))))
    return make_legacy(spec, root)


def make_legacy(spec, root):
    pal = spec.get("palette", {})
    main = tuple(pal.get("main", (88, 60, 160)))
    mark = tuple(pal.get("mark", (255, 220, 90)))
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)

    # 상단 라벨
    label = f"BOWLING SUNDAY · {spec['type']}"
    f = font("Bold", 30)
    tw = d.textlength(label, font=f)
    d.rounded_rectangle((W / 2 - tw / 2 - 26, 56, W / 2 + tw / 2 + 26, 108), radius=26, fill=main)
    d.text((W / 2 - tw / 2, 62), label, font=f, fill=(255, 255, 255))

    # 헤드라인 (형광펜 마킹)
    y = rich_center(d, 140, spec["headline"], font("ExtraBold", 72), 92, INK, mark=mark)
    if spec.get("sub"):
        y = rich_center(d, y + 6, spec["sub"], font("Medium", 36), 50, GRAY)

    # 그림
    top = int(y + 34)
    size = min(H - top - 60, W - 80)
    art = Image.open(root / spec["art"]).convert("RGB").resize((size, size), Image.LANCZOS)
    art = rounded(art, 44)
    img.paste(art, (int((W - size) / 2), top), art)

    # 하단 브랜드
    f = font("SemiBold", 26)
    t = "@enbowl_korea"
    d.text(((W - d.textlength(t, font=f)) / 2, H - 46), t, font=f, fill=(170, 170, 176))
    return img


if __name__ == "__main__":
    post = Path(sys.argv[1])
    root = Path(__file__).resolve().parent.parent.parent
    spec = json.loads((post / "content.json").read_text(encoding="utf-8"))["sun"]
    make(spec, root).save(post / "image.jpg", quality=92)
    print("저장:", post / "image.jpg")
