import sys
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from PIL import Image, ImageDraw, ImageFilter
from brand import font, wrap

W, H = 1080, 1350
THEME = {"navy": (30, 58, 138), "mark": (67, 224, 160), "accent": (255, 214, 0),
         "ink": (25, 25, 28), "bg": (250, 250, 248), "gray": (120, 120, 126), "line": (205, 214, 232)}
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../assets/poses/")

def pose(name, h):
    im = Image.open(P + name + "_c.png").convert("RGBA")
    return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)

def rich_center(d, y, text, f, lh, base, hl=None, mark=None):
    """'*강조*' 를 hl 색으로, mark 가 있으면 형광펜 밑줄"""
    for line in text.split("\n"):
        segs = [(p, i % 2 == 1) for i, p in enumerate(line.split("*")) if p]
        w = sum(d.textlength(p, font=f) for p, _ in segs)
        x = (W - w) / 2
        for p, h in segs:
            tw = d.textlength(p, font=f)
            if h and mark:
                d.rectangle((x - 4, y + lh * 0.48, x + tw + 4, y + lh * 0.86), fill=mark)
            d.text((x, y), p, font=f, fill=(hl if (h and hl) else base))
            x += tw
        y += lh
    return y

def person(d, x, y, s, col):
    d.ellipse((x - s * 0.22, y, x + s * 0.22, y + s * 0.44), fill=col)
    d.rounded_rectangle((x - s * 0.3, y + s * 0.5, x + s * 0.3, y + s * 1.2), radius=int(s * 0.18), fill=col)

def arrow_down(d, cx, top, h, col, w=60):
    d.rectangle((cx - w * 0.25, top, cx + w * 0.25, top + h - w), fill=col)
    d.polygon([(cx - w * 0.7, top + h - w), (cx + w * 0.7, top + h - w), (cx, top + h)], fill=col)

def cover(bg_path, text, sub):
    img = Image.open(bg_path).convert("RGBA")
    # 9:16 렌더에서 4:5 로 크롭
    s = W / img.width; img = img.resize((W, int(img.height * s)))
    top = int(img.height * 0.18); img = img.crop((0, top, W, top + H))
    base = Image.new("RGBA", (W, H), (236, 240, 248, 255)); base.alpha_composite(img); img = base
    grad = Image.new("L", (1, H)); [grad.putpixel((0, y), int(255 * max(0, (y - H * 0.5) / (H * 0.5)) ** 1.3 * 0.9)) for y in range(H)]
    shade = Image.new("RGBA", (W, H), (10, 12, 20, 255)); shade.putalpha(grad.resize((W, H)))
    img.alpha_composite(shade)
    d = ImageDraw.Draw(img)
    d.text((W / 2 - d.textlength("@enbowl_korea", font=font("Medium", 26)) / 2, H - 330), "@enbowl_korea", font=font("Medium", 26), fill=(220, 220, 225))
    y = H - 270
    f = font("ExtraBold", 66)
    for line in text.split("\n"):
        segs = [(p, i % 2 == 1) for i, p in enumerate(line.split("*")) if p]
        w = sum(d.textlength(p, font=f) for p, _ in segs); x = (W - w) / 2
        for p, h in segs:
            d.text((x, y), p, font=f, fill=THEME["accent"] if h else (255, 255, 255), stroke_width=2, stroke_fill=(10, 10, 14))
            x += d.textlength(p, font=f)
        y += 86
    return img.convert("RGB")

def vs_slide():
    img = Image.new("RGB", (W, H), THEME["bg"]); d = ImageDraw.Draw(img)
    rich_center(d, 120, "같은 선수, 같은 볼, 같은 레인.\n그런데 *1구째*와 *72구째*는 같을까요?", font("SemiBold", 44), 64, THEME["ink"], hl=THEME["navy"])
    d.line((W / 2, 330, W / 2, 1000), fill=THEME["line"], width=4)
    a = pose("fresh", 560); b = pose("tired", 560)
    img.paste(a, (int(W * 0.27 - a.width / 2), 380), a); img.paste(b, (int(W * 0.73 - b.width / 2), 380), b)
    for x, t in ((W * 0.27, "1구째"), (W * 0.73, "72구째")):
        f = font("Bold", 40); d.text((x - d.textlength(t, font=f) / 2, 960), t, font=f, fill=THEME["gray"])
    d.ellipse((W / 2 - 62, 600, W / 2 + 62, 724), fill=THEME["navy"])
    f = font("Black", 54); d.text((W / 2 - d.textlength("VS", font=f) / 2, 628), "VS", font=f, fill=(255, 255, 255))
    rich_center(d, 1090, "던질수록 몸은\n어떻게 달라질까요?", font("ExtraBold", 62), 84, THEME["navy"])
    return img

