"""앤볼 블록 캐릭터 움직임 시안 스틸.
사용법: python pose_block.py OUT.png POSE   (POSE: walk | throw | cheer)
"""
import math
import random
import sys

import bpy

OUT, POSE = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
R = math.radians

ORANGE = (255, 114, 0)
CHAR = (36, 37, 42)
WHITE = (250, 250, 248)
FACE = (240, 238, 230)
BLUSH = (255, 150, 120)
NAVY = (60, 66, 100)


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


def empty(name, loc, parent=None, rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    sc.collection.objects.link(e)
    e.location = loc
    e.rotation_euler = rot
    if parent:
        e.parent = parent
    return e


def box(loc, size, rgb, bevel=0.025, rough=0.7, rot=(0, 0, 0), P=None, shear=0.0):
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
    o.data.materials.append(mat(rgb, rough))
    if P:
        o.parent = P
    return o


def sphere(loc, r, rgb, rough=0.2, coat=0.6, P=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=r, location=loc)
    o = bpy.context.object
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat(rgb, rough, coat))
    if P:
        o.parent = P
    return o


def face(P, hz, kind):
    fy = -0.292
    B = CHAR
    if kind == "smile":
        for k in (-1, 1):
            box((0.12 * k, fy, hz + 0.02), (0.055, 0.01, 0.1), B, 0.008, 0.3, P=P)
        box((0, fy, hz - 0.11), (0.08, 0.01, 0.025), (200, 70, 60), 0.006, P=P)
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
        box((0, fy - 0.002, hz - 0.125), (0.05, 0.01, 0.02), (255, 120, 120), 0.006, P=P)
    for k in (-1, 1):
        box((0.19 * k, fy, hz - 0.08), (0.09, 0.008, 0.03), BLUSH, 0.006, P=P)


def character(loc, rot_z, kind):
    """관절: root > hips(상체 숙임) > shoulders / head,  root > legs. 정면 -y."""
    root = empty("root", loc, rot=(0, 0, rot_z))
    hips = empty("hips", (0, 0, 0.28), root)
    J = {"root": root, "hips": hips}
    for k, nm in ((-1, "R"), (1, "L")):     # 캐릭터 오른쪽은 -x
        leg = empty("leg" + nm, (0.11 * k, 0, 0.28), root)
        box((0, 0, -0.12), (0.16, 0.18, 0.22), NAVY, P=leg)
        box((0, -0.03, -0.24), (0.18, 0.26, 0.08), WHITE, P=leg)
        box((0, -0.03, -0.275), (0.185, 0.265, 0.02), (255, 110, 70), 0.005, P=leg)
        J["leg" + nm] = leg
    shirt = ORANGE
    box((0, 0, 0.22), (0.5, 0.34, 0.46), shirt, P=hips)
    dark = tuple(int(c * 0.72) for c in shirt)
    for k in (-1, 1):
        box((0.2 * k, -0.172, 0.22), (0.06, 0.01, 0.44), dark, 0.0, P=hips)
        box((0.07 * k, -0.172, 0.41), (0.12, 0.012, 0.07), WHITE, 0.01, rot=(0, R(20 * k), 0), P=hips)
    box((0, -0.176, 0.27), (0.05, 0.01, 0.05), WHITE, 0.01, P=hips)
    head = empty("head", (0, 0, 0.46), hips)
    hz = 0.31
    box((0, 0, hz), (0.62, 0.58, 0.58), FACE, 0.035, P=head)
    box((0, 0, hz + 0.27), (0.64, 0.6, 0.1), (24, 24, 28), P=head)
    box((0, 0, hz + 0.19), (0.645, 0.605, 0.075), ORANGE, 0.01, P=head)
    box((0.2, -0.305, hz + 0.19), (0.03, 0.01, 0.06), WHITE, 0.003, P=head, shear=0.42)
    face(head, hz, kind)
    J["head"] = head
    for k, nm in ((-1, "R"), (1, "L")):
        sh = empty("sh" + nm, (0.31 * k, 0, 0.38), hips)
        box((0, 0, -0.14), (0.13, 0.13, 0.3), shirt, P=sh)
        box((0, 0, -0.33), (0.11, 0.11, 0.11), FACE, P=sh)
        J["sh" + nm] = sh
    return J


