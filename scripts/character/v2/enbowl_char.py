"""앤볼 대표 캐릭터 시안 (블록 스타일 + 브랜드 요소).
사용법: python enbowl_char.py OUT.png VIEW [VARIANT] [FACE]
  VIEW   : front | back | face
  VARIANT: A(주황 셔츠) | B(흰 셔츠)
  FACE   : smile | wow | focus | happy  (face 뷰에서 쓰는 표정)
"""
import math
import os
import sys

import bpy

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
OUT, VIEW = args[0], args[1]
VAR = args[2] if len(args) > 2 else "A"
FACEX = args[3] if len(args) > 3 else "smile"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

ORANGE = (255, 114, 0)
CHAR = (36, 37, 42)
WHITE = (250, 250, 248)
FACE = (240, 238, 230)
BLUSH = (255, 150, 120)


def srgb(c):
    return tuple((v / 255) ** 2.2 for v in c) + (1,)


_m = {}


def mat(rgb, rough=0.7, coat=0.0):
    k = (rgb, rough, coat)
    if k not in _m:
        m = bpy.data.materials.new(str(k))
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = srgb(rgb)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Coat Weight"].default_value = coat
        _m[k] = m
    return _m[k]


def box(loc, size, rgb, bevel=0.025, rough=0.7, rot=(0, 0, 0), P=None, shear=0.0):
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    o = bpy.context.object
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if shear:   # '/' 모양: 위쪽을 오른쪽으로 민다
        for v in o.data.vertices:
            v.co.x += v.co.z * shear
    o.location = loc
    o.rotation_euler = rot
    if bevel:
        bv = o.modifiers.new("b", "BEVEL")
        bv.width = bevel
        bv.segments = 3
    o.data.materials.append(mat(rgb, rough))
    if P:
        o.parent = P
    return o


def sphere(loc, r, rgb, rough=0.15, coat=0.9, P=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=r, location=loc)
    o = bpy.context.object
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat(rgb, rough, coat))
    if P:
        o.parent = P
    return o


def text(body, loc, size, rgb, rot, P):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    t = bpy.context.object
    t.data.body = body
    t.data.font = bpy.data.fonts.load(os.path.join(ROOT, "fonts/Pretendard-Black.otf"))
    t.data.size = size
    t.data.extrude = 0.004
    t.data.align_x = "CENTER"
    t.data.align_y = "CENTER"
    t.data.materials.append(mat(rgb, 0.5))
    t.parent = P
    return t


def face(P, hz, kind):
    fy = -0.292
    B = CHAR
    if kind == "smile":
        for k in (-1, 1):
            box((0.12 * k, fy, hz + 0.02), (0.055, 0.01, 0.1), B, 0.008, 0.3, P=P)
        box((0, fy, hz - 0.11), (0.08, 0.01, 0.025), (200, 70, 60), 0.006, P=P)
    elif kind == "wow":
        for k in (-1, 1):
            box((0.12 * k, fy, hz + 0.03), (0.07, 0.01, 0.13), B, 0.01, 0.3, P=P)
            box((0.12 * k, fy - 0.003, hz + 0.18), (0.08, 0.01, 0.022), B, 0.005, P=P, rot=(0, math.radians(-12 * k), 0))
        box((0, fy, hz - 0.12), (0.07, 0.01, 0.08), (150, 40, 50), 0.012, P=P)
    elif kind == "focus":
        for k in (-1, 1):
            box((0.12 * k, fy, hz + 0.01), (0.075, 0.01, 0.035), B, 0.008, 0.3, P=P)
            box((0.12 * k, fy - 0.003, hz + 0.1), (0.09, 0.01, 0.022), B, 0.005, P=P, rot=(0, math.radians(15 * k), 0))
        box((0, fy, hz - 0.11), (0.05, 0.01, 0.02), (200, 70, 60), 0.005, P=P)
    elif kind == "happy":   # ^ ^ 눈
        for k in (-1, 1):
            box((0.12 * k - 0.022, fy, hz + 0.02), (0.06, 0.01, 0.022), B, 0.005, P=P, rot=(0, math.radians(-40), 0))
            box((0.12 * k + 0.022, fy, hz + 0.02), (0.06, 0.01, 0.022), B, 0.005, P=P, rot=(0, math.radians(40), 0))
        box((0, fy, hz - 0.11), (0.1, 0.01, 0.05), (170, 50, 55), 0.012, P=P)
        box((0, fy - 0.002, hz - 0.125), (0.05, 0.01, 0.02), (255, 120, 120), 0.006, P=P)
    for k in (-1, 1):
        box((0.19 * k, fy, hz - 0.08), (0.09, 0.008, 0.03), BLUSH, 0.006, P=P)


