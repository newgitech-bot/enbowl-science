#!/usr/bin/env python3
"""BOWLING SCIENCE 릴스 렌더러 (1080x1920, 30fps, H.264 MP4).

posts/<폴더>/content.json (format: "reel") 의 scenes 를 모션그래픽 영상 reel.mp4 로 만든다.
사용법: python scripts/reel.py posts/2026-11-27-EP07
장면 종류: hook, stat, count, list, statement, outro (형식은 GUIDE.md 참고)

인스타 UI 에 가리지 않도록 내용은 위 260px, 아래 420px, 오른쪽 160px 을 피해서 배치한다.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brand import (BODY, DARK, DARK_2, GRAY, INK, LIGHT, ORANGE, ORANGE_SOFT, PEACH, WHITE,
                   block_height, font, slash, wrap)

W, H, FPS = 1080, 1920, 30
M = 90
CW = W - M - 160          # 오른쪽 아이콘 영역 비우기
TOP, BOTTOM = 300, H - 440
WIPE = 8                  # 장면 전환 프레임 수

THEMES = {
    "dark": (DARK, WHITE, (175, 175, 180)),
    "light": (LIGHT, INK, BODY),
    "orange": (ORANGE, WHITE, PEACH),
}


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


class Text:
    """미리 그려둔 텍스트 덩어리. 등장할 때 아래에서 올라오며 나타난다."""

    def __init__(self, text, fnt, color, width, lh, align="left"):
        tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        lines = wrap(tmp, text, fnt, width)
        self.img = Image.new("RGBA", (width, max(1, len(lines)) * lh + 20), (0, 0, 0, 0))
        d = ImageDraw.Draw(self.img)
        for i, line in enumerate(lines):
            x = 0 if align == "left" else (width - d.textlength(line, font=fnt)) / 2
            d.text((x, i * lh), line, font=fnt, fill=color)
        self.h = len(lines) * lh

    def paste(self, frame, x, y, t):
        k = ease(t / 0.45)
        if k <= 0:
            return
        layer = self.img
        if k < 1:
            layer = self.img.copy()
            layer.putalpha(layer.getchannel("A").point(lambda a: int(a * k)))
        frame.alpha_composite(layer, (int(x), int(y + (1 - k) * 60)))


def base(theme, kind):
    bg, _, _ = THEMES[theme]
    img = Image.new("RGBA", (W, H), bg + (255,))
    d = ImageDraw.Draw(img)
    if theme == "dark":
        slash(d, 620, 0, 1300, 200, DARK_2)
    elif theme == "orange":
        slash(d, 640, 900, 1020, 200, ORANGE_SOFT)
    label_col = WHITE if theme == "orange" else ORANGE
    d.text((M, 190), "BOWLING SCIENCE", font=font("Bold", 38), fill=label_col)
    d.text((M, 242), kind, font=font("Medium", 34), fill=THEMES[theme][2])
    return img


# ---------- 장면 ----------
# 각 장면 함수는 (배경 테마, draw(frame, t)) 를 돌려준다. t 는 장면 시작 후 초.

def sc_hook(s, c):
    big = Text(s["text"], font("ExtraBold", 136), WHITE, CW, 164)
    badge = Text(s.get("badge", ""), font("Black", 230), ORANGE, CW, 250) if s.get("badge") else None
    total = big.h + (badge.h + 30 if badge else 0)
    y0 = (TOP + BOTTOM - total) // 2

    def draw(f, t):
        y = y0
        if badge:
            badge.paste(f, M - 8, y, t)
            y += badge.h + 30
        big.paste(f, M, y, t - (0.25 if badge else 0))
    return "dark", draw


def sc_stat(s, c):
    val = Text(s["value"], font("Black", 230), ORANGE, CW, 250)
    lab = Text(s["label"], font("Bold", 74), INK, CW, 98)
    y0 = (TOP + BOTTOM - val.h - lab.h - 40) // 2

    def draw(f, t):
        val.paste(f, M, y0, t)
        lab.paste(f, M, y0 + val.h + 40, t - 0.3)
    return "light", draw


def sc_count(s, c):
    lab = Text(s["label"], font("Bold", 72), WHITE, CW, 94)
    dec = s.get("decimals", 2)
    y0 = (TOP + BOTTOM - 700) // 2
    dur = s.get("dur", 4)

    def draw(f, t):
        lab.paste(f, M, y0, t)
        k = ease((t - 0.4) / max(0.5, dur - 1.6))
        v = s["from"] + (s["to"] - s["from"]) * k
        if t > 0.3:
            d = ImageDraw.Draw(f)
            txt = f"{v:.{dec}f}"
            nf = font("Black", 300)
            d.text((M - 8, y0 + lab.h + 30), txt, font=nf, fill=ORANGE)
            ux = M + d.textlength(txt, font=nf) + 10
            d.text((ux, y0 + lab.h + 230), s.get("unit", ""), font=font("Bold", 56), fill=ORANGE)
            # 진행 막대
            by = y0 + lab.h + 400
            d.rounded_rectangle((M, by, M + CW, by + 26), radius=13, fill=DARK_2)
            frac = (v - s.get("axis_min", 0)) / (s["from"] - s.get("axis_min", 0))
            d.rounded_rectangle((M, by, M + max(26, int(CW * frac)), by + 26), radius=13, fill=ORANGE)
        if s.get("note"):
            note = sc_count.notes.setdefault(id(s), Text(s["note"], font("Medium", 50), (190, 190, 195), CW, 70))
            note.paste(f, M, y0 + lab.h + 480, t - dur + 1.4)
    return "dark", draw


sc_count.notes = {}


def sc_list(s, c):
    ttl = Text(s["title"], font("ExtraBold", 100), INK, CW, 122)
    items = [Text(it, font("Bold", 66), INK, CW - 120, 84) for it in s["items"]]
    gap = 70
    total = ttl.h + 70 + sum(i.h for i in items) + gap * (len(items) - 1)
    y0 = (TOP + BOTTOM - total) // 2

    def draw(f, t):
        ttl.paste(f, M, y0, t)
        y = y0 + ttl.h + 70
        d = ImageDraw.Draw(f)
        for n, it in enumerate(items):
            tt = t - 0.5 - n * 0.45
            k = ease(tt / 0.45)
            if k > 0:
                r = 40 * k
                cx, cy = M + 40, y + 40
                d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ORANGE)
                if k > 0.6:
                    nf = font("Black", 44)
                    d.text((cx - d.textlength(str(n + 1), font=nf) / 2, cy - 28), str(n + 1), font=nf, fill=WHITE)
            it.paste(f, M + 120, y + 4, tt)
            y += it.h + gap
    return "light", draw


def sc_statement(s, c):
    big = Text(s["text"], font("Black", 170), WHITE, CW, 190)
    sub = Text(s.get("sub", ""), font("SemiBold", 62), PEACH, CW, 84) if s.get("sub") else None
    total = big.h + (sub.h + 50 if sub else 0)
    y0 = (TOP + BOTTOM - total) // 2

    def draw(f, t):
        big.paste(f, M, y0, t)
        if sub:
            sub.paste(f, M, y0 + big.h + 50, t - 0.4)
    return "orange", draw


def sc_outro(s, c):
    lab = Text(s.get("label", "지공사 코멘트"), font("Bold", 50), ORANGE, CW, 66)
    big = Text(s["text"], font("ExtraBold", 108), WHITE, CW, 136)
    src = Text("출처  " + c["source"]["short"], font("Regular", 32), (150, 150, 156), CW, 44)
    y0 = (TOP + BOTTOM - 800) // 2

    def draw(f, t):
        lab.paste(f, M, y0, t)
        big.paste(f, M, y0 + 80, t - 0.2)
        d = ImageDraw.Draw(f)
        k = ease((t - 1.0) / 0.5)
        if k > 0:
            ey = y0 + 80 + big.h + 90
            d.rectangle((M, ey, M + int(140 * k), ey + 8), fill=ORANGE)
        Text_enjoy.paste(f, M, y0 + 80 + big.h + 140, t - 1.2)
        src.paste(f, M, BOTTOM - 20, t - 1.4)
    return "dark", draw


Text_enjoy = None

SCENES = {"hook": sc_hook, "stat": sc_stat, "count": sc_count, "list": sc_list,
          "statement": sc_statement, "outro": sc_outro}


def wipe(frame, k):
    """주황 '/' 띠가 화면을 가로지르는 전환. k: 0~1"""
    d = ImageDraw.Draw(frame)
    x = -900 + k * (W + 1400)
    slash(d, x, 0, H, 700, ORANGE)


def render(post_dir):
    global Text_enjoy
    post_dir = Path(post_dir)
    c = json.loads((post_dir / "content.json").read_text(encoding="utf-8"))
    Text_enjoy = Text("Enjoy Bowling.", font("Black", 110), WHITE, CW, 124)

    plan = []
    for s in c["scenes"]:
        theme, draw = SCENES[s["type"]](s, c)
        plan.append((s.get("dur", 3.5), theme, draw))
    bases = {}
    total_frames = int(sum(p[0] for p in plan) * FPS)

    out = post_dir / "reel.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    frame_no = 0
    for idx, (dur, theme, draw) in enumerate(plan):
        if theme not in bases:
            bases[theme] = base(theme, c["kind"])
        n = int(dur * FPS)
        for i in range(n):
            t = i / FPS
            f = bases[theme].copy()
            draw(f, t)
            # 상단 진행 바
            d = ImageDraw.Draw(f)
            prog = (frame_no + 1) / total_frames
            d.rectangle((0, 0, W, 10), fill=(0, 0, 0, 40) if theme != "dark" else DARK_2)
            d.rectangle((0, 0, int(W * prog), 10), fill=WHITE if theme == "orange" else ORANGE)
            if idx > 0 and i < WIPE:
                wipe(f, 0.5 + i / WIPE / 2)
            if idx < len(plan) - 1 and i >= n - WIPE:
                wipe(f, (i - (n - WIPE)) / WIPE / 2)
            proc.stdin.write(f.convert("RGB").tobytes())
            if i == int(1.6 * FPS) and idx == 0:
                f.convert("RGB").save(post_dir / "cover.jpg", quality=92)
            frame_no += 1
    proc.stdin.close()
    proc.wait()
    (post_dir / "caption.txt").write_text(c["caption"].strip() + "\n", encoding="utf-8")
    print(f"rendered {frame_no / FPS:.1f}s reel -> {out}")


if __name__ == "__main__":
    render(sys.argv[1])
