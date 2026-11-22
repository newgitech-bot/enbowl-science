"""네모 얼굴 블록 캐릭터 시안 (앤볼 오리지널 캐릭터).
사용법: python blocky.py OUT.png SHOT   (SHOT: wide | close)
"""
import math
import sys

import bpy
from mathutils import Vector

SHOT = sys.argv[-1]
OUT = sys.argv[-2]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def srgb(c):
    return tuple((v / 255) ** 2.2 for v in c) + (1,)


_m = {}


def mat(rgb, rough=0.75, coat=0.0):
    k = (rgb, rough, coat)
    if k in _m:
        return _m[k]
    m = bpy.data.materials.new(str(k))
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = srgb(rgb)
    b.inputs["Roughness"].default_value = rough
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    _m[k] = m
    return m


def box(loc, size, rgb, bevel=0.03, rough=0.75, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        bv = o.modifiers.new("b", "BEVEL")
        bv.width = bevel
        bv.segments = 3
    o.data.materials.append(mat(rgb, rough))
    if parent:
        o.parent = parent
    return o


def sphere(loc, r, rgb, rough=0.2, coat=0.8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=r, location=loc)
    o = bpy.context.object
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat(rgb, rough, coat))
    return o


FACE = (238, 236, 228)
BLK = (30, 30, 38)
BLUSH = (236, 130, 110)


def bowler(x, y, shirt, hair, face_rot=0.0, pose="hold", ball_rgb=None, mouth="smile", s=1.0):
    """머리 큐브 0.62, 몸 0.46. 정면은 -y."""
    root = bpy.data.objects.new("b", None)
    sc.collection.objects.link(root)
    root.location = (x, y, 0)
    root.rotation_euler = (0, 0, face_rot)
    root.scale = (s, s, s)
    P = root
    # 다리, 신발
    for k in (-1, 1):
        box((0.11 * k, 0, 0.16), (0.16, 0.18, 0.22), (60, 66, 100), parent=P)
        box((0.11 * k, -0.03, 0.04), (0.18, 0.26, 0.08), (250, 250, 250), parent=P)
        box((0.11 * k, -0.03, 0.005), (0.185, 0.265, 0.02), (255, 110, 70), bevel=0.005, parent=P)
    # 몸통 (볼링 셔츠: 옆 줄무늬 + 칼라)
    box((0, 0, 0.5), (0.5, 0.34, 0.46), shirt, parent=P)
    dark = tuple(int(c * 0.72) for c in shirt)
    for k in (-1, 1):
        box((0.2 * k, -0.172, 0.5), (0.06, 0.01, 0.44), dark, bevel=0.0, parent=P)
    box((-0.07, -0.172, 0.69), (0.12, 0.012, 0.07), (250, 250, 250), bevel=0.01, rot=(0, math.radians(-20), 0), parent=P)
    box((0.07, -0.172, 0.69), (0.12, 0.012, 0.07), (250, 250, 250), bevel=0.01, rot=(0, math.radians(20), 0), parent=P)
    box((0, -0.176, 0.55), (0.05, 0.01, 0.05), (255, 255, 255), bevel=0.01, parent=P)   # 단추
    # 머리
    hz = 0.74 + 0.31
    box((0, 0, hz), (0.62, 0.58, 0.58), FACE, bevel=0.035, parent=P)
    # 얼굴: 세로 네모 눈, 볼터치, 입
    for k in (-1, 1):
        box((0.12 * k, -0.292, hz + 0.02), (0.055, 0.01, 0.1), BLK, bevel=0.008, rough=0.3, parent=P)
        box((0.19 * k, -0.292, hz - 0.08), (0.09, 0.008, 0.03), BLUSH, bevel=0.006, parent=P)
    if mouth == "smile":
        box((0, -0.292, hz - 0.11), (0.07, 0.01, 0.025), (190, 70, 70), bevel=0.006, parent=P)
    elif mouth == "o":
        box((0, -0.292, hz - 0.12), (0.06, 0.01, 0.06), (150, 50, 60), bevel=0.01, parent=P)
    # 머리 스타일
    if hair == "band":            # 헤어밴드 (주인공)
        box((0, 0, hz + 0.27), (0.64, 0.6, 0.1), (40, 36, 44), parent=P)
        box((0, 0, hz + 0.19), (0.645, 0.605, 0.07), (255, 70, 70), bevel=0.01, parent=P)
        box((0.0, 0.03, hz + 0.34), (0.3, 0.3, 0.08), (40, 36, 44), parent=P)
    elif hair == "cap":           # 캡모자
        box((0, 0.02, hz + 0.32), (0.66, 0.62, 0.12), (40, 120, 230), parent=P)
        box((0, -0.36, hz + 0.27), (0.5, 0.2, 0.04), (40, 120, 230), parent=P)
    elif hair == "bob":           # 단발
        box((0, 0.04, hz + 0.27), (0.66, 0.6, 0.14), (120, 70, 40), parent=P)
        for k in (-1, 1):
            box((0.33 * k, 0.04, hz + 0.06), (0.06, 0.58, 0.42), (120, 70, 40), parent=P)
    # 팔·볼
    arm = shirt
    if pose == "hold":
        for k in (-1, 1):
            box((0.25 * k, -0.2, 0.6), (0.12, 0.34, 0.12), arm, rot=(math.radians(12), 0, math.radians(14 * k)), parent=P)
            box((0.19 * k, -0.37, 0.57), (0.11, 0.1, 0.11), FACE, parent=P)
        if ball_rgb:
            b = sphere((0, 0, 0), 0.17, ball_rgb)
            b.parent = P
            b.location = (0, -0.36, 0.56)
            for dx, dz in ((-0.04, 0.07), (0.04, 0.07), (0, -0.01)):
                h = sphere((0, 0, 0), 0.022, BLK, 0.3, 0)
                h.parent = P
                h.location = (dx, -0.522, 0.56 + dz)
    elif pose == "cheer":
        for k in (-1, 1):
            box((0.33 * k, 0, 0.82), (0.13, 0.13, 0.3), arm, rot=(0, math.radians(-25 * k), 0), parent=P)
    else:
        for k in (-1, 1):
            box((0.32 * k, 0, 0.48), (0.13, 0.13, 0.3), arm, parent=P)
    return root


