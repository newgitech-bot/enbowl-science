"""BOWLING SUNDAY 단편 이미지 (1080x1350).
사용법: python scripts/cards/sun.py posts/<폴더>
content.json 의 sun 항목:
  {"type": "공감 한 컷", "headline": "*10번 핀* 하나\\n남았을 때", "sub": "...", "art": "assets/gpt/sun01/main.png",
   "palette": {"main": [R,G,B], "mark": [R,G,B]}}
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from card2 import W, H, font, rich_center  # noqa: E402

INK = (25, 25, 28)
GRAY = (120, 120, 126)


def rounded(im, r):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=r, fill=255)
    im = im.convert("RGBA")
    im.putalpha(m)
    return im


def make(spec, root):
    pal = spec.get("palette", {})
    main = tuple(pal.get("main", (88, 60, 160)))
    mark = tuple(pal.get("mark", (255, 220, 90)))
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)

    # 상단 라벨
    label = f"BOWLING SUNDAY · {spec['type']}"
    f = font("Bold", 30)
    tw = d.textlength(label, font=f)
    d.rounded_rectangle((W / 2 - tw / 2 - 26, 56, W / 2 + tw / 2 + 26, 108), radius=26, fill=main)
    d.text((W / 2 - tw / 2, 62), label, font=f, fill=(255, 255, 255))

    # 헤드라인 (형광펜 마킹)
    y = rich_center(d, 140, spec["headline"], font("ExtraBold", 72), 92, INK, mark=mark)
    if spec.get("sub"):
        y = rich_center(d, y + 6, spec["sub"], font("Medium", 36), 50, GRAY)

    # 그림
    top = int(y + 34)
    size = min(H - top - 60, W - 80)
    art = Image.open(root / spec["art"]).convert("RGB").resize((size, size), Image.LANCZOS)
    art = rounded(art, 44)
    img.paste(art, (int((W - size) / 2), top), art)

    # 하단 브랜드
    f = font("SemiBold", 26)
    t = "@enbowl_korea"
    d.text(((W - d.textlength(t, font=f)) / 2, H - 46), t, font=f, fill=(170, 170, 176))
    return img


if __name__ == "__main__":
    post = Path(sys.argv[1])
    root = Path(__file__).resolve().parent.parent.parent
    spec = json.loads((post / "content.json").read_text(encoding="utf-8"))["sun"]
    make(spec, root).save(post / "image.jpg", quality=92)
    print("저장:", post / "image.jpg")
