"""볼링 캐릭터 릴스 3D 장면 렌더 (Blender Workbench). 프레임 PNG 를 out/ 에 저장.
사용: python anim.py START END  (프레임 범위, 끝 포함 안 함)"""
import bpy, math, sys, os
from mathutils import Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scene import *

FPS = 24
OUT = os.environ.get("OUT", "/home/claude/b3d/out")
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
W_, H_ = int(os.environ.get("RW", 1080)), int(os.environ.get("RH", 1920))
sc = setup_render(W_, H_)
w = bpy.data.worlds.new("W"); sc.world = w; w.color = (0.85, 0.88, 0.93)
L = 18.3
XS = alley(5, L)
for i, x in enumerate(XS):
    if x != 0: pins_at(x, L, tag=f"o{i}")
PINS = pins_at(0, L)
PIN0 = [p.location.copy() for p in PINS]
root, head, arms, legs = character(origin=(0.18, -4.0, 0))
root.rotation_euler = (0, 0, math.pi)
BALL = ball(loc=(0, 0, 0), rgb=(30, 60, 200))
sweat = sphere("sweat", (0, 0, 0), (0.035, 0.03, 0.05), mat("sweat", (150, 210, 255), 0.05))
sweat.hide_render = True
cam = camera((0, -1, 1.5), (0, -4, 1.4), lens=32)