def ball(loc, P=None):
    b = empty("ball", loc, P)
    sphere((0, 0, 0), 0.17, CHAR, 0.25, 0.5, P=b)
    for dx, dz in ((-0.04, 0.08), (0.04, 0.08), (0, 0.0)):
        sphere((dx, -0.155, dz), 0.02, (10, 10, 12), 0.4, 0.0, P=b)
    box((0.06, -0.15, -0.06), (0.022, 0.02, 0.09), ORANGE, 0.004, P=b, shear=0.42, rot=(R(-20), 0, 0))
    return b


def pin(x, y, rot=(0, 0, 0), z=0.0, s=0.95):
    prof = [(0, 0), (0.05, 0), (0.08, 0.05), (0.1, 0.15), (0.09, 0.25), (0.055, 0.34), (0.045, 0.4), (0.06, 0.48),
            (0.055, 0.55), (0.0, 0.58)]
    N = 8
    v, f = [], []
    for r, zz in prof:
        for k in range(N):
            a = 2 * math.pi * (k + 0.5) / N
            v.append((r * s * math.cos(a), r * s * math.sin(a), zz * s))
    for i in range(len(prof) - 1):
        for k in range(N):
            f.append((i * N + k, i * N + (k + 1) % N, (i + 1) * N + (k + 1) % N, (i + 1) * N + k))
    me = bpy.data.meshes.new("pin")
    me.from_pydata(v, [], f)
    o = bpy.data.objects.new("pin", me)
    sc.collection.objects.link(o)
    o.location = (x, y, z)
    o.rotation_euler = rot
    o.data.materials.append(mat((250, 250, 246), 0.5))
    o.data.materials.append(mat((230, 60, 60), 0.5))
    for p in o.data.polygons:
        zc = sum(o.data.vertices[i].co.z for i in p.vertices) / len(p.vertices) / s
        if 0.36 < zc < 0.44:
            p.material_index = 1


def alley(strike=False, ret_x=2.6):
    for i in range(10):
        c = (236, 190, 128) if i % 2 else (226, 178, 116)
        box((-1.35 + i * 0.3, 5, -0.05), (0.29, 16, 0.1), c, 0.005, 0.4)
    for k in (-1, 1):
        box((k * 1.7, 5, -0.09), (0.4, 16, 0.1), (170, 176, 196), 0.01)
        box((k * 3.3, 5, -0.05), (2.8, 16, 0.1), (120, 196, 220))
    box((0, 11, 4.0), (14, 0.2, 9.0), (250, 196, 120), 0)
    for i, c in enumerate([(255, 120, 60), (120, 100, 230), (60, 190, 150), (255, 200, 50)]):
        box((-2.7 + i * 1.8, 10.85, 2.6), (1.5, 0.1, 0.8), c, 0.03)
    box((0, 10.8, 0.6), (3.4, 0.2, 1.2), (60, 56, 80), 0.02)
    box((0, -3.5, -0.06), (8, 7, 0.1), (214, 166, 108), 0, 0.4)
    box((ret_x, -1.5, 0.35), (0.6, 1.2, 0.7), (60, 120, 220), 0.08)
    for i, c in enumerate([(255, 90, 90), (90, 200, 120), (255, 200, 60)]):
        sphere((ret_x, -1.8 + i * 0.3, 0.83), 0.13, c)
    sp = 0.3
    random.seed(4)
    for r, row in enumerate([[0], [-0.5, 0.5], [-1, 0, 1], [-1.5, -0.5, 0.5, 1.5]]):
        for xx in row:
            x, y = xx * sp, 9.4 + r * sp * 0.87
            if strike:   # 쓰러지고 튀어오르는 핀
                pin(x + random.uniform(-0.4, 0.4), y + random.uniform(-0.2, 0.5),
                    (R(random.uniform(40, 100)), R(random.uniform(-60, 60)), R(random.uniform(0, 360))),
                    z=random.uniform(0.0, 0.6))
            else:
                pin(x, y)


