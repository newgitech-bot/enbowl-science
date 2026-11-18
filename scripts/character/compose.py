"""3D 프레임 위에 자막·그래픽을 얹어 릴스 mp4 로 합성."""
import json, sys, subprocess, math
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brand import font, ORANGE, WHITE, DARK, PEACH

FPS = 24; W, H = 1080, 1920; M = 70
AUDIO = sys.argv[4] if len(sys.argv) > 4 else None

def ease(x):
    x = max(0, min(1, x)); return 1 - (1 - x) ** 3

def rich_lines(text):
    """'*강조*' 표시를 (조각, 강조여부) 목록으로"""
    out = []
    for line in text.split("\n"):
        segs = []; hl = False
        for i, part in enumerate(line.split("*")):
            if part: segs.append((part, i % 2 == 1))
        out.append(segs)
    return out

def caption_box(text, size=74):
    f = font("Black", size)
    tmp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines = rich_lines(text)
    lw = [sum(tmp.textlength(p, font=f) for p, _ in l) for l in lines]
    bw = int(max(lw) + 70); lh = int(size * 1.28); bh = lh * len(lines) + 50
    img = Image.new("RGBA", (bw + 8, bh + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((4, 4, bw + 3, bh + 3), fill=(12, 12, 14, 235), outline=(255, 255, 255, 255), width=4)
    y = 26
    for l, w in zip(lines, lw):
        x = (bw - w) / 2 + 4
        for p, hl in l:
            d.text((x, y), p, font=f, fill=ORANGE if hl else WHITE)
            x += d.textlength(p, font=f)
        y += lh
    return img

def chip(text, size=46, bg=ORANGE, fg=WHITE):
    f = font("Bold", size)
    tw = ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(text, font=f)
    img = Image.new("RGBA", (int(tw + 64), size + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius=(size + 40) // 2, fill=bg + (245,))
    d.text((32, 14), text, font=f, fill=fg)
    return img

def paste(frame, im, x, y, k, rise=40):
    if k <= 0: return
    if k < 1:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda a: int(a * k)))
    frame.alpha_composite(im, (int(x), int(y + (1 - k) * rise)))

def outline_text(d, xy, text, f, fill, stroke=8):
    d.text(xy, text, font=f, fill=fill, stroke_width=stroke, stroke_fill=(10, 10, 12))

def make_bg():
    bg = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        k = y / H
        c = tuple(int(a + (b - a) * k) for a, b in zip((226, 233, 244), (250, 250, 252)))
        d.line((0, y, W, y), fill=c + (255,))
    for j, y in enumerate((60, 150, 230)):
        d.rounded_rectangle((-40, y, W + 40, y + 22 - j * 5), radius=10, fill=(255, 255, 255, 255))
    return bg

BG = make_bg()

def rich_draw(d, xy, text, f, lh, base=(22, 22, 24)):
    x0, y = xy
    for segs in rich_lines(text):
        x = x0
        for p, hl in segs:
            d.text((x, y), p, font=f, fill=ORANGE if hl else base)
            x += d.textlength(p, font=f)
        y += lh
    return y

def gauges(fr, g, t, fade):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x0, x1, y0 = 60, W - 130, 1060
    rows = g["rows"]; h = 110 + len(rows) * 104
    d.rounded_rectangle((x0, y0, x1, y0 + h), radius=36, fill=(255, 255, 255, 250))
    d.text((x0 + 44, y0 + 30), g["title"], font=font("Bold", 32), fill=(140, 140, 146))
    for n, r in enumerate(rows):
        y = y0 + 90 + n * 104
        k = ease((t - 0.3 - n * 0.35) / 0.8)
        d.text((x0 + 44, y + 10), r["label"], font=font("Bold", 44), fill=(22, 22, 24))
        bx0, bx1 = x0 + 290, x1 - 190
        d.rounded_rectangle((bx0, y + 20, bx1, y + 52), radius=16, fill=(236, 236, 232))
        v = r["from"] + (r["to"] - r["from"]) * k
        col = tuple(r.get("color", ORANGE))
        d.rounded_rectangle((bx0, y + 20, bx0 + int((bx1 - bx0) * v), y + 52), radius=16, fill=col)
        if k > 0.6:
            d.text((bx1 + 22, y + 8), r["tag"], font=font("Black", 44), fill=col)
    if g.get("note"):
        d.text((x0 + 44, y0 + h - 2), g["note"], font=font("Regular", 28), fill=(255, 255, 255), stroke_width=4, stroke_fill=(20, 20, 24))
    paste(fr, lay, 0, 0, min(fade, ease(t / 0.3)), rise=0)

def summary_card(fr, sm, t):
    k = ease(t / 0.4)
    if k <= 0: return
    x0, x1, y0 = 60, W - 130, 360
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0 + 8, y0 + 14, x1 + 8, 1500 + 14), radius=44, fill=(0, 0, 0, 40))
    d.rounded_rectangle((x0, y0, x1, 1500), radius=44, fill=(255, 255, 255, 255))
    px = x0 + 56; y = y0 + 54
    d.text((px, y), "BOWLING SCIENCE  ·  정리", font=font("Bold", 34), fill=ORANGE); y += 80
    d.text((px, y), "결과", font=font("Bold", 34), fill=(140, 140, 146)); y += 54
    y = rich_draw(d, (px, y), sm["result"], font("ExtraBold", 60), 80) + 36
    d.line((px, y, x1 - 56, y), fill=(230, 230, 228), width=4); y += 44
    d.text((px, y), sm.get("tips_label", "이렇게 해보세요"), font=font("Bold", 34), fill=(140, 140, 146)); y += 64
    paste(fr, lay, 0, (1 - k) * 60, k, rise=0)
    for n, tip in enumerate(sm["tips"]):
        kk = ease((t - 1.6 - n * 0.8) / 0.4)
        if kk <= 0: continue
        tl = Image.new("RGBA", (W, 140), (0, 0, 0, 0)); td = ImageDraw.Draw(tl)
        td.ellipse((px, 4, px + 64, 68), fill=ORANGE)
        nf = font("Black", 36); td.text((px + 32 - td.textlength(str(n + 1), font=nf) / 2, 12), str(n + 1), font=nf, fill=WHITE)
        rich_draw(td, (px + 92, 0), tip, font("Bold", 48), 62)
        paste(fr, tl, 0, y + n * 120, kk, rise=30)
    if t > 1.0:
        sd = ImageDraw.Draw(fr)
        if sm.get("note"):
            sd.text((px, 1356), sm["note"], font=font("Regular", 28), fill=(150, 150, 156))
        sd.text((px, 1400), "출처  " + sm["source"], font=font("Regular", 28), fill=(150, 150, 156))

