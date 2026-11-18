#!/usr/bin/env python3
"""BOWLING SCIENCE 캐러셀 렌더러 (1080x1350 JPEG).

posts/<폴더>/content.json (format: "carousel") 를 읽어 cards/01.jpg ... 와 caption.txt 를 만든다.
사용법: python scripts/render.py posts/2026-11-24-EP04
슬라이드 종류: stats, chart, list, text (형식은 GUIDE.md 참고)
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brand import (BODY, DARK, DARK_2, GRAY, INK, LIGHT, LINE, ORANGE, ORANGE_SOFT, PEACH, WHITE,
                   block_height, font, slash, text_block, wrap)

W, H = 1080, 1350
M = 90
CW = W - 2 * M


def header(d, kind, dark=False):
    d.text((M, 84), "BOWLING SCIENCE", font=font("Bold", 28), fill=ORANGE if not dark else ORANGE)
    x = M + d.textlength("BOWLING SCIENCE", font=font("Bold", 28)) + 18
    f = font("SemiBold", 24)
    tw = d.textlength(kind, font=f)
    d.rounded_rectangle((x, 80, x + tw + 32, 120), radius=20,
                        outline=(80, 80, 86) if dark else LINE, width=2)
    d.text((x + 16, 85), kind, font=f, fill=(170, 170, 176) if dark else GRAY)


def footer(d, dark=False, right=None):
    d.text((M, H - 118), "Enbowl", font=font("ExtraBold", 34), fill=WHITE if dark else INK)
    if right:
        f = font("Medium", 28)
        d.text((W - M - d.textlength(right, font=f), H - 110), right, font=f,
               fill=(160, 160, 166) if dark else GRAY)


def title(d, text, y=170):
    return text_block(d, (M, y), text, font("Bold", 58), INK, CW, 76)


def note(d, text, y):
    return text_block(d, (M, y), text, font("Regular", 34), BODY, CW, 54)


# ---------- 슬라이드 ----------

def cover(c):
    cv = c["cover"]
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img)
    slash(d, 640, 0, 900, 170, DARK_2)
    header(d, c["kind"], dark=True)
    y = 250
    if cv.get("badge"):
        d.text((M - 8, y), cv["badge"], font=font("Black", 210), fill=ORANGE)
        y += 270
    else:
        slash(d, M, y + 120, 70, 22, ORANGE)
        y += 230
    y = text_block(d, (M, y), cv["hook"], font("ExtraBold", 84), WHITE, CW, 106)
    text_block(d, (M, y + 34), cv["sub"], font("Medium", 36), (185, 185, 190), CW, 54)
    footer(d, dark=True, right="넘겨서 보기 →")
    return img


def slide_stats(c, s):
    img = Image.new("RGB", (W, H), LIGHT)
    d = ImageDraw.Draw(img)
    header(d, c["kind"])
    y = title(d, s["title"]) + 40
    n = len(s["items"])
    gap = 22
    avail = H - 200 - y - (90 if s.get("note") else 0)
    ch = min(230, (avail - gap * (n - 1)) // n)
    for it in s["items"]:
        d.rounded_rectangle((M, y, W - M, y + ch), radius=28, fill=WHITE)
        vf = font("Black", 110)
        vx = M + 44
        vy = y + (ch - 120) // 2 - 6
        d.text((vx, vy), it["value"], font=vf, fill=ORANGE)
        ux = vx + d.textlength(it["value"], font=vf) + 8
        d.text((ux, vy + 58), it.get("unit", ""), font=font("Bold", 40), fill=ORANGE)
        lx = M + 400
        lh = block_height(d, it["label"], font("SemiBold", 36), W - M - 40 - lx, 50)
        text_block(d, (lx, y + (ch - lh) // 2), it["label"], font("SemiBold", 36), INK, W - M - 40 - lx, 50)
        y += ch + gap
    if s.get("note"):
        note(d, s["note"], y + 14)
    footer(d)
    return img


def slide_chart(c, s):
    img = Image.new("RGB", (W, H), LIGHT)
    d = ImageDraw.Draw(img)
    header(d, c["kind"])
    y = title(d, s["title"]) + 30
    vals, labels = s["values"], s["labels"]
    top, bottom = y + 190, 1010
    lo = s.get("axis_min", min(vals) * 0.97)
    hi = max(vals)
    if s.get("highlight"):
        hf = font("Black", 96)
        d.text((W - M - d.textlength(s["highlight"], font=hf), y - 6), s["highlight"], font=hf, fill=ORANGE)
        if s.get("highlight_label"):
            f = font("Medium", 28)
            d.text((W - M - d.textlength(s["highlight_label"], font=f), y + 100), s["highlight_label"],
                   font=f, fill=GRAY)
    n = len(vals)
    bw = (CW - 30 * (n - 1)) // n
    d.line((M, bottom, W - M, bottom), fill=(200, 200, 196), width=3)
    for i, (v, lb) in enumerate(zip(vals, labels)):
        x = M + i * (bw + 30)
        bh = (v - lo) / (hi - lo) * (bottom - top - 60) + 30
        last = i == n - 1
        col = ORANGE if (last or i == 0) else (205, 205, 200)
        d.rounded_rectangle((x, bottom - bh, x + bw, bottom), radius=14, fill=col)
        t = f"{v:g}"
        vf = font("Bold", 32)
        d.text((x + (bw - d.textlength(t, font=vf)) / 2, bottom - bh - 46), t, font=vf,
               fill=INK if (last or i == 0) else GRAY)
        lf = font("Medium", 28)
        d.text((x + (bw - d.textlength(lb, font=lf)) / 2, bottom + 16), lb, font=lf, fill=GRAY)
    if s.get("unit"):
        d.text((M, y + 20), s["unit"], font=font("Medium", 26), fill=GRAY)
    if s.get("note"):
        note(d, s["note"], bottom + 80)
    footer(d)
    return img


def slide_list(c, s):
    img = Image.new("RGB", (W, H), LIGHT)
    d = ImageDraw.Draw(img)
    header(d, c["kind"])
    y0 = title(d, s["title"]) + 60
    tx = M + 110
    hf, bf = font("Bold", 48), font("Regular", 34)
    heights = []
    for it in s["items"]:
        h = block_height(d, it["head"], hf, W - M - tx, 62)
        if it.get("body"):
            h += 10 + block_height(d, it["body"], bf, W - M - tx, 50)
        heights.append(max(h, 72))
    note_h = block_height(d, s["note"], font("Regular", 34), CW, 54) + 60 if s.get("note") else 0
    avail = H - 190 - y0 - note_h
    gap = max(48, min(110, (avail - sum(heights)) // max(1, len(heights))))
    y = y0
    for i, (it, h) in enumerate(zip(s["items"], heights), 1):
        d.ellipse((M, y, M + 72, y + 72), fill=ORANGE)
        nf = font("Black", 38)
        t = str(i)
        d.text((M + 36 - d.textlength(t, font=nf) / 2, y + 12), t, font=nf, fill=WHITE)
        y2 = text_block(d, (tx, y + 4), it["head"], hf, INK, W - M - tx, 62)
        if it.get("body"):
            text_block(d, (tx, y2 + 10), it["body"], bf, BODY, W - M - tx, 50)
        y += h + gap
    if s.get("note"):
        d.line((M, y, W - M, y), fill=LINE, width=3)
        note(d, s["note"], y + 34)
    footer(d)
    return img


def slide_text(c, s):
    img = Image.new("RGB", (W, H), LIGHT)
    d = ImageDraw.Draw(img)
    header(d, c["kind"])
    y = title(d, s["title"]) + 50
    bf = font("Regular", 40)
    y = text_block(d, (M, y), s["body"], bf, BODY, CW, 64)
    if s.get("callout"):
        f = font("ExtraBold", 56)
        lines = wrap(d, s["callout"], f, CW - 130)
        bh = 110 + len(lines) * 76
        top = max(y + 70, (y + H - 200 - bh) // 2)
        d.rounded_rectangle((M, top, W - M, top + bh), radius=34, fill=DARK)
        slash(d, M + 50, top + 56, 62, 20, ORANGE)
        ty = top + 52
        for line in lines:
            d.text((M + 124, ty), line, font=f, fill=WHITE)
            ty += 76
    footer(d)
    return img


def outro(c):
    t, src = c["takeaway"], c["source"]
    img = Image.new("RGB", (W, H), ORANGE)
    d = ImageDraw.Draw(img)
    slash(d, 660, 640, 710, 150, ORANGE_SOFT)
    d.text((M, 84), "BOWLING SCIENCE", font=font("Bold", 28), fill=WHITE)
    d.text((M, 200), t.get("label", "지공사 코멘트"), font=font("Bold", 34), fill=PEACH)
    y = text_block(d, (M, 260), t["headline"], font("ExtraBold", 64), WHITE, CW, 84)
    y = text_block(d, (M, y + 24), t["body"], font("Medium", 34), WHITE, CW, 52)
    sf = font("Regular", 24)
    lines = wrap(d, src["citation"], sf, CW - 60)
    bh = 76 + len(lines) * 36
    top = H - 300 - bh
    d.rounded_rectangle((M, top, W - M, top + bh), radius=22, fill=(214, 92, 0))
    d.text((M + 30, top + 22), "출처", font=font("Bold", 24), fill=PEACH)
    ty = top + 58
    for line in lines:
        d.text((M + 30, ty), line, font=sf, fill=WHITE)
        ty += 36
    d.text((M, H - 220), "Enjoy Bowling.", font=font("Black", 72), fill=WHITE)
    d.text((M, H - 118), "@enbowl_korea", font=font("Medium", 32), fill=PEACH)
    return img


SLIDES = {"stats": slide_stats, "chart": slide_chart, "list": slide_list, "text": slide_text}


def render(post_dir):
    post_dir = Path(post_dir)
    c = json.loads((post_dir / "content.json").read_text(encoding="utf-8"))
    pages = [cover(c)] + [SLIDES[s["type"]](c, s) for s in c["slides"]] + [outro(c)]
    out = post_dir / "cards"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.jpg"):
        old.unlink()
    for i, p in enumerate(pages, 1):
        p.save(out / f"{i:02d}.jpg", "JPEG", quality=92)
    (post_dir / "caption.txt").write_text(c["caption"].strip() + "\n", encoding="utf-8")
    print(f"rendered {len(pages)} cards -> {out}")


if __name__ == "__main__":
    render(sys.argv[1])