def smooth(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def keys(u, pts):
    """pts: [(u, value)] 사이를 부드럽게 보간"""
    if u <= pts[0][0]: return pts[0][1]
    for (u0, v0), (u1, v1) in zip(pts, pts[1:]):
        if u <= u1:
            k = smooth((u - u0) / (u1 - u0)); return v0 + (v1 - v0) * k
    return pts[-1][1]

def look(loc, target, lens=32):
    cam.location = loc; cam.data.lens = lens
    d = Vector(target) - Vector(loc)
    cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = d.to_track_quat('-Z', 'Y')

def reset_pose(y=-4.0):
    root.location = (0.18, y, 0); root.rotation_euler = (0, 0, math.pi)
    for s in (-1, 1):
        arms[s].rotation_euler = (0, 0, 0); legs[s].rotation_euler = (0, 0, 0)
    head.rotation_euler = (0, 0, 0)

# 투구 동작: u 0~1 (5스텝 어프로치 + 슬라이드 + 팔로스루)
Y0, YF = -4.0, -0.35
REL_U = 0.86

def approach_pose(u):
    reset_pose()
    y = Y0 + (YF - Y0) * min(1, u / 0.9) ** 1.25
    root.location = (0.18, y, -0.17 * smooth((u - 0.7) / 0.2))
    root.rotation_euler = (0.28 * smooth((u - 0.6) / 0.3), 0, math.pi)
    ph = min(u, 0.75) / 0.75 * 4 * math.pi
    amp = 0.45 * (1 - smooth((u - 0.7) / 0.1))
    legs[1].rotation_euler.x = amp * math.sin(ph)
    legs[-1].rotation_euler.x = -amp * math.sin(ph)
    k = smooth((u - 0.7) / 0.2)
    legs[1].rotation_euler.x += -0.55 * k      # 왼발 슬라이드 (앞으로)
    legs[-1].rotation_euler.x += 1.0 * k       # 오른발 뒤로
    arms[-1].rotation_euler.x = keys(u, [(0, -0.35), (0.18, -0.55), (0.38, 0.1), (0.62, 1.45),
                                          (0.82, 0.05), (REL_U, -0.5), (1.0, -2.3)])
    arms[1].rotation_euler.y = -1.1 * smooth((u - 0.3) / 0.4)
    arms[1].rotation_euler.x = -0.3 * smooth((u - 0.5) / 0.3)

def hand_ball_pos():
    bpy.context.view_layer.update()
    sh = arms[-1].matrix_world.translation
    hand = bpy.data.objects["hand-1"].matrix_world.translation
    d = (hand - sh).normalized()
    return hand + d * 0.12

def place_ball(p, spin=0.0):
    BALL.location = p
    BALL.rotation_mode = 'XYZ'; BALL.rotation_euler = (spin, 0, 0)

def ball_path(s, p0):
    """릴리스 후 s 0~1 동안 레인 위 훅 궤적 (베지어)"""
    a = Vector((p0.x, p0.y + 0.4, 0.109)); c = Vector((0.5, L * 0.62, 0.109)); b = Vector((0.06, L - 0.95, 0.109))
    q = (1 - s) ** 2 * a + 2 * (1 - s) * s * c + s * s * b
    return q

def pins_pose(t_after, standing=(9,)):
    """충돌 후 t_after 초. standing 에 든 핀은 서 있음."""
    hit = Vector((0.06, L - 0.86, 0))
    for i, (p, base) in enumerate(zip(PINS, PIN0)):
        p.rotation_mode = 'QUATERNION'; p.location = base.copy(); p.rotation_quaternion = Quaternion()
        if i in standing or t_after <= 0:
            continue
        d = (base - hit); d.z = 0
        dist = d.length
        d = (d.normalized() if dist > 1e-3 else Vector((0, 1, 0))) + Vector((0, 0.6, 0))
        d.normalize()
        delay = dist / 3.0
        k = smooth((t_after - delay) / 0.35)
        if k <= 0: continue
        axis = Vector((0, 0, 1)).cross(d).normalized()
        p.rotation_quaternion = Quaternion(axis, (math.pi / 2) * k + 0.4 * k * (i % 3) / 2)
        p.location = base + d * 0.35 * k + Vector((0, 0, 0.05 * math.sin(math.pi * k)))

# ---------- 샷 구성 ----------
SHOTS = [("A", 0, 72), ("B", 72, 180), ("C", 180, 312), ("D", 312, 420), ("E", 420, 600)]
APPROACH_F = 62     # 어프로치 프레임 수 (C 샷)
TRAVEL_F = 50       # 볼이 핀까지 가는 프레임 수

def frame(f):
    shot = next(s for s in SHOTS if s[1] <= f < s[2])
    name, f0, f1 = shot; t = (f - f0) / FPS
    sweat.hide_render = True
    pins_pose(0)
    if name == "A":
        reset_pose()
        root.location.z = 0.02 * math.sin(t * 3)
        head.rotation_euler = (0.05 * math.sin(t * 2), 0, 0.15 * math.sin(t * 1.3))
        place_ball(hand_ball_pos())
        look((0.9, -1.55, 1.75), (0.18, -4.0, 1.55 - 0.05 * t), lens=34 + t * 2)
    elif name == "B":
        reset_pose()
        root.location.z = 0.015 * math.sin(t * 6)
        head.rotation_euler = (0.08, 0, 0.25 * math.sin(t * 4))   # 두리번
        place_ball(hand_ball_pos())
        sweat.hide_render = False
        k = (t * 0.8) % 1
        sweat.location = (0.18 - 0.40, -4.0 - 0.18, 2.15 - 0.4 * k)
        look((0.18 + 0.5 * math.sin(t * 0.4), -4.0 + 2.6 - 0.1 * t, 1.8), (0.18, -4.0, 1.6), lens=34 + 1.5 * t)
    elif name == "C":
        i = f - f0
        if i < APPROACH_F:
            u = i / APPROACH_F * (REL_U + 0.02)
            approach_pose(u)
            place_ball(hand_ball_pos())
            look((1.6, root.location.y - 2.6, 1.8), (0.1, root.location.y + 1.6, 0.8), lens=30)
        else:
            j = i - APPROACH_F
            u = min(1.0, REL_U + 0.02 + j / 20 * (1 - REL_U))
            approach_pose(u)
            approach_pose(REL_U + 0.02)
            p0 = hand_ball_pos()
            approach_pose(u)
            s = min(1.0, j / TRAVEL_F)
            pb = ball_path(s, p0)
            place_ball(pb, spin=-j * 0.6)
            if s >= 1: pins_pose((j - TRAVEL_F) / FPS)
            look((pb.x + 0.45, pb.y - 2.4, 0.85), (pb.x, pb.y + 3, 0.2), lens=34)
    elif name == "D":
        # 핀 쪽에서 본 충돌 리플레이
        hit_t = 0.9
        if t < hit_t:
            s = 0.75 + 0.25 * (t / hit_t)
        else:
            s = 1.0
        pb = ball_path(s, Vector((0.3, -0.2, 0.1)))
        if t >= hit_t:
            pb = Vector((0.06 + 0.2 * (t - hit_t), L - 0.95 + 1.6 * (t - hit_t), 0.109))
        place_ball(pb, spin=-f * 0.6)
        pins_pose(t - hit_t)
        look((-1.1, L - 3.6, 0.55), (0.2, L - 0.7, 0.25), lens=40)
    elif name == "E":
        reset_pose(YF)
        root.location = (0.18, YF, 0)
        root.rotation_euler = (0, 0, math.pi - 0.0)
        br = 0.03 * math.sin(t * 1.6)
        bpy.data.objects["torso"].scale = (1 + br, 1 + br, 1)
        head.rotation_euler = (-0.1, 0, 0.1 * math.sin(t * 0.7))
        place_ball(Vector((0, L - 0.3, 0.109)))
        pins_pose(5)
        look((0.18 + 0.6, YF + 2.4, 1.7), (0.18, YF, 1.55), lens=40)
    bpy.data.objects["torso"].scale = bpy.data.objects["torso"].scale if name == "E" else (1, 1, 1)

if __name__ == "__main__":
    a, b = int(sys.argv[-2]), int(sys.argv[-1])
    for f in range(a, b):
        frame(f)
        sc.render.filepath = f"{OUT}/{f:04d}.png"
        bpy.ops.render.render(write_still=True)
        print("frame", f, flush=True)
