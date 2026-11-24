"""EP.06 카드뉴스: 국가대표 볼러 39명의 손목·손 증상 (Lee et al., 2021, Malays Orthop J)
캐릭터: 시바견 볼러 (보라 셔츠, 레몬색 깃) / 색: 플럼 + 레몬 마킹
python scripts/cards/ep06.py posts/2026-11-26-EP06/cards
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import card2
from card2 import W, H, rich_center, font
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../..")
G = os.path.join(ROOT, "assets/gpt/ep06/")
T = {"main": (92, 42, 124), "mark": (255, 226, 84), "accent": (255, 214, 64), "ink": (28, 24, 32),
     "bg": (250, 249, 247), "gray": (124, 118, 130), "line": (222, 212, 232), "soft": (243, 236, 248),
     "light": (196, 182, 210), "red": (224, 76, 70)}
WHITE = (255, 255, 255)
MAXW = W - 120


def base():
    img = Image.new("RGB", (W, H), T["bg"]); return img, ImageDraw.Draw(img)


def footer(d):
    f = font("Medium", 22); t = "@enbowl_korea"
    d.text((W / 2 - d.textlength(t, font=f) / 2, H - 52), t, font=f, fill=(176, 170, 180))


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


# 1. 표지
def s_cover():
    im = Image.open(G + "01_cover.png").convert("RGBA")
    s = W / im.width; im = im.resize((W, int(im.height * s)), Image.LANCZOS)
    top = 40; img = im.crop((0, top, W, top + H))
    grad = Image.new("L", (1, H))
    for y in range(H):
        grad.putpixel((0, y), int(255 * max(0, (y - H * 0.52) / (H * 0.48)) ** 1.2 * 0.92))
    shade = Image.new("RGBA", (W, H), (22, 12, 30, 255)); shade.putalpha(grad.resize((W, H)))
    img.alpha_composite(shade)
    d = ImageDraw.Draw(img)
    ctext(d, W / 2, H - 352, "@enbowl_korea", font("Medium", 26), (226, 220, 232))
    f = font("ExtraBold", 66); y = H - 300
    for line in ["볼링 치고 손목이 아픈 거,", "국가대표도 *3명 중 2명*이었어요"]:
        segs = [(p, i % 2 == 1) for i, p in enumerate(line.split("*")) if p]
        w = sum(d.textlength(p, font=f) for p, _ in segs); assert w <= MAXW, line
        x = (W - w) / 2
        for p, h in segs:
            d.text((x, y), p, font=f, fill=T["accent"] if h else WHITE, stroke_width=2, stroke_fill=(20, 12, 26))
            x += d.textlength(p, font=f)
        y += 88
    ctext(d, W / 2, y + 22, "말레이시아 국가대표 볼러 39명을 진찰한 연구", font("Medium", 32), (230, 224, 236))
    return img.convert("RGB")


# 2. 질문
def s_question():
    img, d = base()
    rc(d, 110, "게임이 끝나면\n볼 쥐는 손의 손목이 시큰한 경우가 있어요", font("SemiBold", 46), 66, T["ink"])
    f = font("Bold", 34)
    for cx, y, t in ((W * 0.27, 300, "많이 던져서?"), (W * 0.73, 300, "그립이 안 맞아서?"), (W / 2, 392, "그냥 피곤해서?")):
        tw = d.textlength(t, font=f)
        d.rounded_rectangle((cx - tw / 2 - 34, y, cx + tw / 2 + 34, y + 76), radius=38, fill=WHITE, outline=T["main"], width=3)
        d.text((cx - tw / 2, y + 18), t, font=f, fill=T["main"])
    paste_c(img, art("02_think", h=560, w=700), W / 2, 500)
    rc(d, 1110, "국가대표 39명의 손을 직접 진찰한\n*연구 결과*가 있어요.", font("Bold", 46), 68, T["ink"], mark=T["mark"])
    footer(d); return img


# 3. 연구 방법
def s_method():
    img, d = base()
    rc(d, 100, "누구를, 어떻게 조사했을까요?", font("ExtraBold", 56), 78, T["main"])
    a = art("03_check", h=430, w=520); img.paste(a, (70, 230), a)
    x0 = 640
    f = font("Black", 170); d.text((x0, 250), "39", font=f, fill=T["main"])
    d.text((x0 + d.textlength("39", font=f) + 10, 360), "명", font=font("Bold", 52), fill=T["main"])
    for i, t in enumerate(["말레이시아 국가대표·상비군", "남자 18명, 여자 21명", "평균 24세, 경력 평균 13.4년"]):
        d.text((x0 - 20, 480 + i * 52), t, font=font("Medium", 31), fill=T["ink"])
    items = [("설문", "손과 팔 증상을\n직접 기록"), ("진찰", "정형외과 손 전문\n의료진이 검사"), ("훈련량", "주 평균 5.2번\n한 번에 2.3시간")]
    bw = 290; gap = 25; xs = (W - bw * 3 - gap * 2) / 2
    for i, (h, b) in enumerate(items):
        x = xs + i * (bw + gap); y = 730
        d.rounded_rectangle((x, y, x + bw, y + 270), radius=28, fill=WHITE, outline=T["line"], width=3)
        d.rounded_rectangle((x, y, x + bw, y + 82), radius=28, fill=T["main"]); d.rectangle((x, y + 50, x + bw, y + 82), fill=T["main"])
        ctext(d, x + bw / 2, y + 18, h, font("Bold", 38), WHITE)
        yy = y + 120
        for line in b.split("\n"):
            ctext(d, x + bw / 2, yy, line, font("Medium", 31), T["ink"]); yy += 46
    d.rounded_rectangle((90, 1050, W - 90, 1190), radius=26, fill=T["soft"])
    rc(d, 1078, "모두 *무거운 볼(6.1~7.0kg)*을 썼어요.\n영상 촬영 없이 진찰 검사로 판단했어요.", font("SemiBold", 36), 52, T["ink"], hl=T["main"])
    footer(d); return img


# 4. 두 손 비교
def s_vs():
    img, d = base()
    rc(d, 100, "손목 증상, 두 손을 비교하면", font("Medium", 44), 62, T["ink"])
    rc(d, 166, "*볼 쥐는 손*에만 몰렸어요", font("ExtraBold", 60), 84, T["main"], mark=T["mark"])
    paste_c(img, art("04_hands", h=470, w=760), W / 2, 300)
    d.line((W / 2, 800, W / 2, 1100), fill=T["line"], width=4)
    for cx, lab, big, n, col in ((W * 0.27, "볼 쥐는 손", "66.7%", "39명 중 26명", T["main"]),
                                 (W * 0.73, "반대 손", "2.6%", "39명 중 1명", T["light"])):
        chip(d, cx, 800, lab, font("Bold", 34), col, WHITE)
        ctext(d, cx, 885, big, font("Black", 120), col)
        ctext(d, cx, 1040, n, font("SemiBold", 34), T["gray"])
    rc(d, 1150, "증상이 있었거나 지금 있는 선수 비율이에요.\n두 손의 차이는 통계적으로 뚜렷했어요.", font("Medium", 34), 50, T["gray"])
    footer(d); return img


# 5. 부위별
def s_sites():
    img, d = base()
    rc(d, 100, "손가락은 어땠을까요?", font("Medium", 44), 62, T["ink"])
    rc(d, 166, "*볼 구멍에 넣는 세 손가락*만 아팠어요", font("ExtraBold", 52), 76, T["main"], mark=T["mark"])
    rows = [("손목", 66.7), ("약지", 43.6), ("중지", 30.8), ("엄지", 20.5), ("팔꿈치", 7.7), ("검지", 0.0), ("새끼손가락", 0.0)]
    x0, x1 = 300, W - 200; y = 330
    d.text((90, 286), "볼 쥐는 쪽, 증상이 있었거나 있는 선수 비율", font=font("Medium", 26), fill=T["gray"])
    for lab, v in rows:
        hot = lab in ("약지", "중지", "엄지")
        d.text((90, y + 14), lab, font=font("Bold", 38), fill=T["ink"] if v else T["gray"])
        d.rounded_rectangle((x0, y, x1, y + 72), radius=18, fill=(238, 234, 242))
        if v:
            d.rounded_rectangle((x0, y, x0 + (x1 - x0) * v / 70, y + 72), radius=18,
                                fill=T["main"] if (hot or lab == "손목") else T["light"])
        t = f"{v:.1f}%" if v else "0명"
        d.text((x1 + 20, y + 14), t, font=font("ExtraBold", 38), fill=T["main"] if v else T["gray"])
        y += 100
    d.rounded_rectangle((90, 1060, W - 90, 1200), radius=26, fill=T["soft"])
    rc(d, 1086, "검지와 새끼손가락은 *0명*이었어요.\n볼을 쥐는 엄지·중지·약지에만 증상이 나왔어요.", font("SemiBold", 36), 52, T["ink"], hl=T["main"])
    footer(d); return img


# 6. 드퀘르뱅 건초염
def s_dq():
    img, d = base()
    rc(d, 100, "진찰에서 가장 많이 나온 진단은", font("Medium", 44), 62, T["ink"])
    rc(d, 166, "*드퀘르뱅 건초염*이었어요", font("ExtraBold", 60), 84, T["main"], mark=T["mark"])
    a = art("06_wrist", h=560, w=520); img.paste(a, (60, 320), a)
    cx = 800
    ctext(d, cx, 400, "53.8%", font("Black", 130), T["main"])
    ctext(d, cx, 570, "39명 중 21명", font("Bold", 42), T["ink"])
    chip(d, cx, 650, "볼 쥐는 손", font("Bold", 32), T["main"], WHITE, h=58)
    d.rounded_rectangle((90, 930, W - 90, 1190), radius=28, fill=WHITE, outline=T["line"], width=3)
    rc(d, 962, "드퀘르뱅 건초염", font("Bold", 40), 58, T["main"])
    rc(d, 1030, "손목 엄지 쪽 힘줄을 감싼 막에\n염증이 생긴 상태예요.", font("Medium", 38), 56, T["ink"])
    footer(d); return img


# 7. 그립
def s_grip():
    img, d = base()
    rc(d, 100, "그렇다면 그립 방식은?", font("Medium", 44), 62, T["ink"])
    rc(d, 166, "*그립에 따른 차이는 없었어요*", font("ExtraBold", 56), 80, T["main"], mark=T["mark"])
    cols = [("핑거팁 그립", "손가락 끝마디까지", "29명", "86.2%", "25명", "65.5%"),
            ("컨벤셔널 그립", "손가락 둘째 마디까지", "10명", "100%", "10명", "70%")]
    bw = 420; xs = [W / 2 - 30 - bw, W / 2 + 30]
    for x, (h, sub, n, p, pn, wr) in zip(xs, cols):
        y = 320
        d.rounded_rectangle((x, y, x + bw, y + 640), radius=30, fill=WHITE, outline=T["line"], width=3)
        d.rounded_rectangle((x, y, x + bw, y + 90), radius=30, fill=T["main"]); d.rectangle((x, y + 56, x + bw, y + 90), fill=T["main"])
        ctext(d, x + bw / 2, y + 20, h, font("Bold", 40), WHITE)
        ctext(d, x + bw / 2, y + 116, f"{sub} · {n}", font("Medium", 28), T["gray"])
        ctext(d, x + bw / 2, y + 190, "증상 있던 선수", font("SemiBold", 32), T["ink"])
        ctext(d, x + bw / 2, y + 240, p, font("Black", 104), T["main"])
        ctext(d, x + bw / 2, y + 370, f"({pn})", font("Medium", 30), T["gray"])
        d.line((x + 40, y + 440, x + bw - 40, y + 440), fill=T["line"], width=3)
        ctext(d, x + bw / 2, y + 470, "손목 증상", font("SemiBold", 32), T["ink"])
        ctext(d, x + bw / 2, y + 520, wr, font("ExtraBold", 72), T["main"])
    f = font("Black", 70); ctext(d, W / 2, 590, "≈", f, T["mark"])
    rc(d, 1030, "두 그립 사이에 통계적으로\n*의미 있는 차이가 나오지 않았어요.*", font("SemiBold", 42), 62, T["ink"], hl=T["main"])
    rc(d, 1170, "컨벤셔널 그립 선수는 10명뿐이라 비교에 한계가 있어요.", font("Medium", 30), 44, T["gray"])
    footer(d); return img


# 8. 아파도 계속
def s_keep():
    img, d = base()
    rc(d, 100, "드퀘르뱅 건초염이 나온 21명 중", font("Medium", 44), 62, T["ink"])
    rc(d, 166, "*11명은 아픈 채로 훈련했어요*", font("ExtraBold", 60), 84, T["main"], mark=T["mark"])
    a = art("08_keep", h=480, w=460); img.paste(a, (70, 320), a)
    rows = [("훈련 중 손목 통증", "11명", "평균 3.0점"), ("훈련 뒤 손목 통증", "9명", "평균 2.38점")]
    y = 330
    for h, n, sc in rows:
        x = 560
        d.rounded_rectangle((x, y, W - 80, y + 220), radius=26, fill=WHITE, outline=T["line"], width=3)
        d.rounded_rectangle((x, y, x + 16, y + 220), radius=8, fill=T["main"])
        d.text((x + 40, y + 30), h, font=font("Bold", 34), fill=T["ink"])
        d.text((x + 40, y + 88), n, font=font("Black", 76), fill=T["main"])
        d.text((x + 40 + d.textlength(n, font=font("Black", 76)) + 20, y + 120), sc, font=font("SemiBold", 32), fill=T["gray"])
        y += 250
    ctext(d, W / 2, 840, "통증 점수: 0점(안 아픔)부터 10점(가장 심함)까지", font("Medium", 28), T["gray"])
    d.rounded_rectangle((90, 920, W - 90, 1100), radius=26, fill=T["soft"])
    rc(d, 950, "약지 통증이 *12개월 넘게* 이어진\n선수도 6명 있었어요.", font("SemiBold", 40), 60, T["ink"], hl=T["main"])
    rc(d, 1140, "가볍게 아파도 날짜와 게임 수를 적어 두세요.", font("Medium", 36), 52, T["ink"])
    footer(d); return img


# 9. 연구진의 해석
def s_why():
    img, d = base()
    rc(d, 100, "왜 손목에 부담이 쌓일까요?", font("ExtraBold", 56), 78, T["main"])
    rc(d, 192, "연구진은 세 가지를 꼽았어요.", font("Medium", 38), 56, T["gray"])
    steps = [("1", "훅을 거는 릴리스", "손목으로 볼에 회전을 거는 동작을 반복해요"),
             ("2", "세 손가락 그립", "엄지·중지·약지로만 무거운 볼을 쥐어요"),
             ("3", "많은 훈련량", "한 번에 2시간 이상, 일주일에 5번 이상 던져요")]
    y = 300
    for n, a, b in steps:
        d.rounded_rectangle((90, y, W - 90, y + 190), radius=28, fill=WHITE, outline=T["line"], width=3)
        d.ellipse((126, y + 55, 206, y + 135), fill=T["main"]); ctext(d, 166, y + 68, n, font("Black", 44), WHITE)
        d.text((240, y + 40), a, font=font("Bold", 42), fill=T["ink"])
        f = font("Medium", 31); assert d.textlength(b, font=f) < W - 90 - 240 - 30, b
        d.text((240, y + 108), b, font=f, fill=T["gray"])
        y += 220
    d.rounded_rectangle((90, 980, W - 90, 1190), radius=26, fill=T["soft"])
    rc(d, 1010, "직접 잰 결과가 아니라 *연구진의 해석*이에요.", font("SemiBold", 38), 56, T["ink"], hl=T["main"])
    rc(d, 1080, "모두 무거운 볼을 써서 볼 무게 비교는 못 했고,\n훈련량에 따른 차이도 분석하지 않았어요.", font("Medium", 32), 48, T["gray"])
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
    y = sec(y, "결과", ["볼 쥐는 손목 증상 66.7% (반대 손 2.6%)", "드퀘르뱅 건초염 소견 53.8% (21명)", "그립 방식에 따른 차이 없음"], T["soft"])
    y = sec(y, "연구 시사점", ["손목 엄지 쪽 통증이 다음 날까지 남으면", "날짜와 게임 수를 적어 두기", "반복되면 훈련량 줄이고 손 전문 진료", "엄지 구멍이 내 손에 맞는지 점검하기"], T["main"])
    y = sec(y, "한계", ["말레이시아 국가대표 39명만 조사", "비교할 일반 볼러 집단 없음", "영상 촬영 없이 진찰과 설문으로 판단"], T["soft"])
    a = art("10_cheer", h=1290 - y - 20, w=360); paste_c(img, a, W / 2, y)
    f = font("Regular", 22)
    ctext(d, W / 2, H - 52, "출처: Lee et al. (2021), Malaysian Orthopaedic Journal, 15(1), 113-118", f, T["gray"])
    return img


SLIDES = [s_cover, s_question, s_method, s_vs, s_sites, s_dq, s_grip, s_keep, s_why, s_summary]

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "ep06"
    os.makedirs(out, exist_ok=True)
    for i, fn in enumerate(SLIDES, 1):
        fn().save(f"{out}/{i:02d}.jpg", quality=92)
    ims = [Image.open(f"{out}/{i:02d}.jpg").resize((324, 405)) for i in range(1, len(SLIDES) + 1)]
    sh = Image.new("RGB", (334 * 5 + 10, 415 * 2 + 10), "white")
    for i, im in enumerate(ims): sh.paste(im, (10 + (i % 5) * 334, 10 + (i // 5) * 415))
    sh.save(os.environ.get("SHEET", "ep06_sheet.jpg"), quality=90)
