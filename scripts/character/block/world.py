"""앤볼 블록 월드: 블록 캐릭터 + 풍성한 블록 볼링장 (Cycles).
레인 방향 +y (핀 쪽), 파울라인 y=0, 어프로치·좌석은 y<0.
"""
import math
import os
import random

import bpy

R = math.radians
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../.."))
TEX = os.path.join(HERE, "tex")
L = 18.3          # 레인 길이(실제)
LANE_W = 1.06
PITCH = 2.0

ORANGE = (255, 114, 0)
CHAR = (36, 37, 42)
WHITE = (250, 250, 248)
FACE = (240, 238, 230)
BLUSH = (255, 150, 120)
NAVY = (60, 66, 100)


def srgb(c):
    return tuple((v / 255) ** 2.2 for v in c) + (1,)


_m = {}


def mat(rgb, rough=0.7, coat=0.0, emit=0.0):
    k = (rgb, rough, coat, emit)
    if k not in _m:
        m = bpy.data.materials.new(str(k))
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = srgb(rgb)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Coat Weight"].default_value = coat
        if emit:
            b.inputs["Emission Color"].default_value = srgb(rgb)
            b.inputs["Emission Strength"].default_value = emit
        _m[k] = m
    return _m[k]


def img_mat(path, emit=0.0, rough=0.6):
    k = ("img", path, emit)
    if k in _m:
        return _m[k]
    m = bpy.data.materials.new(os.path.basename(path))
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(path)
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    if emit:
        nt.links.new(tx.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = emit
    _m[k] = m
    return m


def coll():
    return bpy.context.scene.collection


def empty(name, loc=(0, 0, 0), parent=None, rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    coll().objects.link(e)
    e.location = loc
    e.rotation_euler = rot
    if parent:
        e.parent = parent
    return e


def box(loc, size, rgb=None, bevel=0.025, rough=0.7, rot=(0, 0, 0), P=None, shear=0.0, m=None, emit=0.0):
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    o = bpy.context.object
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if shear:
        for v in o.data.vertices:
            v.co.x += v.co.z * shear
    o.location = loc
    o.rotation_euler = rot
    if bevel:
        bv = o.modifiers.new("b", "BEVEL")
        bv.width = bevel
        bv.segments = 3
    o.data.materials.append(m or mat(rgb, rough, emit=emit))
    if P:
        o.parent = P
    return o


def plane(loc, size, m, rot=(0, 0, 0), P=None):
    bpy.ops.mesh.primitive_plane_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = (size[0] / 2, size[1] / 2, 1)
    o.data.materials.append(m)
    if P:
        o.parent = P
    return o


def sphere(loc, r, rgb, rough=0.2, coat=0.6, P=None, seg=40):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = bpy.context.object
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat(rgb, rough, coat))
    if P:
        o.parent = P
    return o


# ---------------- 캐릭터 ----------------
def face(P, hz, kind):
    fy = -0.292
    B = CHAR
    if kind in ("smile", "nervous"):
        for k in (-1, 1):
            box((0.12 * k, fy, hz + 0.02), (0.055, 0.01, 0.1), B, 0.008, 0.3, P=P)
        if kind == "smile":
            box((0, fy, hz - 0.11), (0.08, 0.01, 0.025), (200, 70, 60), 0.006, P=P)
        else:   # 긴장: 물결 입 + 처진 눈썹
            for i, dz in enumerate((0, 0.012, 0, 0.012)):
                box((-0.045 + i * 0.03, fy, hz - 0.11 + dz), (0.03, 0.01, 0.014), (200, 70, 60), 0.003, P=P)
            for k in (-1, 1):
                box((0.12 * k, fy - 0.003, hz + 0.12), (0.08, 0.01, 0.02), B, 0.004, P=P, rot=(0, R(-14 * k), 0))
    elif kind == "wow":
        for k in (-1, 1):
            box((0.12 * k, fy, hz + 0.03), (0.07, 0.01, 0.13), B, 0.01, 0.3, P=P)
            box((0.12 * k, fy - 0.003, hz + 0.18), (0.08, 0.01, 0.022), B, 0.005, P=P, rot=(0, R(-12 * k), 0))
        box((0, fy, hz - 0.12), (0.07, 0.01, 0.08), (150, 40, 50), 0.012, P=P)
    elif kind == "focus":
        for k in (-1, 1):
            box((0.12 * k, fy, hz + 0.01), (0.075, 0.01, 0.035), B, 0.008, 0.3, P=P)
            box((0.12 * k, fy - 0.003, hz + 0.1), (0.09, 0.01, 0.022), B, 0.005, P=P, rot=(0, R(15 * k), 0))
        box((0, fy, hz - 0.11), (0.05, 0.01, 0.02), (200, 70, 60), 0.005, P=P)
    elif kind == "happy":
        for k in (-1, 1):
            box((0.12 * k - 0.022, fy, hz + 0.02), (0.06, 0.01, 0.022), B, 0.005, P=P, rot=(0, R(-40), 0))
            box((0.12 * k + 0.022, fy, hz + 0.02), (0.06, 0.01, 0.022), B, 0.005, P=P, rot=(0, R(40), 0))
        box((0, fy, hz - 0.11), (0.1, 0.01, 0.05), (170, 50, 55), 0.012, P=P)
    for k in (-1, 1):
        box((0.19 * k, fy, hz - 0.08), (0.09, 0.008, 0.03), BLUSH, 0.006, P=P)


def character(loc=(0, 0, 0), rot_z=0.0, kind="smile", shirt=ORANGE, hair="band", pants=NAVY, scale=1.0):
    """관절: root > hips > head / shL / shR,  root > legL / legR.  정면 -y.  키 약 1.43."""
    root = empty("root", loc, rot=(0, 0, rot_z))
    root.scale = (scale,) * 3
    hips = empty("hips", (0, 0, 0.28), root)
    J = {"root": root, "hips": hips}
    for k, nm in ((-1, "R"), (1, "L")):
        leg = empty("leg" + nm, (0.11 * k, 0, 0.28), root)
        box((0, 0, -0.12), (0.16, 0.18, 0.22), pants, P=leg)
        box((0, -0.03, -0.24), (0.18, 0.26, 0.08), WHITE, P=leg)
        box((0, -0.03, -0.275), (0.185, 0.265, 0.02), (255, 110, 70), 0.005, P=leg)
        J["leg" + nm] = leg
    box((0, 0, 0.22), (0.5, 0.34, 0.46), shirt, P=hips)
    dark = tuple(int(c * 0.72) for c in shirt)
    for k in (-1, 1):
        box((0.2 * k, -0.172, 0.22), (0.06, 0.01, 0.44), dark, 0.0, P=hips)
        box((0.07 * k, -0.172, 0.41), (0.12, 0.012, 0.07), WHITE, 0.01, rot=(0, R(20 * k), 0), P=hips)
    box((0, -0.176, 0.27), (0.05, 0.01, 0.05), WHITE, 0.01, P=hips)
    head = empty("head", (0, 0, 0.46), hips)
    hz = 0.31
    box((0, 0, hz), (0.62, 0.58, 0.58), FACE, 0.035, P=head)
    if hair == "band":
        box((0, 0, hz + 0.27), (0.64, 0.6, 0.1), (24, 24, 28), P=head)
        box((0, 0, hz + 0.19), (0.645, 0.605, 0.075), ORANGE, 0.01, P=head)
        box((0.2, -0.305, hz + 0.19), (0.03, 0.01, 0.06), WHITE, 0.003, P=head, shear=0.42)
    elif hair == "cap":
        box((0, 0.02, hz + 0.32), (0.66, 0.62, 0.12), (40, 120, 230), P=head)
        box((0, -0.36, hz + 0.27), (0.5, 0.2, 0.04), (40, 120, 230), P=head)
    elif hair == "bob":
        box((0, 0.04, hz + 0.27), (0.66, 0.6, 0.14), (120, 70, 40), P=head)
        for k in (-1, 1):
            box((0.33 * k, 0.04, hz + 0.06), (0.06, 0.58, 0.42), (120, 70, 40), P=head)
    elif hair == "spike":
        box((0, 0, hz + 0.28), (0.64, 0.6, 0.12), (230, 190, 60), P=head)
        for i in range(3):
            box((-0.18 + i * 0.18, 0, hz + 0.37), (0.14, 0.5, 0.1), (230, 190, 60), P=head, rot=(0, R(15), 0))
    J["head"] = head
    J["face"] = empty("face", (0, 0, 0), head)
    face(J["face"], hz, kind)
    for k, nm in ((-1, "R"), (1, "L")):
        sh = empty("sh" + nm, (0.31 * k, 0, 0.38), hips)
        box((0, 0, -0.14), (0.13, 0.13, 0.3), shirt, P=sh)
        box((0, 0, -0.33), (0.11, 0.11, 0.11), FACE, P=sh)
        J["sh" + nm] = sh
        J["hand" + nm] = empty("hand" + nm, (0, -0.02, -0.33), sh)
    J["hz"] = hz
    return J


def set_face(J, kind):
    for o in list(J["face"].children):
        bpy.data.objects.remove(o, do_unlink=True)
    face(J["face"], J["hz"], kind)


def ball(rgb=CHAR, r=0.17, slash=ORANGE):
    b = empty("ball")
    sphere((0, 0, 0), r, rgb, 0.25, 0.6, P=b)
    k = r / 0.17
    for dx, dz in ((-0.04, 0.08), (0.04, 0.08), (0, 0.0)):
        sphere((dx * k, -0.155 * k, dz * k), 0.02 * k, (10, 10, 12), 0.4, 0.0, P=b, seg=16)
    if slash:
        box((0.06 * k, -0.15 * k, -0.06 * k), (0.022 * k, 0.02 * k, 0.09 * k), slash, 0.004, P=b, shear=0.42,
            rot=(R(-20), 0, 0))
    return b


def pin(x, y, s=0.95, name="pin"):
    prof = [(0, 0), (0.05, 0), (0.08, 0.05), (0.1, 0.15), (0.09, 0.25), (0.055, 0.34), (0.045, 0.4), (0.06, 0.48),
            (0.055, 0.55), (0.0, 0.58)]
    N = 8
    v, f = [], []
    for rr, z in prof:
        for k in range(N):
            a = 2 * math.pi * (k + 0.5) / N
            v.append((rr * s * math.cos(a), rr * s * math.sin(a), z * s))
    for i in range(len(prof) - 1):
        for k in range(N):
            f.append((i * N + k, i * N + (k + 1) % N, (i + 1) * N + (k + 1) % N, (i + 1) * N + k))
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    o = bpy.data.objects.new(name, me)
    coll().objects.link(o)
    o.location = (x, y, 0)
    o.data.materials.append(mat((250, 250, 246), 0.45))
    o.data.materials.append(mat((230, 60, 60), 0.5))
    for p in o.data.polygons:
        zc = sum(o.data.vertices[i].co.z for i in p.vertices) / len(p.vertices) / s
        if 0.36 < zc < 0.44:
            p.material_index = 1
    return o


def pin_set(x0, tag=""):
    sp = 0.3048
    out = []
    for r, row in enumerate([[0], [-0.5, 0.5], [-1, 0, 1], [-1.5, -0.5, 0.5, 1.5]]):
        for xx in row:
            out.append(pin(x0 + xx * sp, L - 0.86 + r * sp * 0.866, name=f"pin{tag}{len(out)}"))
    return out


# ---------------- 텍스처 (PIL) ----------------
def make_textures():
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(TEX, exist_ok=True)
    F = lambda w, s: ImageFont.truetype(os.path.join(ROOT, f"fonts/Pretendard-{w}.otf"), s)  # noqa: E731
    # 점수 모니터
    for i, (name, marks) in enumerate((("A", "X 9/ X X 72 X"), ("B", "8/ X 9- X X X"), ("C", "X X X 9/ X X"))):
        im = Image.new("RGB", (640, 360), (20, 40, 90))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 640, 60), fill=(255, 114, 0))
        d.text((20, 8), f"LANE {i + 1}", font=F("Black", 40), fill="white")
        d.text((620, 8), "ENBOWL", font=F("Black", 40), fill="white", anchor="ra")
        for r, who in enumerate(("PLAYER 1", "PLAYER 2")):
            y = 90 + r * 130
            d.text((20, y), who, font=F("Bold", 30), fill=(200, 220, 255))
            for c in range(6):
                x = 20 + c * 100
                d.rectangle((x, y + 40, x + 92, y + 120), outline=(120, 160, 230), width=3)
                d.text((x + 46, y + 80), marks.split()[c] if r == 0 else marks.split()[(c + 2) % 6], font=F("Black", 34),
                       fill="white", anchor="mm")
        im.save(os.path.join(TEX, f"score{name}.png"))
    # 마스킹 패널 (앤볼)
    im = Image.new("RGB", (800, 300), (255, 114, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(330, 60), (380, 60), (340, 240), (290, 240)], fill="white")
    d.text((420, 150), "ENBOWL", font=F("Black", 110), fill="white", anchor="lm")
    im.save(os.path.join(TEX, "mask_enbowl.png"))
    # 포스터
    im = Image.new("RGB", (400, 560), (255, 214, 60))
    d = ImageDraw.Draw(im)
    d.text((200, 120), "STRIKE", font=F("Black", 96), fill=(32, 30, 58), anchor="mm")
    d.text((200, 220), "NIGHT", font=F("Black", 96), fill=(255, 114, 0), anchor="mm")
    for k in range(3):
        x = 110 + k * 90
        d.ellipse((x - 30, 330, x + 30, 390), fill="white")
        d.rectangle((x - 18, 380, x + 18, 480), fill="white")
        d.rectangle((x - 18, 400, x + 18, 412), fill=(230, 60, 60))
    im.save(os.path.join(TEX, "poster1.png"))
    im = Image.new("RGB", (400, 560), (60, 190, 150))
    d = ImageDraw.Draw(im)
    d.ellipse((90, 120, 310, 340), fill=(32, 30, 58))
    for dx, dy in ((-30, -20), (30, -20), (0, 30)):
        d.ellipse((200 + dx - 16, 210 + dy - 16, 200 + dx + 16, 210 + dy + 16), fill=(10, 10, 12))
    d.text((200, 440), "LET'S", font=F("Black", 70), fill="white", anchor="mm")
    d.text((200, 510), "BOWL", font=F("Black", 70), fill="white", anchor="mm")
    im.save(os.path.join(TEX, "poster2.png"))
    # 카펫 패턴
    random.seed(3)
    im = Image.new("RGB", (512, 512), (52, 60, 120))
    d = ImageDraw.Draw(im)
    cols = [(255, 114, 0), (60, 190, 150), (255, 214, 60), (150, 120, 230), (240, 240, 250)]
    for _ in range(90):
        x, y = random.randint(0, 512), random.randint(0, 512)
        c = random.choice(cols)
        s = random.randint(8, 22)
        t = random.random()
        if t < 0.33:
            d.ellipse((x, y, x + s, y + s), fill=c)
        elif t < 0.66:
            d.rectangle((x, y, x + s, y + s // 3), fill=c)
        else:
            d.polygon([(x, y + s), (x + s // 2, y), (x + s, y + s)], fill=c)
    im.save(os.path.join(TEX, "carpet.png"))


# ---------------- 볼링장 ----------------
def lane(x0, idx):
    for i in range(13):
        c = (238, 194, 132) if i % 2 else (228, 182, 120)
        box((x0 - LANE_W / 2 + LANE_W * (i + 0.5) / 13, L / 2, -0.03), (LANE_W / 13 * 0.985, L, 0.06), c, 0.003, 0.35)
    box((x0, -2.6, -0.03), (LANE_W + 0.5, 5.2, 0.06), (226, 180, 118), 0.003, 0.35)   # 어프로치
    box((x0, 0.0, 0.001), (LANE_W + 0.5, 0.03, 0.004), (40, 40, 44), 0)                 # 파울라인
    for k in (-1, 1):
        box((x0 + k * (LANE_W / 2 + 0.12), L / 2, -0.07), (0.24, L, 0.06), (170, 176, 196), 0.02)
    for k in range(7):     # 스팟 화살표
        x = x0 - LANE_W / 2 + LANE_W * (k + 0.5) / 7
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.05, depth=0.006, location=(x, 4.6 + abs(k - 3) * 0.3, 0.002))
        bpy.context.object.data.materials.append(mat((170, 90, 40), 0.5))
    for k in (-0.3, -0.1, 0.1, 0.3):  # 어프로치 점
        sphere((x0 + k, -1.5, 0.0), 0.025, (170, 90, 40), 0.5, 0, seg=12)


def alley(n=5, tex=True, npc=True):
    if tex:
        make_textures()
    xs = [(i - n // 2) * PITCH for i in range(n)]
    W = n * PITCH + 8
    panel_cols = [(60, 190, 150), (150, 120, 230), None, (255, 200, 50), (0, 170, 210)]
    for i, x in enumerate(xs):
        lane(x, i)
        if panel_cols[i % 5] is None:
            box((x, L - 0.5, 1.5), (PITCH - 0.1, 0.12, 0.75), m=img_mat(os.path.join(TEX, "mask_enbowl.png"), 0.6), bevel=0.03)
        else:
            box((x, L - 0.5, 1.5), (PITCH - 0.1, 0.12, 0.75), panel_cols[i % 5], 0.03, emit=0.25)
        box((x, L + 0.7, 0.55), (PITCH - 0.1, 0.1, 1.1), (44, 42, 62), 0)                      # 피트 커튼
        box((x, L - 0.55, 1.05), (PITCH - 0.2, 0.3, 0.04), (255, 240, 200), 0, emit=1.2)      # 핀 조명
    for i in range(n + 1):           # 레인 사이 캐핑
        x = (i - n // 2 - 0.5) * PITCH
        box((x, L / 2 - 1, 0.02), (PITCH - LANE_W - 0.48, L + 2, 0.08), (236, 238, 244), 0.02)
    # 벽·천장
    box((0, L + 1.3, 3.5), (W, 0.2, 7), (250, 214, 160), 0)
    box((0, 6, 4.2), (W, 34, 0.2), (40, 44, 70), 0)                                            # 천장
    for y in range(-10, 18, 3):                                                                   # 천장 조명 줄
        for i in range(n + 1):
            x = (i - n // 2 - 0.5) * PITCH
            box((x, y, 4.05), (0.25, 2.2, 0.06), (255, 248, 230), 0, emit=2.5)
    for k in (-1, 1):
        box((k * W / 2, 4, 3.5), (0.2, 34, 7), (250, 200, 140), 0)
        # 옆벽 네온 줄
        box((k * (W / 2 - 0.12), 4, 3.2), (0.04, 30, 0.08), (255, 114, 0), 0, emit=5.0)
        box((k * (W / 2 - 0.12), 4, 2.9), (0.04, 30, 0.05), (60, 200, 255), 0, emit=5.0)
        # 볼 거치대
        for j in range(3):
            y = -6 + j * 1.6
            box((k * (W / 2 - 0.5), y, 0.5), (0.5, 1.3, 0.06), (90, 96, 120), 0.01)
            box((k * (W / 2 - 0.5), y, 0.95), (0.5, 1.3, 0.06), (90, 96, 120), 0.01)
            for b in range(4):
                c = random.choice([(255, 90, 90), (60, 130, 255), (255, 200, 60), (90, 200, 120), (180, 110, 240), (255, 140, 40)])
                sphere((k * (W / 2 - 0.5), y - 0.45 + b * 0.3, 0.66), 0.13, c, seg=24)
                c = random.choice([(255, 90, 90), (60, 130, 255), (255, 200, 60), (90, 200, 120), (180, 110, 240)])
                sphere((k * (W / 2 - 0.5), y - 0.45 + b * 0.3, 1.11), 0.13, c, seg=24)
    # 오버헤드 점수 모니터
    for i, x in enumerate(xs):
        box((x, -0.6, 3.1), (1.5, 0.12, 0.88), (30, 32, 40), 0.03)
        plane((x, -0.67, 3.1), (1.36, 0.76), img_mat(os.path.join(TEX, f"score{'ABC'[i % 3]}.png"), 1.4),
              rot=(R(90), 0, 0))
        box((x, -0.6, 3.75), (0.06, 0.06, 0.5), (30, 32, 40), 0)
    # 좌석 구역 (어프로치 뒤)
    box((0, -8.5, -0.02), (W, 7, 0.04), m=_carpet(), bevel=0)
    box((0, -5.3, 0.06), (W, 0.25, 0.12), (220, 222, 230), 0.01)              # 단차
    for i, x in enumerate(xs):
        # 점수 입력 콘솔
        # 소파 (U자)
        sc_ = [(255, 114, 0), (60, 190, 150), (150, 120, 230), (255, 200, 50), (0, 170, 210)][i % 5]
        box((x, -7.2, 0.22), (1.6, 0.6, 0.44), sc_, 0.08)
        box((x, -7.5, 0.55), (1.6, 0.15, 0.5), sc_, 0.06)
        box((x, -6.6, 0.3), (0.7, 0.45, 0.04), (245, 245, 250), 0.01)           # 작은 테이블
        box((x, -6.6, 0.15), (0.08, 0.08, 0.3), (120, 120, 130), 0)
        for dx, c in ((-0.15, (255, 90, 90)), (0.12, (60, 190, 255))):          # 음료 컵
            box((x + dx, -6.6, 0.38), (0.08, 0.08, 0.12), c, 0.01)
    # 뒷벽 (카메라가 캐릭터를 정면에서 볼 때 보이는 배경)
    box((0, -11.2, 3.5), (W, 0.2, 7), (255, 236, 205), 0)
    for k, p in ((-3.2, "poster1"), (3.2, "poster2")):
        plane((k, -11.08, 1.9), (1.0, 1.4), img_mat(os.path.join(TEX, p + ".png"), 0.15), rot=(R(90), 0, R(180)))
    _neon("BOWLING", (0, -11.05, 2.9), 0.55)
    box((0, -11.08, 2.9), (4.6, 0.04, 0.9), (40, 44, 70), 0.04)
    for k in (-1, 1):   # 화분
        x = k * (W / 2 - 1.0)
        box((x, -10.4, 0.25), (0.45, 0.45, 0.5), (220, 120, 80), 0.03)
        for j, (dx, dz) in enumerate(((0, 0.75), (0.15, 0.62), (-0.14, 0.66), (0, 0.95))):
            box((x + dx, -10.4, dz), (0.32, 0.32, 0.32), (70, 170, 90), 0.04, rot=(0, 0, R(j * 20)))
    # 시계
    sphere((-6.2 if n >= 5 else -4, -11.05, 3.6), 0.35, (250, 250, 250), 0.4, 0)
    if npc:
        _npcs(xs)
    return xs


def _carpet():
    m = img_mat(os.path.join(TEX, "carpet.png"), 0.0, 0.9)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.5, 0.5, 0.5)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    tx = [n for n in nt.nodes if n.type == "TEX_IMAGE"][0]
    nt.links.new(mp.outputs["Vector"], tx.inputs["Vector"])
    return m


def _neon(text, loc, size):
    bpy.ops.object.text_add(location=loc, rotation=(R(90), 0, R(180)))
    t = bpy.context.object
    t.data.body = text
    t.data.font = bpy.data.fonts.load(os.path.join(ROOT, "fonts/Pretendard-Black.otf"))
    t.data.size = size
    t.data.extrude = 0.02
    t.data.align_x = "CENTER"
    t.data.align_y = "CENTER"
    t.data.materials.append(mat((255, 120, 200), 0.3, emit=6.0))
    return t


def _npcs(xs):
    """옆 레인의 다른 볼러들 (배경)"""
    far = [x for x in xs if abs(x) >= 2 * PITCH - 0.01]
    styles = [((150, 120, 230), "bob"), ((250, 200, 60), "cap"), ((90, 200, 230), "spike"), ((255, 120, 150), "bob")]
    for i, x in enumerate(far):
        sh, hr = styles[i % len(styles)]
        J = character((x + 0.2, -3.2 + i * 0.4, 0), R(180), "smile", shirt=sh, hair=hr)
        if i % 2 == 0:   # 대기 자세
            J["shL"].rotation_euler = (R(-20), 0, 0)
        else:            # 투구 자세
            J["root"].location.y = -0.7
            J["hips"].rotation_euler = (R(-18), 0, 0)
            J["legL"].rotation_euler = (R(30), 0, 0)
            J["legR"].rotation_euler = (R(-45), 0, 0)
            J["shR"].rotation_euler = (R(30), 0, 0)
            J["shL"].rotation_euler = (0, R(-70), 0)
            b = ball(rgb=(255, 90, 90), slash=None)
            b.location = (x + 0.3, 1.5, 0.17)
        # 좌석의 구경꾼
        if i == 0:
            J2 = character((x - 0.4, -6.9, 0.3), 0, "happy", shirt=(90, 200, 120), hair="spike", scale=0.95)
            J2["shL"].rotation_euler = (0, R(-150), 0)
            J2["shR"].rotation_euler = (0, R(150), 0)


def lights_world(sun=2.0, sky=0.45):
    sc = bpy.context.scene
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = srgb((210, 220, 245))
    bg.inputs["Strength"].default_value = sky
    sd = bpy.data.lights.new("sun", "SUN")
    sd.energy = sun
    sd.angle = R(15)
    sd.color = (1, 0.96, 0.9)
    so = bpy.data.objects.new("sun", sd)
    so.rotation_euler = (R(40), R(-15), R(-30))
    coll().objects.link(so)
    for y in (-7, -2, 4, 10, 16):     # 실내 보조광
        ld = bpy.data.lights.new("a", "AREA")
        ld.size = 8
        ld.energy = 380
        ld.color = (1, 0.95, 0.88)
        o = bpy.data.objects.new("a", ld)
        o.location = (0, y, 3.9)
        coll().objects.link(o)


def camera(lens=32):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    c = bpy.data.objects.new("cam", cd)
    coll().objects.link(c)
    bpy.context.scene.camera = c
    return c


def look(c, loc, target, lens=None):
    from mathutils import Vector
    c.location = loc
    if lens:
        c.data.lens = lens
    c.rotation_mode = "QUATERNION"
    c.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y")


def setup_render(w=1080, h=1920, samples=32):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.view_settings.view_transform = "Standard"
    sc.render.image_settings.color_mode = "RGBA"
    return sc
