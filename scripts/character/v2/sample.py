"""릴스 v2 품질 샘플: Cycles 조명 렌더 + 물리 핀 충돌 + 추적 카메라.
타임라인은 48fps(물리 기준). 합성할 때 일반 구간은 2프레임마다, 충돌 구간은 모든 프레임을 써서 0.5배 슬로모션.

사용법:
  python sample.py OUT_DIR FRAMES [--preview]
  FRAMES 예: 0-214:2,215-330     (구간:간격 을 쉼표로)
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import scene as S  # noqa: E402

FPS = 48
END = 330
RELEASE = 116
IMPACT = 222
CS = 0.72        # 캐릭터 축척
BR = 0.118       # 볼 반지름
LEN = 18.3
HEAD_Y = LEN - 0.86


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


# ---------- 재질: Principled BSDF 로 변환 ----------
def principled(m, base, rough=0.5, coat=0.0, emit=0.0):
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = base
    b.inputs["Roughness"].default_value = rough
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.03
    if emit:
        b.inputs["Emission Color"].default_value = base
        b.inputs["Emission Strength"].default_value = emit
    return b


def wood_grain(m, base):
    b = principled(m, base, 0.18, coat=0.8)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (60.0, 1.2, 60.0)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nz.inputs["Detail"].default_value = 8.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    dark = tuple(c * 0.82 for c in base[:3]) + (1,)
    ramp.color_ramp.elements[0].color = dark
    ramp.color_ramp.elements[1].color = base
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])


def upgrade_materials():
    for m in bpy.data.materials:
        base = tuple(m.diffuse_color)
        n = m.name
        if n.startswith("wood"):
            wood_grain(m, base)
        elif n in ("pin",):
            principled(m, base, 0.22, coat=1.0)
        elif n.startswith("ball"):
            principled(m, base, 0.06, coat=1.0)
        elif n in ("screen",) or n.startswith("mask"):
            principled(m, base, 0.4, emit=1.6 if n == "screen" else 0.35)
        elif n == "capping":
            principled(m, (0.55, 0.58, 0.64, 1), 0.35)
        elif n == "gutter":
            principled(m, (0.25, 0.27, 0.31, 1), 0.25)
        elif n in ("ret", "hood"):
            principled(m, base, 0.3)
        elif n in ("hair",):
            principled(m, base, 0.35, coat=0.3)
        elif n in ("black", "hole"):
            principled(m, base, 0.2)
        else:
            principled(m, base, 0.55)


# ---------- 핀: 한 덩어리 메시, 무게중심 원점 ----------
def make_pin(name, loc):
    m = S.mat("pin", S.WHITE, 0.2)
    r = S.mat("pinred", (210, 30, 40))
    prof = [(0, 0), (0.026, 0), (0.04, 0.02), (0.054, 0.06), (0.06, 0.11), (0.058, 0.16), (0.048, 0.21),
            (0.034, 0.25), (0.025, 0.28), (0.024, 0.30), (0.029, 0.32), (0.0325, 0.34), (0.031, 0.356),
            (0.026, 0.368), (0.018, 0.377), (0.008, 0.383), (0, 0.385)]
    s = 0.99
    N = 28
    verts, faces = [], []
    for rr, z in prof:
        for k in range(N):
            a = 2 * math.pi * k / N
            verts.append((rr * s * math.cos(a), rr * s * math.sin(a), z * s))
    for i in range(len(prof) - 1):
        for k in range(N):
            a = i * N + k; b = i * N + (k + 1) % N
            faces.append((a, b, (i + 1) * N + (k + 1) % N, (i + 1) * N + k))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    o.data.materials.append(r)
    for p in o.data.polygons:
        p.use_smooth = True
        zc = sum(o.data.vertices[v].co.z for v in p.vertices) / len(p.vertices)
        if 0.248 * s < zc < 0.262 * s or 0.278 * s < zc < 0.292 * s:
            p.material_index = 1
    o.location = loc
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.origin_set(type="ORIGIN_CENTER_OF_VOLUME")
    o.select_set(False)
    return o


def build():
    clear()
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 0, END
    S.alley(n=5, length=LEN)
    # 레인 위 원래 핀은 쓰지 않고 물리 핀을 만든다
    sp = 0.3048
    rows = [[0], [-0.5, 0.5], [-1, 0, 1], [-1.5, -0.5, 0.5, 1.5]]
    pins = []
    for r_, row in enumerate(rows):
        for x in row:
            pins.append(make_pin(f"ppin{len(pins)}", (x * sp, HEAD_Y + r_ * sp * 0.866, 0)))
    # 다른 레인의 서 있는 핀(배경)
    for i, x0 in enumerate([-4, -2, 2, 4]):
        for r_, row in enumerate(rows):
            for x in row:
                make_pin(f"bpin{i}_{r_}_{x}", (x0 + x * sp, HEAD_Y + r_ * sp * 0.866, 0))

    # 캐릭터 (레인을 바라보게 180도)
    root, head, arms, legs = S.character("bowler", shirt=S.ORANGE)
    root.scale = (CS, CS, CS)
    root.rotation_euler = (0, 0, math.pi)
    ball = S.ball("ball", (0, 0, BR), rgb=(40, 90, 230), r=BR)

    upgrade_materials()
    animate(root, arms, legs, ball)
    physics(pins, ball)
    lights_world()
    cameras(root, ball)
    return sc


def key(o, path, f, val, idx=None):
    if idx is None:
        setattr(o, path, val)
        o.keyframe_insert(path, frame=f)
    else:
        getattr(o, path)[idx] = val
        o.keyframe_insert(path, index=idx, frame=f)


def animate(root, arms, legs, ball):
    R, L = arms[-1], arms[1]     # 캐릭터 오른팔(-1), 왼팔(+1)
    # 어프로치: 4걸음 + 슬라이드
    for f, y in ((0, -4.4), (24, -4.4), (112, -0.95), (126, -0.75)):
        key(root, "location", f, y, 1)
    key(root, "location", 0, 0.05, 0)
    # 걸음: 다리 번갈아
    for i, f in enumerate(range(24, 112, 22)):
        s = 1 if i % 2 == 0 else -1
        key(legs[1], "rotation_euler", f, math.radians(-22 * s), 0)
        key(legs[-1], "rotation_euler", f, math.radians(22 * s), 0)
    key(legs[1], "rotation_euler", 112, math.radians(-38), 0)     # 왼발 슬라이드 앞으로
    key(legs[-1], "rotation_euler", 112, math.radians(30), 0)
    key(legs[-1], "rotation_euler", 126, math.radians(48), 0)     # 오른발 뒤로 뻗기
    # 상체 숙이기 (root x 회전)
    key(root, "rotation_euler", 90, 0, 0)
    key(root, "rotation_euler", 120, math.radians(-14), 0)
    # 오른팔 스윙: 앞(-) 뒤(+)
    for f, a in ((0, -55), (30, -55), (44, -40), (66, 0), (90, 70), (104, 40), (116, -12), (134, -95)):
        key(R, "rotation_euler", f, math.radians(a), 0)
    # 왼팔 균형
    for f, a in ((0, -30), (60, -20), (110, 0)):
        key(L, "rotation_euler", f, math.radians(a), 0)
    key(L, "rotation_euler", 0, math.radians(-8), 1)
    key(L, "rotation_euler", 80, math.radians(-10), 1)
    key(L, "rotation_euler", 116, math.radians(-55), 1)

    # 볼: 릴리스 전엔 손 위치를 따라가게 굽고, 이후 레인 경로
    sc = bpy.context.scene
    hand = bpy.data.objects["hand-1"]
    for f in range(0, RELEASE + 1, 2):
        sc.frame_set(f)
        p = hand.matrix_world.translation.copy()
        key(ball, "location", f, Vector((p.x, p.y + 0.02, p.z - BR * 0.75)))
    rel = ball.location.copy()
    path = [(RELEASE + 6, (rel.x + 0.02, rel.y + 0.6, BR)), (150, (0.40, 5.5, BR)), (180, (0.34, 11.0, BR)),
            (205, (0.18, 15.2, BR)), (IMPACT, (0.065, HEAD_Y - 0.12, BR)), (240, (-0.02, LEN + 0.5, BR)),
            (256, (-0.05, LEN + 1.0, -0.15))]
    for f, p in path:
        key(ball, "location", f, Vector(p))
    # 굴러가는 회전
    key(ball, "rotation_euler", RELEASE, 0, 0)
    key(ball, "rotation_euler", 256, (LEN + 1.0) / BR, 0)
    for fc in ball.animation_data.action.fcurves if ball.animation_data.action and hasattr(ball.animation_data.action, "fcurves") else []:
        if fc.data_path == "rotation_euler":
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def passive_box(name, loc, size):
    o = S.box(name, loc, size, S.mat("inv", (0, 0, 0)))
    o.hide_render = True
    bpy.context.view_layer.objects.active = o
    bpy.ops.rigidbody.object_add()
    o.rigid_body.type = "PASSIVE"
    o.rigid_body.friction = 0.6
    o.rigid_body.restitution = 0.3
    return o


def physics(pins, ball):
    sc = bpy.context.scene
    bpy.ops.rigidbody.world_add()
    w = sc.rigidbody_world
    w.point_cache.frame_start = 0
    w.point_cache.frame_end = END
    w.substeps_per_frame = 12
    w.solver_iterations = 30
    for p in pins:
        bpy.context.view_layer.objects.active = p
        bpy.ops.rigidbody.object_add()
        rb = p.rigid_body
        rb.type = "ACTIVE"; rb.collision_shape = "CONVEX_HULL"
        rb.mass = 1.6; rb.friction = 0.45; rb.restitution = 0.55
        rb.collision_margin = 0.002
    bpy.context.view_layer.objects.active = ball
    bpy.ops.rigidbody.object_add()
    rb = ball.rigid_body
    rb.type = "ACTIVE"; rb.kinematic = True; rb.collision_shape = "SPHERE"; rb.mass = 7.0
    rb.restitution = 0.3; rb.collision_margin = 0.002
    # 핀 데크, 킥백, 피트
    passive_box("deck", (0, HEAD_Y + 0.6, -0.01), (1.06, 2.2, 0.02))
    passive_box("pit_floor", (0, LEN + 1.4, -0.35), (2.2, 2.0, 0.05))
    for s in (-1, 1):
        passive_box(f"kick{s}", (s * 0.68, HEAD_Y + 0.9, 0.35), (0.04, 3.0, 0.8))
        passive_box(f"gutfloor{s}", (s * 0.65, HEAD_Y, -0.08), (0.22, 3.0, 0.02))
    passive_box("curtain", (0, LEN + 2.2, 0.6), (2.2, 0.05, 1.4))


def lights_world():
    sc = bpy.context.scene
    world = bpy.data.worlds.new("w")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.82, 0.85, 0.9, 1)
    bg.inputs["Strength"].default_value = 0.22
    # 천장 조명 줄
    for y in range(-8, 20, 3):
        for x in (-3, -1, 1, 3):
            ld = bpy.data.lights.new(f"L{x}_{y}", "AREA")
            ld.shape = "RECTANGLE"; ld.size = 1.4; ld.size_y = 0.35
            ld.energy = 110; ld.color = (1.0, 0.96, 0.9)
            lo = bpy.data.objects.new(ld.name, ld)
            lo.location = (x, y, 3.6)
            bpy.context.collection.objects.link(lo)
    # 핀 데크 조명 (핀이 빛나 보이게)
    ld = bpy.data.lights.new("deck", "AREA"); ld.size = 2.2; ld.size_y = 0.5; ld.energy = 220
    lo = bpy.data.objects.new("deck", ld); lo.location = (0, HEAD_Y - 0.8, 1.4)
    lo.rotation_euler = (math.radians(-35), 0, 0)
    bpy.context.collection.objects.link(lo)


def cam(name, loc, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    c = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(c)
    c.location = loc
    return c


def track(c, target):
    t = c.constraints.new("TRACK_TO")
    t.target = target; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"


def cameras(root, ball):
    sc = bpy.context.scene
    # A: 볼러 뒤 오른쪽 낮은 앵글, 함께 전진
    tgtA = bpy.data.objects.new("tgtA", None); bpy.context.collection.objects.link(tgtA)
    a = cam("camA", (0, 0, 0), 32)
    for f, y in ((0, -4.4), (24, -4.4), (112, -0.95), (126, -0.75), (132, -0.7)):
        key(a, "location", f, Vector((0.6, y - 3.2, 1.4)))
        key(tgtA, "location", f, Vector((0.05, y + 3.0, 0.45)))
    track(a, tgtA)
    a.data.dof.use_dof = True; a.data.dof.focus_object = root; a.data.dof.aperture_fstop = 4.0
    # B: 볼 뒤를 낮게 따라가는 추적 카메라
    b = cam("camB", (-0.18, -1.6, 0.22), 50)
    cl = b.constraints.new("COPY_LOCATION"); cl.target = ball; cl.use_offset = True
    cl.use_z = False
    track(b, ball)
    b.data.dof.use_dof = True; b.data.dof.focus_object = ball; b.data.dof.aperture_fstop = 2.2
    # C: 핀 데크 옆 앞쪽, 충돌 슬로모션
    tgtC = bpy.data.objects.new("tgtC", None); bpy.context.collection.objects.link(tgtC)
    tgtC.location = (-0.05, HEAD_Y + 0.4, 0.18)
    c = cam("camC", (0.4, HEAD_Y - 1.3, 0.24), 30)
    track(c, tgtC)
    c.data.dof.use_dof = True; c.data.dof.focus_object = tgtC; c.data.dof.aperture_fstop = 3.5
    for f, cc in ((0, a), (134, b), (208, c)):
        mk = sc.timeline_markers.new(cc.name, frame=f); mk.camera = cc
    sc.camera = a


def setup_render(preview):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 10 if preview else 48
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 0
    sc.render.resolution_x, sc.render.resolution_y = (360, 640) if preview else (1080, 1920)
    sc.render.resolution_percentage = 100
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.45
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    sc.view_settings.exposure = 0.0
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"


def parse_frames(spec):
    out = set()
    for part in spec.split(","):
        rng, _, step = part.partition(":")
        a, _, b = rng.partition("-")
        a = int(a); b = int(b or a); step = int(step or 1)
        out.update(range(a, b + 1, step))
    return sorted(out)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out_dir = argv[0]
    frames = parse_frames(argv[1])
    preview = "--preview" in argv
    os.makedirs(out_dir, exist_ok=True)
    sc = build()
    setup_render(preview)
    want = set(frames)
    # 물리 캐시가 이어지도록 0부터 차례로 진행하며 필요한 프레임만 렌더
    for f in range(0, max(frames) + 1):
        sc.frame_set(f)
        if f in want:
            sc.render.filepath = os.path.join(out_dir, f"{f:04d}.png")
            bpy.ops.render.render(write_still=True)
            print("rendered", f, flush=True)
