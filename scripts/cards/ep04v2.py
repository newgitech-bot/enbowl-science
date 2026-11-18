from card2 import *
from PIL import Image, ImageDraw
T = THEME
WHITE = (255, 255, 255)

def base():
    img = Image.new("RGB", (W, H), T["bg"]); return img, ImageDraw.Draw(img)

def footer(d, n):
    f = font("Medium", 22); t = f"@enbowl_korea"
    d.text((W / 2 - d.textlength(t, font=f) / 2, H - 52), t, font=f, fill=(170, 170, 176))

def box(d, x0, y0, x1, y1, title, fill=None):
    d.rounded_rectangle((x0, y0, x1, y1), radius=28, fill=WHITE, outline=T["line"], width=3)
    if title:
        d.rounded_rectangle((x0, y0, x1, y0 + 80), radius=28, fill=fill or T["navy"]); d.rectangle((x0, y0 + 50, x1, y0 + 80), fill=fill or T["navy"])
        f = font("Bold", 36); d.text(((x0 + x1) / 2 - d.textlength(title, font=f) / 2, y0 + 18), title, font=f, fill=WHITE)

def center_text(d, x, y, t, f, col):
    d.text((x - d.textlength(t, font=f) / 2, y), t, font=f, fill=col)

def bubble(d, x, y, w, text):
    f = font("Bold", 34); h = 84
    d.rounded_rectangle((x, y, x + w, y + h), radius=42, fill=WHITE, outline=T["navy"], width=3)
    center_text(d, x + w / 2, y + 22, text, f, T["navy"])

# 3. 궁금증
def s_question():
    img, d = base()
    rich_center(d, 110, "후반 게임만 되면\n볼이 덜 나가는 느낌, 있지 않나요?", font("SemiBold", 46), 66, T["ink"])
    bubble(d, 90, 330, 400, "레인 오일이 변해서?"); bubble(d, W - 490, 330, 400, "힘이 빠져서?")
    bubble(d, W / 2 - 200, 440, 400, "자세가 무너져서?")
    im = pose("think", 560); img.paste(im, (int(W / 2 - im.width / 2), 560), im)
    rich_center(d, 1150, "*기분 탓인지, 진짜인지*\n국가대표 선수들로 확인해 봤습니다.", font("Bold", 46), 66, T["ink"], mark=T["mark"])
    footer(d, 3); return img

# 5. 측정 방법
def s_method():
    img, d = base()
    rich_center(d, 110, "어떻게 측정했을까?", font("ExtraBold", 58), 80, T["navy"])
    rich_center(d, 200, "실제 볼링장에서, 평소처럼 던지는 동안 기록했습니다.", font("Medium", 38), 56, T["ink"])
    im = pose("fresh", 760); x0 = int(W * 0.3 - im.width / 2); y0 = 320
    img.paste(im, (x0, y0), im)
    # 센서 점 (몸 관절 위치 대략)
    pts = [(0.5, 0.12), (0.5, 0.36), (0.12, 0.42), (0.88, 0.42), (0.2, 0.55), (0.8, 0.55), (0.36, 0.62), (0.64, 0.62),
           (0.38, 0.78), (0.62, 0.78), (0.4, 0.95), (0.6, 0.95)]
    for px, py in pts:
        cx, cy = x0 + px * im.width, y0 + py * im.height
        d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=(255, 114, 0), outline=WHITE, width=4)
    items = [("관성 센서 17곳", "온몸 관절 움직임\n초당 240번 기록"), ("압력 깔창", "양발에 실리는 힘\n초당 100번 기록"),
             ("레이저 추적", "볼 속도와\n쓰러진 핀 수")]
    y = 360
    for a, b in items:
        x = W * 0.56
        d.rounded_rectangle((x, y, W - 70, y + 230), radius=26, fill=WHITE, outline=T["line"], width=3)
        d.rounded_rectangle((x, y, x + 16, y + 230), radius=8, fill=T["navy"])
        d.text((x + 40, y + 34), a, font=font("Bold", 40), fill=T["navy"])
        yy = y + 100
        for line in b.split("\n"):
            d.text((x + 40, yy), line, font=font("Medium", 32), fill=T["ink"]); yy += 46
        y += 260
    rich_center(d, 1180, "볼은 각자 쓰던 7.5kg(16파운드) 볼 그대로", font("Medium", 34), 50, T["gray"])
    footer(d, 5); return img