def enbowl_bowler(rot_z=0.0, kind="smile"):
    P = bpy.data.objects.new("root", None)
    sc.collection.objects.link(P)
    P.rotation_euler = (0, 0, rot_z)
    shirt = ORANGE            # 주황 셔츠 (앤볼 대표색), 기본 의상
    accent = WHITE if VAR == "A" else ORANGE
    # 다리·신발 (다른 캐릭터와 같은 기본 의상)
    for k in (-1, 1):
        box((0.11 * k, 0, 0.16), (0.16, 0.18, 0.22), (60, 66, 100), P=P)
        box((0.11 * k, -0.03, 0.04), (0.18, 0.26, 0.08), WHITE, P=P)
        box((0.11 * k, -0.03, 0.005), (0.185, 0.265, 0.02), (255, 110, 70), 0.005, P=P)
    # 셔츠: 단색 + 앞판 세로 줄 + 흰 칼라 + 단추
    box((0, 0, 0.5), (0.5, 0.34, 0.46), shirt, P=P)
    dark = tuple(int(c * 0.72) for c in shirt)
    for k in (-1, 1):   # 앞판 세로 줄(진한 민트), 흰 칼라, 흰 단추
        box((0.2 * k, -0.172, 0.5), (0.06, 0.01, 0.44), dark, 0.0, P=P)
        box((0.07 * k, -0.172, 0.69), (0.12, 0.012, 0.07), WHITE, 0.01, rot=(0, math.radians(20 * k), 0), P=P)
    box((0, -0.176, 0.55), (0.05, 0.01, 0.05), WHITE, 0.01, P=P)
    # 머리 + 헤어 + 주황 헤어밴드('/' 포인트)
    hz = 1.05
    box((0, 0, hz), (0.62, 0.58, 0.58), FACE, 0.035, P=P)
    box((0, 0, hz + 0.27), (0.64, 0.6, 0.1), (24, 24, 28), P=P)
    box((0, 0, hz + 0.19), (0.645, 0.605, 0.075), ORANGE, 0.01, P=P)
    box((0.2, -0.305, hz + 0.19), (0.03, 0.01, 0.06), WHITE, 0.003, P=P, shear=0.42)
    face(P, hz, kind)
    # 팔 + 볼 (차콜 볼에 주황 '/')
    for k in (-1, 1):
        box((0.25 * k, -0.2, 0.6), (0.12, 0.34, 0.12), shirt, rot=(math.radians(12), 0, math.radians(14 * k)), P=P)
        box((0.19 * k, -0.37, 0.57), (0.11, 0.1, 0.11), FACE, P=P)
    sphere((0, -0.36, 0.56), 0.17, CHAR, 0.25, 0.5, P=P)
    for dx, dz in ((-0.04, 0.08), (0.04, 0.08), (0, 0.0)):
        sphere((dx, -0.515, 0.56 + dz), 0.02, (10, 10, 12), 0.4, 0.0, P=P)
    box((0.06, -0.505, 0.5), (0.022, 0.02, 0.09), ORANGE, 0.004, P=P, shear=0.42,
        rot=(math.radians(-20), math.radians(0), 0))
    return P


def studio():
    box((0, 0, -0.05), (8, 8, 0.1), (255, 236, 214), 0, 0.9)
    bpy.ops.mesh.primitive_plane_add(location=(0, 3, 2), rotation=(math.radians(90), 0, 0))
    p = bpy.context.object
    p.scale = (5, 3, 1)
    p.data.materials.append(mat((255, 228, 200), 0.9))
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = srgb((255, 240, 225))
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.3
    for loc, rot, e, size in (((-1.6, -2.2, 2.4), (55, 0, -35), 75, 2.5), ((1.8, -1.2, 1.6), (70, 0, 55), 28, 2.0),
                              ((0.5, 2.0, 2.2), (-120, 0, 15), 45, 1.5)):
        ld = bpy.data.lights.new("a", "AREA")
        ld.size = size
        ld.energy = e
        o = bpy.data.objects.new("a", ld)
        o.location = loc
        o.rotation_euler = tuple(math.radians(a) for a in rot)
        sc.collection.objects.link(o)


def cam(loc, tgt, lens):
    cd = bpy.data.cameras.new("c")
    cd.lens = lens
    c = bpy.data.objects.new("c", cd)
    sc.collection.objects.link(c)
    c.location = loc
    t = bpy.data.objects.new("t", None)
    sc.collection.objects.link(t)
    t.location = tgt
    tr = c.constraints.new("TRACK_TO")
    tr.target = t
    tr.track_axis = "TRACK_NEGATIVE_Z"
    tr.up_axis = "UP_Y"
    sc.camera = c


studio()
if VIEW == "front":
    enbowl_bowler(math.radians(-22), "smile")
    cam((0, -3.4, 1.0), (0, 0, 0.68), 50)
elif VIEW == "back":
    enbowl_bowler(math.radians(180 - 22), "smile")
    cam((0, -3.4, 1.0), (0, 0, 0.68), 50)
else:
    enbowl_bowler(math.radians(-10), FACEX)
    cam((0, -2.2, 1.12), (0, 0, 1.0), 85)
sc.render.engine = "CYCLES"
sc.cycles.samples = 40
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = (600, 800) if VIEW != "face" else (500, 500)
sc.view_settings.view_transform = "Standard"
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("saved", OUT)