def sparkle(loc, s):
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=s, depth=0.02, location=loc, rotation=(R(90), 0, 0))
    bpy.context.object.data.materials.append(mat((255, 220, 60), 0.4))


def world_cam(cloc, tloc, lens):
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = srgb((200, 220, 255))
    bg.inputs["Strength"].default_value = 0.9
    sd = bpy.data.lights.new("sun", "SUN")
    sd.energy = 3.0
    sd.angle = R(12)
    sd.color = (1, 0.96, 0.9)
    so = bpy.data.objects.new("sun", sd)
    so.rotation_euler = (R(50), R(-20), R(-35))
    sc.collection.objects.link(so)
    cd = bpy.data.cameras.new("c")
    cd.lens = lens
    c = bpy.data.objects.new("c", cd)
    sc.collection.objects.link(c)
    c.location = cloc
    t = empty("t", tloc)
    tr = c.constraints.new("TRACK_TO")
    tr.target = t
    tr.track_axis = "TRACK_NEGATIVE_Z"
    tr.up_axis = "UP_Y"
    sc.camera = c


if POSE == "walk":
    alley()
    J = character((0.3, -1.6, 0), R(-25), "smile")        # 카메라 쪽을 보며 걸어옴
    J["legL"].rotation_euler = (R(28), 0, 0)
    J["legR"].rotation_euler = (R(-28), 0, 0)
    J["shL"].rotation_euler = (R(-30), 0, R(8))
    J["shR"].rotation_euler = (R(18), 0, R(-6))
    J["root"].location.z = 0.03
    ball((0, 0, -0.45), J["shR"])
    world_cam((0.6, -4.8, 1.25), (0.2, -1.2, 0.7), 38)
elif POSE == "throw":
    alley(ret_x=-2.6)
    J = character((0.15, -0.9, 0), 0.0, "focus")          # 레인을 향해(+y) 던짐, 옆에서 봄
    J["root"].rotation_euler = (0, 0, R(180))
    J["hips"].rotation_euler = (R(-18), 0, 0)              # 상체 숙임(정면 -y 기준, 회전 후 레인쪽)
    J["legL"].rotation_euler = (R(35), 0, 0)              # 왼발 앞으로 슬라이드
    J["legR"].rotation_euler = (R(-55), 0, 0)               # 오른발 뒤로 뻗기
    J["root"].location.z = -0.04
    J["shR"].rotation_euler = (R(35), 0, 0)               # 오른팔 앞으로 쭉
    J["shL"].rotation_euler = (0, R(-75), 0)               # 왼팔 옆으로 균형
    ball((0.55, 0.9, 0.17))                               # 막 손을 떠나 레인 위로
    world_cam((0.75, -3.9, 1.1), (0.35, 1.5, 0.45), 34)
else:  # cheer
    alley(strike=True)
    J = character((0.0, -1.2, 0), 0.0, "happy")
    J["shL"].rotation_euler = (0, R(-160), 0)
    J["shR"].rotation_euler = (0, R(160), 0)
    J["root"].location.z = 0.12                             # 살짝 점프
    J["legL"].rotation_euler = (R(-15), 0, 0)
    J["legR"].rotation_euler = (R(20), 0, 0)
    for p, s in (((-0.75, -1.6, 1.75), 0.08), ((0.8, -1.6, 1.6), 0.06), ((0.6, -1.6, 2.0), 0.045)):
        sparkle(p, s)
    world_cam((0.0, -4.4, 1.15), (0.0, 1.0, 0.95), 34)

sc.render.engine = "CYCLES"
sc.cycles.samples = 48
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 720, 1280
sc.view_settings.view_transform = "Standard"
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("saved", OUT)
