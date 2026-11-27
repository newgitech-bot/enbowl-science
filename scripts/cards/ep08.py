"""EP.08 카드뉴스: 짧은 오일 레인의 '마찰 경계' 라인 (Ji et al., 2025, AIP Advances)
캐릭터: 펭귄 볼러 (청록 셔츠, 코랄 깃) / 색: 딥 틸 + 코랄 마킹
python scripts/cards/ep08.py posts/2026-11-30-EP08/cards
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card2 import W, H, rich_center, font
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../..")
G = os.path.join(ROOT, "assets/gpt/ep08/")
T = {"main": (14, 98, 104), "mark": (255, 186, 172), "accent": (255, 176, 156), "ink": (22, 30, 32),
     "bg": (249, 250, 249), "gray": (118, 128, 130), "line": (206, 226, 226), "soft": (230, 243, 242),
     "light": (168, 202, 204), "coral": (238, 112, 92), "wood": (240, 222, 188), "oil": (196, 228, 238)}
WHITE = (255, 255, 255)
MAXW = W - 120


def base():
    img = Image.new("RGB", (W, H), T["bg"]); return img, ImageDraw.Draw(img)


def footer(d):
    f = font("Medium", 22); t = "@enbowl_korea"
    d.text((W / 2 - d.textlength(t, font=f) / 2, H - 52), t, font=f, fill=(170, 178, 180))


def ctext(d, x, y, t, f, col):
    w = d.textlength(t, font=f)
    assert w <= MAXW, f"글자 넘침: {t} ({w:.0f}px)"
    d.text((x - w / 2, y), t, font=f, fill=col)


def rc(d, y, text, f, lh, col, hl=None, mark=None):
    for line in text.split("\n"):
        w = d.textlength(line.replace("*", ""), font=f)
        assert w <= MAXW, f"글자 넘침: {line} ({w:.0f}px)"
    return rich_center(d, y, text, f, lh, col, hl=hl, mark=mark)


def key_white(im):
    im = im.convert("RGBA")
    a = im.convert("L").point(lambda v: 0 if v > 246 else (255 if v < 228 else int((246 - v) / 18 * 255)))
    im.putalpha(a)
    bb = a.getbbox()
    return im.crop(bb) if bb else im


def art(name, h=None, w=None):
    im = key_white(Image.open(G + name + ".png"))
    if h and (not w or im.width * h / im.height <= w):
        return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
    return im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)


def paste_c(img, im, cx, y):
    img.paste(im, (int(cx - im.width / 2), int(y)), im)


def chip(d, cx, y, t, f, fill, col, pad=24, h=60):
    tw = d.textlength(t, font=f)
    d.rounded_rectangle((cx - tw / 2 - pad, y, cx + tw / 2 + pad, y + h), radius=h // 2, fill=fill)
    d.text((cx - tw / 2, y + (h - f.size) / 2 - 4), t, font=f, fill=col)


def lane(d, x0, y0, w, h, oil_frac=35 / 60, band=0.62):
    """위에서 본 레인. 아래가 파울라인, 위가 핀. 가운데 오일 구간(마찰 작음)."""
    d.rectangle((x0, y0, x0 + w, y0 + h), fill=T["wood"])
    oy = y0 + h * (1 - oil_frac)
    bx = w * (1 - band) / 2
    d.rectangle((x0 + bx, oy, x0 + w - bx, y0 + h), fill=T["oil"])
    for i in range(1, 8):
        x = x0 + w * i / 8
        d.line((x, y0, x, y0 + h), fill=(228, 208, 172), width=1)
    d.rectangle((x0 - 14, y0, x0, y0 + h), fill=(150, 158, 160))
    d.rectangle((x0 + w, y0, x0 + w + 14, y0 + h), fill=(150, 158, 160))
    d.line((x0 - 14, y0 + h, x0 + w + 14, y0 + h), fill=T["coral"], width=4)
    cx = x0 + w / 2
    for r, row in enumerate([[0], [-1, 1], [-2, 0, 2], [-3, -1, 1, 3]]):
        for k in row:
            px, py = cx + k * w * 0.075, y0 + 70 - r * 16
            d.ellipse((px - 7, py - 7, px + 7, py + 7), fill=WHITE, outline=T["gray"], width=2)
    return oy, x0 + bx, x0 + w - bx


def curve(d, pts, col, width, dash=False):
    if dash:
        for i in range(0, len(pts) - 1, 2):
            d.line([pts[i], pts[i + 1]], fill=col, width=width)
    else:
        d.line(pts, fill=col, width=width, joint="curve")


def path(x_start, y_start, x_bp, y_bp, x_end, y_end, n=40):
    """출발점에서 경계점까지 거의 곧게, 그 뒤 포켓으로 꺾이는 2차 베지어 비슷한 선."""
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((x_start + (x_bp - x_start) * t, y_start + (y_bp - y_start) * t))
    for i in range(1, n + 1):
        t = i / n
        cx, cy = x_bp, y_bp - (y_bp - y_end) * 0.55
        x = (1 - t) ** 2 * x_bp + 2 * (1 - t) * t * cx + t ** 2 * x_end
        y = (1 - t) ** 2 * y_bp + 2 * (1 - t) * t * cy + t ** 2 * y_end
        pts.append((x, y))
    return pts


# 1. 표지
def s_cover():
    im = Image.open(G + "01_cover.png").convert("RGBA")
    s = W / im.width; im = im.resize((W, int(im.height * s)), Image.LANCZOS)
    top = 30; img = im.crop((0, top, W, top + H))
    grad = Image.new("L", (1, H))
    for y in range(H):
        grad.putpixel((0, y), int(255 * max(0, (y - H * 0.5) / (H * 0.5)) ** 1.1 * 0.93))
    shade = Image.new("RGBA", (W, H), (8, 34, 38, 255)); shade.putalpha(grad.resize((W, H)))
    img.alpha_composite(shade)
    d = ImageDraw.Draw(img)
    ctext(d, W / 2, H - 362, "@enbowl_korea", font("Medium", 26), (214, 230, 230))
    f = font("ExtraBold", 66); y = H - 310
    for line in ["짧은 오일 레인, 어디로 던져야", "실수해도 *덜 빗나갈까요*?"]:
        segs = [(p, i % 2 == 1) for i, p in enumerate(line.split("*")) if p]
        w = sum(d.textlength(p, font=f) for p, _ in segs); assert w <= MAXW, line
        x = (W - w) / 2
        for p, h in segs:
            d.text((x, y), p, font=f, fill=T["accent"] if h else WHITE, stroke_width=2, stroke_fill=(6, 26, 28))
            x += d.textlength(p, font=f)
        y += 88
    ctext(d, W / 2, y + 22, "볼링공 물리 시뮬레이션 연구 (AIP Advances, 2025)", font("Medium", 32), (220, 234, 234))
    return img.convert("RGB")


# 2. 질문
def s_question():
    img, d = base()
    rc(d, 110, "같은 목표를 보고 던졌는데\n어떤 공은 포켓, 어떤 공은 빗나가요", font("SemiBold", 46), 66, T["ink"])
    f = font("Bold", 34)
    for cx, y, t in ((W * 0.29, 300, "손이 흔들려서?"), (W * 0.71, 300, "라인이 문제라서?")):
        tw = d.textlength(t, font=f)
        d.rounded_rectangle((cx - tw / 2 - 34, y, cx + tw / 2 + 34, y + 76), radius=38, fill=WHITE, outline=T["main"], width=3)
        d.text((cx - tw / 2, y + 18), t, font=f, fill=T["main"])
    paste_c(img, art("02_think", h=620, w=720), W / 2, 420)
    rc(d, 1100, "컴퓨터로 공을 굴려서\n*라인마다 계산한 연구*가 있어요.", font("Bold", 46), 68, T["ink"], mark=T["mark"])
    footer(d); return img


# 3. 마찰 기초
def s_friction():
    img, d = base()
    rc(d, 100, "볼링공은 오일 위에서 미끄러지고", font("Medium", 44), 62, T["ink"])
    rc(d, 166, "*마른 곳*에서 꺾여요", font("ExtraBold", 60), 84, T["main"], mark=T["mark"])
    # 옆에서 본 레인 띠
    x0, x1, y = 90, W - 90, 330
    d.rounded_rectangle((x0, y, x1, y + 120), radius=18, fill=T["wood"])
    ox = x0 + (x1 - x0) * 0.58
    d.rounded_rectangle((x0, y, ox, y + 120), radius=18, fill=T["oil"]); d.rectangle((ox - 20, y, ox, y + 120), fill=T["oil"])
    d.line((ox, y - 16, ox, y + 136), fill=T["coral"], width=5)
    ctext(d, (x0 + ox) / 2, y + 40, "오일 구간", font("Bold", 34), T["main"])
    ctext(d, (ox + x1) / 2, y + 40, "마른 구간", font("Bold", 34), (150, 112, 60))
    ctext(d, x0 + 70, y + 140, "파울라인", font("Medium", 26), T["gray"])
    ctext(d, x1 - 40, y + 140, "핀", font("Medium", 26), T["gray"])
    for cx, lab, big, col in ((W * 0.29, "오일 위", "0.04", T["main"]), (W * 0.71, "마른 곳", "0.2", T["coral"])):
        chip(d, cx, 540, lab, font("Bold", 34), col, WHITE)
        ctext(d, cx, 620, "약 " + big, font("Black", 112), col)
    ctext(d, W / 2, 780, "트랙션(볼과 레인 사이 마찰) 값이에요", font("Medium", 32), T["gray"])
    paste_c(img, art("06_slide", h=250, w=520), W / 2, 845)
    d.rounded_rectangle((90, 1110, W - 90, 1250), radius=26, fill=T["soft"])
    rc(d, 1136, "마찰이 *다섯 배쯤* 차이 나서\n공이 마른 곳에 닿으면 꺾이기 시작해요.", font("SemiBold", 36), 52, T["ink"], hl=T["main"])
    footer(d); return img


# 4. 연구 방법
def s_method():
    img, d = base()
    rc(d, 100, "컴퓨터 안에서 공을 던졌어요", font("ExtraBold", 56), 78, T["main"])
    a = art("04_compute", h=380, w=430); img.paste(a, (70, 220), a)
    x0 = 540; y = 236
    for h, b in [("공", "6.8kg, 초속 8m, 회전"), ("출발", "보드 0~39번 × 각도 0~6도"), ("실수", "출발 각도 흔들림 0.1도")]:
        d.text((x0, y), h, font=font("Bold", 34), fill=T["main"])
        d.text((x0 + 92, y + 2), b, font=font("Medium", 31), fill=T["ink"])
        y += 66
    d.text((x0, 446), "(사람의 실수를 표준편차로 넣었어요)", font=font("Medium", 26), fill=T["gray"])
    rc(d, 650, "레인은 두 가지예요", font("Bold", 40), 58, T["ink"])
    bw = 430; gap = 40; xs = (W - bw * 2 - gap) / 2
    for i, (hd, l1, l2, frac, band) in enumerate([("평평한 레인", "12.2m(40피트)까지", "오일을 고르게", 40 / 60, 1.0),
                                                ("짧은 오일 레인", "10.7m(35피트)까지", "오일을 고르지 않게", 35 / 60, 0.62)]):
        x = xs + i * (bw + gap); yy = 730
        d.rounded_rectangle((x, yy, x + bw, yy + 470), radius=28, fill=WHITE, outline=T["line"], width=3)
        d.rounded_rectangle((x, yy, x + bw, yy + 80), radius=28, fill=T["main"]); d.rectangle((x, yy + 50, x + bw, yy + 80), fill=T["main"])
        ctext(d, x + bw / 2, yy + 18, hd, font("Bold", 38), WHITE)
        lane(d, x + 50, yy + 110, 100, 330, oil_frac=frac, band=band)
        for k, t in enumerate((l1, l2)):
            f = font("SemiBold", 27); assert d.textlength(t, font=f) < bw - 205, t
            d.text((x + 185, yy + 200 + k * 44), t, font=f, fill=T["ink"])
    footer(d); return img


# 5. 스트라이크 판정
def s_pocket():
    img, d = base()
    rc(d, 100, "스트라이크 확률은 어떻게 셌을까요?", font("Medium", 44), 62, T["ink"])
    rc(d, 166, "*포켓*에 들어간 공만 셌어요", font("ExtraBold", 60), 84, T["main"], mark=T["mark"])
    cx = W / 2; k = 4.2  # 1cm = 4.2px
    hy = 690  # 헤드핀 중심
    dx, dy = 30.48 / 2 * k, 26.4 * k  # 핀 간격(가로 반 칸, 세로 한 줄)
    d.line((cx, 300, cx, 920), fill=T["light"], width=3)
    d.rectangle((cx + 1.3 * k, hy - 30, cx + 14.0 * k, hy + 200), fill=T["mark"])
    for r in range(4):
        for c in range(r + 1):
            px, py = cx + (c * 2 - r) * dx, hy - r * dy
            d.ellipse((px - 6.05 * k, py - 6.05 * k, px + 6.05 * k, py + 6.05 * k), fill=WHITE, outline=T["ink"], width=3)
    br = 10.85 * k; bx, by = cx + 8 * k, hy + 130
    d.line((bx, by, bx + 10, by + 110), fill=T["main"], width=6)
    d.ellipse((bx - br, by - br, bx + br, by + br), fill=T["main"])
    ctext(d, cx - 190, hy + 100, "레인 가운데", font("Medium", 28), T["gray"])
    d.text((cx + 130, hy + 70), "포켓", font=font("Bold", 34), fill=T["coral"])
    d.text((cx + 130, hy + 114), "가운데에서 1.3~14.0cm 옆", font=font("Medium", 28), fill=T["ink"])
    d.rounded_rectangle((90, 960, W - 90, 1220), radius=28, fill=WHITE, outline=T["line"], width=3)
    rc(d, 990, "미국볼링협회(USBC) 2009년 자료", font("Bold", 36), 54, T["main"])
    rc(d, 1050, "진입각(공이 핀에 들어가는 각도)이\n*6도일 때 스트라이크가 가장 많고*\n2도일 때 가장 적었어요.", font("Medium", 34), 50, T["ink"], hl=T["main"])
    footer(d); return img


# 6. 결과 1
def s_vs():
    img, d = base()
    rc(d, 100, "가장 높은 스트라이크 확률을 비교하면", font("Medium", 44), 62, T["ink"])
    rc(d, 166, "*짧은 오일 레인*이 더 높았어요", font("ExtraBold", 60), 84, T["main"], mark=T["mark"])
    d.line((W / 2, 340, W / 2, 760), fill=T["line"], width=4)
    for cx, lab, sub, big, col in ((W * 0.27, "짧은 오일 레인", "10.7m(35피트)", "89%", T["main"]),
                                   (W * 0.73, "평평한 레인", "12.2m(40피트)", "75%", T["light"])):
        chip(d, cx, 350, lab, font("Bold", 34), col, WHITE)
        ctext(d, cx, 430, sub, font("Medium", 30), T["gray"])
        ctext(d, cx, 500, "약", font("SemiBold", 40), col)
        ctext(d, cx, 560, big, font("Black", 150), col)
    d.rounded_rectangle((90, 800, W - 90, 1000), radius=26, fill=T["soft"])
    rc(d, 828, "평평한 레인은 좋은 출발 조건이\n*좁은 범위*에만 있었어요.", font("SemiBold", 40), 60, T["ink"], hl=T["main"])
    rc(d, 1080, "출발 보드와 각도를 바꿔 가며 계산한 값 중\n가장 높은 값이에요. 계산으로 낸 추정값이라\n통계 검정은 하지 않았어요.", font("Medium", 32), 50, T["gray"])
    footer(d); return img


# 7. 결과 2: 경계 라인
def s_line():
    img, d = base()
    rc(d, 100, "짧은 오일 레인에서 가장 좋은 라인은", font("Medium", 44), 62, T["ink"])
    rc(d, 166, "*마찰 경계*를 따라갔어요", font("ExtraBold", 60), 84, T["main"], mark=T["mark"])
    x0, y0, w, h = 120, 300, 340, 900
    oy, bl, br = lane(d, x0, y0, w, h)
    # 경계선 강조
    d.line((br, oy, br, y0 + h), fill=T["coral"], width=4)
    pts = path(br - 6, y0 + h - 10, br - 10, oy + 10, x0 + w / 2 + 22, y0 + 120)
    curve(d, pts, T["main"], 9)
    bx, by = pts[0]
    d.ellipse((bx - 18, by - 30, bx + 18, by + 6), fill=T["main"])
    tx = 540
    chip(d, tx + 230, 330, "가장 좋은 라인", font("Bold", 34), T["main"], WHITE)
    rc_left = [(font("Black", 84), "28번 보드", T["main"], 420), (font("Bold", 44), "에서 1.8도로 출발", T["ink"], 520)]
    for f, t, col, yy in rc_left:
        d.text((tx, yy), t, font=f, fill=col)
    d.line((tx, 620, W - 90, 620), fill=T["line"], width=3)
    d.rounded_rectangle((tx, 660, tx + 34, 694), radius=6, fill=T["oil"])
    d.text((tx + 50, 656), "마찰이 작은 구간", font=font("SemiBold", 32), fill=T["ink"])
    d.rounded_rectangle((tx, 720, tx + 34, 754), radius=6, fill=T["wood"])
    d.text((tx + 50, 716), "마찰이 큰 구간", font=font("SemiBold", 32), fill=T["ink"])
    d.line((tx, 800, tx + 34, 800), fill=T["coral"], width=5)
    d.text((tx + 50, 778), "두 구간의 경계", font=font("SemiBold", 32), fill=T["coral"])
    d.rounded_rectangle((tx - 20, 880, W - 70, 1150), radius=26, fill=T["soft"])
    for i, t in enumerate(["이 라인은 두 구간의", "*경계와 거의 겹쳤어요.*", "", "그림은 이해를 돕는", "모식도예요."]):
        if not t: continue
        f = font("SemiBold", 34) if i < 2 else font("Medium", 28)
        col = T["ink"] if i < 2 else T["gray"]
        segs = [(p, k % 2 == 1) for k, p in enumerate(t.split("*")) if p]
        x = tx
        for p, hh in segs:
            d.text((x, 910 + i * 46), p, font=f, fill=T["main"] if hh else col)
            x += d.textlength(p, font=f)
    footer(d); return img


# 8. 결과 3: 같은 실수, 다른 결과
def s_spread():
    img, d = base()
    rc(d, 100, "출발 각도가 똑같이 흔들려도", font("Medium", 44), 62, T["ink"])
    rc(d, 166, "*경계 라인*은 덜 빗나갔어요", font("ExtraBold", 60), 84, T["main"], mark=T["mark"])
    rows = [("경계 라인", "28번 보드 · 1.8도", 3, "3cm 안쪽", T["main"]),
            ("다른 라인", "10번 보드 · 3.2도", 8, "8cm까지", T["coral"])]
    y = 330
    for lab, sub, v, t, col in rows:
        d.rounded_rectangle((90, y, W - 90, y + 300), radius=28, fill=WHITE, outline=T["line"], width=3)
        d.text((130, y + 34), lab, font=font("Bold", 42), fill=col)
        d.text((130 + d.textlength(lab, font=font("Bold", 42)) + 20, y + 44), sub, font=font("Medium", 30), fill=T["gray"])
        # 핀 도착 위치 흩어짐
        cx = 360; yy = y + 190; unit = 52
        d.line((130, yy, W - 380, yy), fill=T["line"], width=4)
        d.rounded_rectangle((cx - v * unit / 2, yy - 26, cx + v * unit / 2, yy + 26), radius=26, fill=col)
        for k in (-1, 1):
            xx = cx + k * v * unit / 2
            d.line((xx, yy - 46, xx, yy + 46), fill=col, width=4)
        d.text((W - 330, y + 156), t, font=font("Black", 56), fill=col)
        y += 340
    ctext(d, W / 2, 1010, "핀에 도착하는 위치가 흔들린 폭", font("SemiBold", 34), T["ink"])
    d.rounded_rectangle((90, 1080, W - 90, 1230), radius=26, fill=T["soft"])
    rc(d, 1106, "같은 실수를 해도 라인에 따라\n포켓에서 벗어나는 정도가 *두 배 넘게* 달랐어요.", font("SemiBold", 36), 52, T["ink"], hl=T["main"])
    footer(d); return img


# 9. 연구진의 해석
def s_why():
    img, d = base()
    rc(d, 100, "경계 라인은 왜 실수에 강할까요?", font("ExtraBold", 54), 76, T["main"])
    a = art("09_explain", h=420, w=360); img.paste(a, (60, 230), a)
    cards = [("바깥으로 빠지면", "마찰이 큰 구간을 만나", "일찍 꺾여 돌아와요"),
             ("안쪽으로 빠지면", "마찰이 작은 구간에서", "덜 꺾여요")]
    y = 230
    for h, l1, l2 in cards:
        x = 450
        d.rounded_rectangle((x, y, W - 80, y + 200), radius=26, fill=WHITE, outline=T["line"], width=3)
        d.rounded_rectangle((x, y, x + 16, y + 200), radius=8, fill=T["main"])
        d.text((x + 40, y + 26), h, font=font("Bold", 38), fill=T["main"])
        d.text((x + 40, y + 86), l1, font=font("Medium", 32), fill=T["ink"])
        d.text((x + 40, y + 132), l2, font=font("Medium", 32), fill=T["ink"])
        y += 230
    rc(d, 730, "어느 쪽으로 빠져도 꺾임이 반대로 맞춰져서", font("Medium", 40), 58, T["ink"])
    rc(d, 794, "*핀 앞에서는 흔들림이 줄어들어요*", font("ExtraBold", 52), 76, T["main"], mark=T["mark"])
    d.rounded_rectangle((90, 940, W - 90, 1170), radius=26, fill=T["soft"])
    rc(d, 970, "직접 잰 결과가 아니라 *연구진의 해석*이에요.", font("SemiBold", 36), 54, T["ink"], hl=T["main"])
    rc(d, 1040, "공 한 종류, 한 가지 속도와 회전만 넣었고\n게임 중 오일이 닳는 변화는 넣지 않았어요.", font("Medium", 32), 50, T["gray"])
    footer(d); return img


# 10. 정리
def s_summary():
    img, d = base()
    rc(d, 70, "BOWLING SCIENCE · 정리", font("Bold", 30), 44, T["gray"])
    def sec(y, title, lines, fill):
        d.rounded_rectangle((70, y, W - 70, y + 58 + 50 * len(lines)), radius=24, fill=fill)
        d.text((104, y + 18), title, font=font("Bold", 32), fill=T["main"] if fill != T["main"] else T["mark"])
        for i, t in enumerate(lines):
            f = font("SemiBold", 31); assert d.textlength(t, font=f) < W - 140 - 260, t
            d.text((300, y + 18 + i * 50), t, font=f, fill=WHITE if fill == T["main"] else T["ink"])
        return y + 58 + 50 * len(lines) + 22
    y = 140
    y = sec(y, "결과", ["최고 스트라이크 확률: 짧은 오일 약 89%", "평평한 레인 약 75%", "가장 좋은 라인은 마찰 경계를 따라감", "같은 실수에 흔들림 3cm 안쪽 vs 8cm"], T["soft"])
    y = sec(y, "연구 시사점", ["공이 처음 꺾이는 곳을 보고 경계 찾기", "후보 라인 두 개로 몇 구씩 던져 보고", "핀 도착 위치가 덜 흩어지는 쪽 고르기"], T["main"])
    y = sec(y, "한계", ["실제 투구가 아닌 컴퓨터 계산", "실제 공 궤적과 비교하지 않음", "공 한 종류, 오일 변화 미반영"], T["soft"])
    a = art("10_cheer", h=1290 - y - 20, w=360); paste_c(img, a, W / 2, y)
    f = font("Regular", 22)
    ctext(d, W / 2, H - 52, "출처: Ji et al. (2025), AIP Advances, 15(4), 045222", f, T["gray"])
    return img


SLIDES = [s_cover, s_question, s_friction, s_method, s_pocket, s_vs, s_line, s_spread, s_why, s_summary]

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "ep08"
    os.makedirs(out, exist_ok=True)
    for i, fn in enumerate(SLIDES, 1):
        fn().save(f"{out}/{i:02d}.jpg", quality=92)
    ims = [Image.open(f"{out}/{i:02d}.jpg").resize((324, 405)) for i in range(1, len(SLIDES) + 1)]
    sh = Image.new("RGB", (334 * 5 + 10, 415 * 2 + 10), "white")
    for i, im in enumerate(ims): sh.paste(im, (10 + (i % 5) * 334, 10 + (i // 5) * 415))
    sh.save(os.environ.get("SHEET", "ep08_sheet.jpg"), quality=90)