# 6. 속도 그래프
def s_chart():
    img, d = base()
    rich_center(d, 110, "세트가 지날수록", font("Medium", 44), 62, T["ink"])
    rich_center(d, 176, "*릴리스 속도가 꾸준히 떨어졌습니다*", font("ExtraBold", 54), 76, T["navy"], mark=T["mark"])
    vals = [8.37, 8.31, 8.23, 8.14, 8.09, 8.07]; lo, hi = 7.9, 8.4
    top, bottom = 420, 1010; n = len(vals); bw = 110; gap = (W - 160 - bw * n) / (n - 1)
    d.line((80, bottom, W - 80, bottom), fill=T["line"], width=4)
    for i, v in enumerate(vals):
        x = 80 + i * (bw + gap); bh = (v - lo) / (hi - lo) * (bottom - top)
        col = T["navy"] if i in (0, n - 1) else (200, 208, 226)
        d.rounded_rectangle((x, bottom - bh, x + bw, bottom), radius=16, fill=col)
        center_text(d, x + bw / 2, bottom - bh - 52, f"{v:.2f}", font("Bold", 34), T["navy"] if i in (0, n - 1) else T["gray"])
        center_text(d, x + bw / 2, bottom + 16, f"{i + 1}세트", font("Medium", 30), T["gray"])
    d.text((80, 340), "릴리스 속도 (m/s) · 세로축 7.9부터", font=font("Medium", 26), fill=T["gray"])
    rich_center(d, 1110, "1세트보다 *약 0.3 m/s (3.6%)* 느려졌습니다.\n같은 선수, 같은 볼, 같은 레인인데도요.", font("SemiBold", 40), 60, T["ink"], hl=T["navy"])
    footer(d, 6); return img

# 7. 손의 변화
def s_hands():
    img, d = base()
    rich_center(d, 110, "대신 달라진 곳이 있었습니다.", font("Medium", 44), 62, T["ink"])
    rich_center(d, 176, "*바로 손입니다*", font("ExtraBold", 62), 84, T["navy"], mark=T["mark"])
    cols = [("손목", "릴리스 전\n더 많이 굽힘"), ("팔꿈치", "릴리스 전\n더 많이 굽힘"), ("손목 회전", "릴리스 때\n안쪽으로 더 돌림")]
    bw = 290; gap = 25; x0 = (W - bw * 3 - gap * 2) / 2
    for i, (a, b) in enumerate(cols):
        x = x0 + i * (bw + gap)
        box(d, x, 330, x + bw, 830, a)
        # 위로 향하는 화살표
        cx = x + bw / 2
        d.polygon([(cx - 60, 560), (cx + 60, 560), (cx, 450)], fill=T["navy"]); d.rectangle((cx - 22, 560, cx + 22, 640), fill=T["navy"])
        yy = 690
        for line in b.split("\n"):
            center_text(d, cx, yy, line, font("SemiBold", 32), T["ink"]); yy += 46
    d.rounded_rectangle((90, 880, W - 90, 1040), radius=26, fill=(232, 238, 250))
    rich_center(d, 912, "반면 백스윙 꼭대기까지는\n*세트별 차이가 없었습니다.*", font("SemiBold", 40), 58, T["ink"], hl=T["navy"])
    rich_center(d, 1110, "몸 전체가 아니라, 릴리스 순간의\n손 쓰임만 바뀐 셈입니다.", font("Medium", 40), 60, T["ink"])
    footer(d, 7); return img

# 8. 그대로였던 것
def s_same():
    img, d = base()
    rich_center(d, 110, "그런데 결과는", font("Medium", 44), 62, T["ink"])
    rich_center(d, 176, "*거의 그대로였습니다*", font("ExtraBold", 62), 84, T["navy"], mark=T["mark"])
    rows = [("핀 결과", "8.5 ~ 9.0개", "세트별 차이 없음"), ("앞발에 실리는 최대 힘", "체중의 약 1.66배", "세트별 차이 없음"),
            ("몸이 나아가는 속도", "약 2.6 m/s", "세트별 차이 없음")]
    y = 340
    for a, b, c in rows:
        d.rounded_rectangle((90, y, W - 90, y + 170), radius=26, fill=WHITE, outline=T["line"], width=3)
        d.text((130, y + 30), a, font=font("Bold", 38), fill=T["ink"]); d.text((130, y + 92), c, font=font("Medium", 30), fill=T["gray"])
        f = font("ExtraBold", 46); d.text((W - 130 - d.textlength(b, font=f), y + 54), b, font=f, fill=T["navy"])
        f2 = font("Black", 64); d.text((W - 130 - d.textlength(b, font=f) - 80, y + 40), "≈", font=f2, fill=T["mark"])
        y += 195
    im = pose("think", 300); img.paste(im, (int(W / 2 - im.width / 2), 940), im)
    footer(d, 8); return img

