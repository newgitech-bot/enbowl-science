import card2, ep04v2
from card2 import *
from PIL import Image, ImageDraw, ImageChops
import os; AI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../assets/ai/")

def rounded(im, r=40):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=r, fill=255)
    im = im.convert("RGBA"); im.putalpha(m); return im

def key_white(im):
    im = im.convert("RGBA"); px = im.load()
    g = im.convert("L")
    a = g.point(lambda v: 0 if v > 246 else (255 if v < 230 else int((246 - v) / 16 * 255)))
    im.putalpha(a); return im

def crop_content(im):
    bb = im.getchannel("A").getbbox(); return im.crop(bb) if bb else im

MAP = {"think": ("think", "round"), "fresh": ("method", "key"), "cheer": ("cheer", "round"), "tired": ("vs", "round")}

def ai_pose(name, h):
    src, mode = MAP.get(name, (name, "round"))
    if name == "think" and h < 400: src, mode = "ok", "round"   # 결과 장의 작은 캐릭터는 OK 포즈
    im = Image.open(AI + src + ".png")
    im = crop_content(key_white(im)) if mode == "key" else rounded(im.convert("RGB"), 48)
    return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)

card2.pose = ai_pose; ep04v2.pose = ai_pose

def vs_ai():
    img = Image.new("RGB", (W, H), THEME["bg"]); d = ImageDraw.Draw(img)
    rich_center(d, 120, "같은 선수, 같은 볼, 같은 레인.\n그런데 *1구째*와 *72구째*는 같을까요?", font("SemiBold", 44), 64, THEME["ink"], hl=THEME["navy"])
    im = rounded(Image.open(AI + "vs.png").convert("RGB"), 48).resize((780, 780), Image.LANCZOS)
    img.paste(im, (int(W / 2 - 390), 290), im)
    for x, t in ((W / 2 - 200, "1구째"), (W / 2 + 200, "72구째")):
        f = font("Bold", 36); tw = d.textlength(t, font=f)
        d.rounded_rectangle((x - tw / 2 - 22, 1000, x + tw / 2 + 22, 1056), radius=28, fill=THEME["navy"])
        d.text((x - tw / 2, 1006), t, font=f, fill=(255, 255, 255))
    rich_center(d, 1110, "던질수록 몸은\n어떻게 달라질까요?", font("ExtraBold", 60), 80, THEME["navy"])
    return img

def cover_ai():
    im = Image.open(AI + "cover.png").convert("RGBA")
    s = W / im.width; im = im.resize((W, int(im.height * s)))
    top = (im.height - H) // 2; im = im.crop((0, top, W, top + H))
    im.save("/tmp/cover_ai_bg.png")
    return cover("/tmp/cover_ai_bg.png", "국가대표도 *72구째*엔\n볼이 느려질까?", "")

if __name__ == "__main__":
    import os
    # cover() 는 9:16 기준 크롭을 하므로, 4:5 이미지는 그대로 쓰도록 우회
    def cover_direct(path, text, sub):
        img = Image.open(path).convert("RGBA")
        grad = Image.new("L", (1, H)); [grad.putpixel((0, y), int(255 * max(0, (y - H * 0.5) / (H * 0.5)) ** 1.3 * 0.9)) for y in range(H)]
        shade = Image.new("RGBA", (W, H), (10, 12, 20, 255)); shade.putalpha(grad.resize((W, H))); img.alpha_composite(shade)
        d = ImageDraw.Draw(img); f = font("ExtraBold", 66); y = H - 270
        d.text((W / 2 - d.textlength("@enbowl_korea", font=font("Medium", 26)) / 2, H - 330), "@enbowl_korea", font=font("Medium", 26), fill=(220, 220, 225))
        for line in text.split("\n"):
            segs = [(p, i % 2 == 1) for i, p in enumerate(line.split("*")) if p]
            w = sum(d.textlength(p, font=f) for p, _ in segs); x = (W - w) / 2
            for p, h in segs:
                d.text((x, y), p, font=f, fill=THEME["accent"] if h else (255, 255, 255), stroke_width=2, stroke_fill=(10, 10, 14)); x += d.textlength(p, font=f)
            y += 86
        return img.convert("RGB")
    im = Image.open(AI + "cover.png").convert("RGBA"); s = W / im.width; im = im.resize((W, int(im.height * s)))
    top = (im.height - H) // 2; im.crop((0, top, W, top + H)).save("/tmp/cover_ai_bg.png")
    os.makedirs("ep04_ai", exist_ok=True)
    slides = [cover_direct("/tmp/cover_ai_bg.png", "국가대표도 *72구째*엔\n볼이 느려질까?", ""), vs_ai(), ep04v2.s_question(),
              study_slide(), ep04v2.s_method(), ep04v2.s_chart(), ep04v2.s_hands(), ep04v2.s_same(), ep04v2.s_why(), ep04v2.s_summary()]
    for i, s_ in enumerate(slides, 1): s_.save(f"ep04_ai/{i:02d}.jpg", quality=92)
    ims = [Image.open(f"ep04_ai/{i:02d}.jpg").resize((324, 405)) for i in range(1, 11)]
    sh = Image.new("RGB", (334 * 5 + 10, 415 * 2 + 10), "white")
    for i, im in enumerate(ims): sh.paste(im, (10 + (i % 5) * 334, 10 + (i // 5) * 415))
    sh.save("ep04_ai_sheet.jpg", quality=90)