def pin(x, y, s=1.0):
    """각진 블록풍 핀 (8각 회전체)"""
    prof = [(0, 0), (0.05, 0), (0.08, 0.05), (0.1, 0.15), (0.09, 0.25), (0.055, 0.34), (0.045, 0.4), (0.06, 0.48),
            (0.055, 0.55), (0.0, 0.58)]
    N = 8
    v, f = [], []
    for r, z in prof:
        for k in range(N):
            a = 2 * math.pi * (k + 0.5) / N
            v.append((r * s * math.cos(a), r * s * math.sin(a), z * s))
    for i in range(len(prof) - 1):
        for k in range(N):
            f.append((i * N + k, i * N + (k + 1) % N, (i + 1) * N + (k + 1) % N, (i + 1) * N + k))
    me = bpy.data.meshes.new("pin")
    me.from_pydata(v, [], f)
    o = bpy.data.objects.new("pin", me)
    sc.collection.objects.link(o)
    o.location = (x, y, 0)
    o.data.materials.append(mat((250, 250, 246), 0.5))
    o.data.materials.append(mat((230, 60, 60), 0.5))
    for p in o.data.polygons:
        zc = sum(o.data.vertices[i].co.z for i in p.vertices) / len(p.vertices) / s
        if 0.36 < zc < 0.44:
            p.material_index = 1
    return o


def alley():
    # 레인 (판자)
    for i in range(10):
        c = (236, 190, 128) if i % 2 else (226, 178, 116)
        box((-1.35 + i * 0.3, 5, -0.05), (0.29, 16, 0.1), c, bevel=0.005, rough=0.4)
    for k in (-1, 1):
        box((k * 1.7, 5, -0.09), (0.4, 16, 0.1), (170, 176, 196), bevel=0.01)
        box((k * 3.3, 5, -0.05), (2.8, 16, 0.1), (120, 196, 220))
    # 벽, 패널, 핀 데크
    box((0, 11, 4.0), (14, 0.2, 9.0), (250, 196, 120), bevel=0)
    for i, c in enumerate([(255, 120, 60), (120, 100, 230), (60, 190, 150), (255, 200, 50)]):
        box((-2.7 + i * 1.8, 10.85, 2.6), (1.5, 0.1, 0.8), c, bevel=0.03)
    box((0, 10.8, 0.6), (3.4, 0.2, 1.2), (60, 56, 80), bevel=0.02)
    sp = 0.3
    for r, row in enumerate([[0], [-0.5, 0.5], [-1, 0, 1], [-1.5, -0.5, 0.5, 1.5]]):
        for xx in row:
            pin(xx * sp, 9.4 + r * sp * 0.87, 0.95)
    # 바닥 앞쪽 어프로치
    box((0, -2.5, -0.06), (8, 5, 0.1), (214, 166, 108), bevel=0, rough=0.4)
    # 볼 리턴
    box((2.4, -0.8, 0.35), (0.6, 1.2, 0.7), (60, 120, 220), bevel=0.08)
    for i, c in enumerate([(255, 90, 90), (90, 200, 120), (255, 200, 60)]):
        sphere((2.4, -1.1 + i * 0.3, 0.83), 0.13, c)


def light_cam():
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = srgb((200, 220, 255))
    bg.inputs["Strength"].default_value = 0.9
    sd = bpy.data.lights.new("sun", "SUN")
    sd.energy = 3.2
    sd.angle = math.radians(12)
    sd.color = (1, 0.96, 0.9)
    so = bpy.data.objects.new("sun", sd)
    so.rotation_euler = (math.radians(50), math.radians(-20), math.radians(-35))
    sc.collection.objects.link(so)
    cd = bpy.data.cameras.new("c")
    c = bpy.data.objects.new("c", cd)
    sc.collection.objects.link(c)
    t = bpy.data.objects.new("t", None)
    sc.collection.objects.link(t)
    if SHOT == "wide":
        cd.lens = 32
        c.location = (0.0, -4.6, 1.5)
        t.location = (0, 1.5, 0.7)
    else:
        cd.lens = 45
        c.location = (0.6, -2.6, 1.2)
        t.location = (0.05, 0.2, 0.85)
    tr = c.constraints.new("TRACK_TO")
    tr.target = t
    tr.track_axis = "TRACK_NEGATIVE_Z"
    tr.up_axis = "UP_Y"
    sc.camera = c


alley()
if SHOT == "wide":
    bowler(0.0, 0.0, (70, 190, 160), "band", pose="hold", ball_rgb=(40, 110, 255))
    bowler(-1.05, 0.5, (150, 120, 230), "bob", face_rot=math.radians(-20), pose="cheer", mouth="o")
    bowler(1.05, 0.5, (250, 200, 60), "cap", face_rot=math.radians(20), pose="idle")
else:
    bowler(0.0, 0.0, (70, 190, 160), "band", pose="hold", ball_rgb=(40, 110, 255), mouth="o")
light_cam()
sc.render.engine = "CYCLES"
sc.cycles.samples = 48
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 720, 1280
sc.view_settings.view_transform = "Standard"
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("saved", OUT)