# 9. 왜?
def s_why():
    img, d = base()
    rich_center(d, 110, "왜 이런 일이 생겼을까요?", font("ExtraBold", 56), 78, T["navy"])
    rich_center(d, 200, "연구진은 이렇게 해석했습니다.", font("Medium", 38), 56, T["gray"])
    steps = [("1", "던질수록 레인 오일이 변함", "볼과 레인 사이 마찰이 달라짐"),
             ("2", "몸이 먼저 알아채고 적응", "속도를 낮추고 손목·팔꿈치를 더 씀"),
             ("3", "볼에 회전을 더 실어줌", "직선 속도 대신 회전 에너지로 전환")]
    y = 320
    for i, (n, a, b) in enumerate(steps):
        d.rounded_rectangle((100, y, W - 100, y + 190), radius=28, fill=WHITE, outline=T["line"], width=3)
        d.ellipse((140, y + 55, 220, y + 135), fill=T["navy"]); center_text(d, 180, y + 70, n, font("Black", 44), WHITE)
        d.text((260, y + 42), a, font=font("Bold", 42), fill=T["ink"]); d.text((260, y + 108), b, font=font("Medium", 32), fill=T["gray"])
        if i < 2:
            cx = W / 2; d.polygon([(cx - 30, y + 205), (cx + 30, y + 205), (cx, y + 245)], fill=T["mark"])
        y += 260
    rich_center(d, 1140, "속도가 줄어든 건 지친 게 아니라\n*레인 변화에 맞춘 결과*일 수 있습니다.", font("SemiBold", 42), 62, T["ink"], hl=T["navy"])
    footer(d, 9); return img

# 10. 정리 (한계 포함)
def s_summary():
    img, d = base()
    rich_center(d, 90, "그렇다면 우리는?", font("ExtraBold", 56), 78, T["navy"])
    tips = ["후반 게임엔 손목 쓰임부터 점검하기", "손목·전완 훈련으로 회전 컨트롤 키우기", "볼 교체도 함께 실험해 보기", "늘어난 손목 회전, 건초염 관리 챙기기"]
    y = 200
    for t in tips:
        d.rounded_rectangle((100, y, W - 100, y + 92), radius=22, fill=T["navy"])
        center_text(d, W / 2, y + 24, t, font("Bold", 36), WHITE); y += 110
    rich_center(d, y + 30, "속도가 떨어져도\n*손이 답을 찾습니다.*", font("ExtraBold", 62), 84, T["navy"], mark=T["mark"])
    im = pose("cheer", 280); img.paste(im, (int(W / 2 - im.width / 2), 930), im)
    f = font("Regular", 22)
    for i, t in enumerate(["국가대표 6명 대상 현장 연구로, 볼 교체 없이 진행된 결과입니다.",
                           "출처: Seiferheld et al. (2023), Sensors 23(19), 8284"]):
        center_text(d, W / 2, H - 92 + i * 32, t, f, T["gray"])
    return img

if __name__ == "__main__":
    import os
    os.makedirs("ep04", exist_ok=True)
    slides = [cover("/home/claude/b3d/cover_bg.png", "국가대표도 *72구째*엔\n볼이 느려질까?", ""), vs_slide(), s_question(),
              study_slide(), s_method(), s_chart(), s_hands(), s_same(), s_why(), s_summary()]
    for i, s in enumerate(slides, 1):
        s.save(f"ep04/{i:02d}.jpg", quality=92)
    ims = [Image.open(f"ep04/{i:02d}.jpg").resize((324, 405)) for i in range(1, 11)]
    sh = Image.new("RGB", (334 * 5 + 10, 415 * 2 + 10), "white")
    for i, im in enumerate(ims): sh.paste(im, (10 + (i % 5) * 334, 10 + (i // 5) * 415))
    sh.save("ep04_sheet.jpg", quality=90)
