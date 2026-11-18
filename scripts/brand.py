"""Enbowl 브랜드 공통 요소: 글꼴, 색, 줄바꿈, '/' 모티프."""
from pathlib import Path

from PIL import ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"

ORANGE = (255, 114, 0)
ORANGE_SOFT = (255, 138, 46)
DARK = (17, 18, 20)
DARK_2 = (32, 33, 38)
INK = (22, 22, 24)
BODY = (70, 70, 74)
GRAY = (140, 140, 146)
LINE = (226, 226, 222)
LIGHT = (246, 246, 243)
WHITE = (255, 255, 255)
PEACH = (255, 226, 202)

_cache = {}


def font(weight, size):
    key = (weight, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(str(FONTS / f"Pretendard-{weight}.otf"), size)
    return _cache[key]


def wrap(draw, text, fnt, width):
    """공백 기준 줄바꿈, 긴 단어는 글자 단위로 자름. \\n 은 강제 줄바꿈."""
    lines = []
    for para in str(text).split("\n"):
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


def text_block(draw, xy, text, fnt, fill, width, line_height, align="left"):
    x, y = xy
    for line in wrap(draw, text, fnt, width):
        lx = x
        if align == "center":
            lx = x + (width - draw.textlength(line, font=fnt)) / 2
        draw.text((lx, y), line, font=fnt, fill=fill)
        y += line_height
    return y


def block_height(draw, text, fnt, width, line_height):
    return len(wrap(draw, text, fnt, width)) * line_height


def slash(draw, x, y, h, w, color):
    lean = h * 0.42
    draw.polygon([(x + lean, y), (x + lean + w, y), (x + w, y + h), (x, y + h)], fill=color)