def study_slide():
    img = Image.new("RGB", (W, H), THEME["bg"]); d = ImageDraw.Draw(img)
    y = rich_center(d, 110, "한 연구에서는\n덴마크 남자 국가대표 6명을 대상으로", font("Medium", 44), 64, THEME["ink"])
    rich_center(d, y + 20, "*72구를 던지는 동안 온몸에*\n*센서를 달고 측정했습니다.*", font("ExtraBold", 50), 72, THEME["ink"], mark=THEME["mark"])
    cy = 560
    for i in range(3):
        person(d, 150 + i * 70, cy, 80, (190, 190, 196)); person(d, W - 150 - i * 70, cy, 80, (190, 190, 196))
    f = font("Black", 150); t = "6"
    d.text((W / 2 - d.textlength(t, font=f) / 2 - 20, cy - 40), t, font=f, fill=THEME["navy"])
    d.text((W / 2 + d.textlength(t, font=f) / 2 - 10, cy + 60), "명", font=font("Bold", 46), fill=THEME["navy"])
    d.line((120, 780, W - 120, 780), fill=THEME["line"], width=3)
    rich_center(d, 815, "모두 에버리지 200 이상인 국가대표 선수들", font("Medium", 38), 54, THEME["ink"])
    items = [("12구 × 6세트", "모두 스트라이크 시도"), ("센서 17곳", "몸 전체 움직임"), ("레이저 추적", "볼 속도·핀 결과")]
    bw = 290; gap = 25; x0 = (W - bw * 3 - gap * 2) / 2
    for i, (a, b) in enumerate(items):
        x = x0 + i * (bw + gap)
        d.rounded_rectangle((x, 930, x + bw, 1160), radius=28, fill=(255, 255, 255), outline=THEME["line"], width=3)
        d.rounded_rectangle((x, 930, x + bw, 1010), radius=28, fill=THEME["navy"])
        d.rectangle((x, 980, x + bw, 1010), fill=THEME["navy"])
        f = font("Bold", 38); d.text((x + bw / 2 - d.textlength(a, font=f) / 2, 948), a, font=f, fill=(255, 255, 255))
        f = font("Medium", 32); d.text((x + bw / 2 - d.textlength(b, font=f) / 2, 1062), b, font=f, fill=THEME["ink"])
    return img

def result_slide():
    img = Image.new("RGB", (W, H), THEME["bg"]); d = ImageDraw.Draw(img)
    rich_center(d, 110, "세트가 지날수록 릴리스 속도는 떨어졌지만", font("Medium", 42), 60, THEME["ink"])
    rich_center(d, 180, "*점수는 거의 그대로였습니다.*", font("ExtraBold", 54), 76, THEME["navy"])
    px = [(80, "볼 속도", "tired", "↓", "8.37 → 8.07 m/s"), (W / 2 + 15, "핀 결과", "think", "≈", "8.5~9.0개 유지")]
    for x, title, ps, sym, note in px:
        w = W / 2 - 95
        d.rounded_rectangle((x, 330, x + w, 1080), radius=30, fill=(255, 255, 255), outline=THEME["navy"], width=4)
        d.rounded_rectangle((x, 330, x + w, 420), radius=30, fill=THEME["navy"]); d.rectangle((x, 380, x + w, 420), fill=THEME["navy"])
        f = font("Bold", 44); d.text((x + w / 2 - d.textlength(title, font=f) / 2, 350), title, font=f, fill=(255, 255, 255))
        im = pose(ps, 430); img.paste(im, (int(x + w / 2 - im.width / 2), 450), im)
        f = font("Black", 110); col = THEME["navy"] if sym == "↓" else (120, 130, 150)
        if sym == "↓": arrow_down(d, x + w / 2, 890, 120, col, 70)
        else: d.text((x + w / 2 - d.textlength(sym, font=f) / 2, 880), sym, font=f, fill=col)
        f = font("SemiBold", 32); d.text((x + w / 2 - d.textlength(note, font=f) / 2, 1020), note, font=f, fill=THEME["gray"])
    rich_center(d, 1130, "선수들은 속도 대신 *손목과 팔꿈치*로\n레인 변화에 맞췄습니다.", font("SemiBold", 42), 62, THEME["ink"], hl=THEME["navy"])
    return img

def summary_slide():
    img = Image.new("RGB", (W, H), THEME["bg"]); d = ImageDraw.Draw(img)
    rich_center(d, 100, "후반 게임에서 볼 반응이 달라진다면", font("Medium", 42), 60, THEME["ink"])
    tips = ["손목·전완 훈련으로 회전 컨트롤 키우기", "볼 교체도 함께 실험해 보기", "손목 부상(건초염) 관리 챙기기"]
    y = 200
    for t in tips:
        d.rounded_rectangle((110, y, W - 110, y + 96), radius=22, fill=THEME["navy"])
        f = font("Bold", 38); d.text((W / 2 - d.textlength(t, font=f) / 2, y + 26), t, font=f, fill=(255, 255, 255)); y += 116
    rich_center(d, y + 30, "속도가 떨어져도\n*손이 답을 찾습니다.*", font("ExtraBold", 66), 88, THEME["navy"], mark=THEME["mark"])
    im = pose("cheer", 470); img.paste(im, (int(W / 2 - im.width / 2), H - 470 - 60), im)
    f = font("Regular", 22); src = "출처: Seiferheld et al. (2023), Sensors 23(19), 8284"
    d.text((W / 2 - d.textlength(src, font=f) / 2, H - 50), src, font=f, fill=THEME["gray"])
    return img

if __name__ == "__main__":
    import os
    os.makedirs("out", exist_ok=True)
    cover("/home/claude/b3d/cover_bg.png", "국가대표도 *72구째*엔\n볼이 느려질까?", "").save("out/01.jpg", quality=92)
    vs_slide().save("out/02.jpg", quality=92)
    study_slide().save("out/03.jpg", quality=92)
    result_slide().save("out/04.jpg", quality=92)
    summary_slide().save("out/05.jpg", quality=92)