def render(spec, frames_dir, out):
    caps = [(c["start"], c["end"], caption_box(c["text"])) for c in spec["captions"]]
    chips = [(c["start"], c["end"], chip(c["text"]), c["y"]) for c in spec.get("chips", [])]
    cnt = spec.get("counter")
    n = spec["frames"]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", AUDIO, "-shortest",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        fr = BG.copy()
        src = Path(f"{frames_dir}/{i:04d}.png")
        if not src.exists(): src = Path(f"{frames_dir}/{i-1:04d}.png")
        fr.alpha_composite(Image.open(src).convert("RGBA"))
        d = ImageDraw.Draw(fr)
        # 상단 라벨
        summ = spec["summary"]
        for s, e, im in caps:
            if s <= t < e:
                k = min(ease((t - s) / 0.25), ease((e - t) / 0.2))
                paste(fr, im, (W - im.width) / 2, 270, k, rise=0)
        for s, e, im, y in chips:
            if s <= t < e:
                k = min(ease((t - s) / 0.3), ease((e - t) / 0.2))
                paste(fr, im, M, y, k)
        for lb in spec.get("labels", []):
            if lb["start"] <= t < lb["end"]:
                k = min(ease((t - lb["start"]) / 0.3), ease((lb["end"] - t) / 0.2))
                im = chip(lb["text"], 50, tuple(lb["color"]))
                paste(fr, im, lb["x"] - im.width / 2, lb["y"], k, rise=20)
        g = spec.get("gauges")
        if g and g["start"] <= t < g["end"]:
            gauges(fr, g, t - g["start"], min(1, ease((g["end"] - t) / 0.2)))
        if cnt and cnt["start"] <= t < cnt["end"]:
            k = ease((t - cnt["start"] - 0.3) / 1.6)
            v = cnt["from"] + (cnt["to"] - cnt["from"]) * k
            a = min(ease((t - cnt["start"]) / 0.3), ease((cnt["end"] - t) / 0.2))
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            outline_text(ld, (M, 700), cnt["label"], font("Black", 54), WHITE, 7)
            num = f"{v:.0f}"
            nf = font("Black", 220)
            outline_text(ld, (M - 6, 760), num, nf, ORANGE, 10)
            outline_text(ld, (M + ld.textlength(num, font=nf) + 6, 880), cnt["unit"], font("Black", 90), ORANGE, 8)
            for j, line in enumerate(cnt["note"].split("\n")):
                outline_text(ld, (M, 1020 + j * 58), line, font("Bold", 40), WHITE, 6)
            paste(fr, lay, 0, 0, a, rise=0)
        if t >= summ["start"]:
            summary_card(fr, summ, t - summ["start"])
        p.stdin.write(fr.convert("RGB").tobytes())
        if i == int(1.5 * FPS):
            fr.convert("RGB").save(Path(out).with_name("cover.jpg"), quality=92)
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    render(spec, sys.argv[2], sys.argv[3])
