#!/usr/bin/env python3
"""BOWLING SCIENCE 카드뉴스 렌더러.

posts/EPxx/content.json 을 읽어 1080x1350 JPEG 6장(cards/01.jpg ~ 06.jpg)을 만든다.
사용법: python scripts/render.py posts/EP03
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"

W, H = 1080, 1350
M = 96  # 좌우 여백

ORANGE = (255, 114, 0)
DARK = (17, 18, 20)
INK = (26, 26, 26)
BODY = (58, 58, 58)
GRAY = (130, 130, 130)
LIGHT = (247, 247, 245)
WHITE = (255, 255, 255)


def font(weight, size):
    return ImageFont.truetype(str(FONTS / f"Pretendard-{weight}.otf"), size)


def wrap(draw, text, fnt, width):
    """공백 기준으로 줄바꿈하고, 한 단어가 너무 길면 글자 단위로 자른다. \n 은 강제 줄바꿈."""
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            trial = word if not cur else cur + " " + word
            if draw.textlength(trial, font=fnt) <= width:
                cur = trial
                continue
            if cur:
                lines.append(cur)
            cur = ""
            for ch in word:
                if draw.textlength(cur + ch, font=fnt) <= width:
                    cur += ch
                else:
                    lines.append(cur)
                    cur = ch
        lines.append(cur)
    return lines


def text_block(draw, xy, text, fnt, fill, width, line_height):
    x, y = xy
    for line in wrap(draw, text, fnt, width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += line_height
    return y


def slash(draw, x, y, h, w, color):
    """브랜드 '/' 모티프: 기울어진 평행사변형."""
    lean = h * 0.42
    draw.polygon([(x + lean, y), (x + lean + w, y), (x + w, y + h), (x, y + h)], fill=color)


def header(draw, ep, page, total, dark):
    sub = (150, 150, 150) if dark else GRAY
    draw.text((M, 84), "BOWLING SCIENCE", font=font("Bold", 30), fill=ORANGE)
    label = f"EP.{ep:02d}   {page:02d} / {total:02d}"
    f = font("Medium", 28)
    draw.text((W - M - draw.textlength(label, font=f), 86), label, font=f, fill=sub)


def footer(draw, dark, right=None):
    col = WHITE if dark else INK
    draw.text((M, H - 120), "Enbowl", font=font("ExtraBold", 36), fill=col)
    if right:
        f = font("Medium", 28)
        draw.text((W - M - draw.textlength(right, font=f), H - 112), right, font=f,
                  fill=(150, 150, 150) if dark else GRAY)


def cover(c, total):
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img)
    slash(d, 600, 0, 760, 150, (34, 35, 39))
    header(d, c["ep"], 1, total, dark=True)
    slash(d, M, 380, 70, 22, ORANGE)
    y = text_block(d, (M, 480), c["title"], font("ExtraBold", 92), WHITE, W - 2 * M, 116)
    text_block(d, (M, y + 36), c["subtitle"], font("Medium", 40), (190, 190, 190), W - 2 * M, 60)
    footer(d, dark=True, right="넘겨서 보기 →")
    return img


def content(c, card, idx, total):
    img = Image.new("RGB", (W, H), LIGHT)
    d = ImageDraw.Draw(img)
    header(d, c["ep"], idx, total, dark=False)
    d.text((M - 6, 170), f"{idx - 1:02d}", font=font("Black", 150), fill=ORANGE)
    y = text_block(d, (M, 390), card["heading"], font("Bold", 62), INK, W - 2 * M, 82)
    text_block(d, (M, y + 40), card["body"], font("Regular", 40), BODY, W - 2 * M, 64)
    if card.get("callout"):
        f = font("SemiBold", 38)
        lines = wrap(d, card["callout"], f, W - 2 * M - 130)
        bh = 70 + len(lines) * 56
        top = H - 190 - bh
        d.rounded_rectangle((M, top, W - M, top + bh), radius=28, fill=DARK)
        slash(d, M + 40, top + 36, 44, 14, ORANGE)
        ty = top + 36
        for line in lines:
            d.text((M + 100, ty), line, font=f, fill=WHITE)
            ty += 56
    footer(d, dark=False)
    return img


def outro(c, total):
    o = c["outro"]
    img = Image.new("RGB", (W, H), ORANGE)
    d = ImageDraw.Draw(img)
    slash(d, 620, 560, 790, 150, (255, 134, 36))
    d.text((M, 84), "BOWLING SCIENCE", font=font("Bold", 30), fill=WHITE)
    d.text((M, 300), "정리", font=font("Bold", 36), fill=(255, 225, 200))
    y = text_block(d, (M, 370), o["summary"], font("ExtraBold", 70), WHITE, W - 2 * M, 92)
    d.rectangle((M, y + 40, M + 120, y + 46), fill=WHITE)
    text_block(d, (M, y + 90), o["cta"], font("Medium", 38), WHITE, W - 2 * M, 58)
    d.text((M, H - 250), "Enjoy Bowling.", font=font("Black", 76), fill=WHITE)
    d.text((M, H - 140), "@enbowl_korea", font=font("Medium", 34), fill=(255, 225, 200))
    return img


def render(post_dir):
    post_dir = Path(post_dir)
    c = json.loads((post_dir / "content.json").read_text(encoding="utf-8"))
    total = len(c["cards"]) + 2
    pages = [cover(c, total)]
    pages += [content(c, card, i + 2, total) for i, card in enumerate(c["cards"])]
    pages.append(outro(c, total))
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
