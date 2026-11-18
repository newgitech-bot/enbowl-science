"""EP.05 v4: 확장판 캐릭터 릴스 (약 44초). python anim2.py START END"""
import bpy, math, sys, os, random
from mathutils import Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scene import *

FPS = 24
OUT = os.environ.get("OUT", "/home/claude/b3d/out2")
os.makedirs(OUT, exist_ok=True)
CS = 0.72            # 캐릭터 크기 (레인·핀·볼은 실제 비율)
BR = 0.13            # 볼 반지름 (실제보다 살짝 크게)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = setup_render(int(os.environ.get("RW", 1080)), int(os.environ.get("RH", 1920)))
sc.display.render_aa = os.environ.get("AA", "8")
w = bpy.data.worlds.new("W"); sc.world = w; w.color = (0.85, 0.88, 0.93)
L = 18.3
XS = alley(5, L)
OTHER = {}
for i, x in enumerate(XS):
    if x not in (0, -PITCH): pins_at(x, L, tag=f"o{i}")
PINS = pins_at(0, L)
PINS_C = pins_at(-PITCH, L, tag="c")
P0 = {id(p): p.location.copy() for p in PINS + PINS_C}

def make_char(name, x):
    root, head, arms, legs = character(name=name, origin=(x + 0.18, -4.0, 0))
    root.scale = (CS, CS, CS)
    root.rotation_euler = (0, 0, math.pi)
    return dict(root=root, head=head, arms=arms, legs=legs, x=x, hand=None)

A = make_char("bowler", 0.0)          # 압박 조건 (주인공)
B = make_char("calm", -PITCH)         # 편한 조건
for c in (A, B):
    c["hand"] = [o for o in c["root"].children_recursive if o.name.startswith("hand-1")][0]
    c["torso"] = [o for o in c["root"].children_recursive if o.name.startswith("torso") and not o.name.startswith("torso_")][0]
BALL = ball("ballA", rgb=(30, 60, 200), r=BR)
BALL_B = ball("ballB", rgb=(0, 160, 120), r=BR)
sweat = sphere("sweat", (0, 0, 0), (0.026, 0.022, 0.038), mat("sweat", (150, 210, 255), 0.05))
cam = camera((0, -1, 1.5), (0, -4, 1.4), lens=32)

def smooth(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def keys(u, pts):
    if u <= pts[0][0]: return pts[0][1]
    for (u0, v0), (u1, v1) in zip(pts, pts[1:]):
        if u <= u1: return v0 + (v1 - v0) * smooth((u - u0) / (u1 - u0))
    return pts[-1][1]

def look(loc, target, lens=32):
    cam.location = loc; cam.data.lens = lens
    cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y')

def reset(c, y=-4.0):
    c["root"].location = (c["x"] + 0.18, y, 0); c["root"].rotation_euler = (0, 0, math.pi)
    for s in (-1, 1):
        c["arms"][s].rotation_euler = (0, 0, 0); c["legs"][s].rotation_euler = (0, 0, 0)
    c["head"].rotation_euler = (0, 0, 0); c["torso"].scale = (1, 1, 1)

Y0, YF, REL_U = -4.0, -0.4, 0.86

def approach(c, u):
    reset(c)
    r = c["root"]
    y = Y0 + (YF - Y0) * min(1, u / 0.9) ** 1.25
    r.location = (c["x"] + 0.18, y, -0.12 * smooth((u - 0.7) / 0.2))
    r.rotation_euler = (0.28 * smooth((u - 0.6) / 0.3), 0, math.pi)
    ph = min(u, 0.75) / 0.75 * 4 * math.pi
    amp = 0.45 * (1 - smooth((u - 0.7) / 0.1))
    k = smooth((u - 0.7) / 0.2)
    c["legs"][1].rotation_euler.x = amp * math.sin(ph) - 0.55 * k
    c["legs"][-1].rotation_euler.x = -amp * math.sin(ph) + 1.0 * k
    c["arms"][-1].rotation_euler.x = keys(u, [(0, -0.35), (0.18, -0.55), (0.38, 0.1), (0.62, 1.45),
                                              (0.82, 0.05), (REL_U, -0.5), (1.0, -2.3)])
    c["arms"][1].rotation_euler.y = -1.1 * smooth((u - 0.3) / 0.4)
    c["arms"][1].rotation_euler.x = -0.3 * smooth((u - 0.5) / 0.3)

def hand_pos(c):
    bpy.context.view_layer.update()
    sh = c["arms"][-1].matrix_world.translation
    h = c["hand"].matrix_world.translation
    return h + (h - sh).normalized() * (0.06 + BR * 0.85)

def path(s, x0, lane_x=0.0):
    a = Vector((x0, 0.4, BR)); m = Vector((lane_x + 0.48, L * 0.62, BR)); b = Vector((lane_x + 0.06, L - 0.95, BR))
    return (1 - s) ** 2 * a + 2 * (1 - s) * s * m + s * s * b

def pins_pose(pins, t_after, lane_x=0.0, standing=(9,)):
    hit = Vector((lane_x + 0.06, L - 0.86, 0))
    for i, p in enumerate(pins):
        base = P0[id(p)]
        p.rotation_mode = 'QUATERNION'; p.location = base.copy(); p.rotation_quaternion = Quaternion()
        if i in standing or t_after <= 0: continue
        d = base - hit; d.z = 0; dist = d.length
        d = (d.normalized() if dist > 1e-3 else Vector((0, 1, 0))) + Vector((0, 0.6, 0)); d.normalize()
        k = smooth((t_after - dist / 3.0) / 0.35)
        if k <= 0: continue
        p.rotation_quaternion = Quaternion(Vector((0, 0, 1)).cross(d).normalized(), math.pi / 2 * k + 0.2 * k * (i % 3))
        p.location = base + d * 0.35 * k + Vector((0, 0, 0.05 * math.sin(math.pi * k)))

def idle(c, t, nervous=False):
    reset(c)
    c["root"].location.z = 0.012 * math.sin(t * (6 if nervous else 3))
    if nervous:
        c["root"].rotation_euler.z = math.pi + 0.025 * math.sin(t * 23)
        c["head"].rotation_euler = (0.06, 0, 0.3 * math.sin(t * 3.5))
    else:
        c["head"].rotation_euler = (0.03 * math.sin(t * 1.5), 0, 0.1 * math.sin(t * 1.1))
    br = 0.03 * math.sin(t * (4 if nervous else 1.6))
    c["torso"].scale = (1 + br, 1 + br, 1)

def show_sweat(c, t, on=True):
    sweat.hide_render = not on
    if on:
        k = (t * 0.8) % 1
        hx = c["x"] + 0.18
        sweat.location = (hx - 0.30 * CS * 1.0, -4.0 - 0.13, 1.42 * CS + 0.62 * CS - 0.3 * k)

# ---------- 샷 (시작 프레임, 끝 프레임) ----------
SHOTS = [("hook", 0, 72), ("intro", 72, 192), ("compare", 192, 360), ("mind", 360, 480),
         ("slowmo", 480, 648), ("pins", 648, 768), ("speed", 768, 912), ("summary", 912, 1104)]

def frame(f):
    name, f0, f1 = next(s for s in SHOTS if s[1] <= f < s[2])
    t = (f - f0) / FPS
    for c in (A, B): reset(c)
    sweat.hide_render = True
    BALL_B.location = (-PITCH, -6, -5)
    pins_pose(PINS, 0); pins_pose(PINS_C, 0, -PITCH)
    BALL.location = hand_pos(A)
    if name == "hook":
        idle(A, t, nervous=True); idle(B, t); show_sweat(A, t)
        BALL.location = hand_pos(A)
        look((0.7, -1.0, 1.45), (0.18, -4.0, 0.98 - 0.02 * t), lens=31 + 1.0 * t)
    elif name == "intro":
        idle(A, t, nervous=True); idle(B, t)
        BALL.location = hand_pos(A)
        a = 0.35 * math.sin(t * 0.45)
        look((0.18 + 3.2 * math.sin(a), -4.0 + 3.2 * math.cos(a), 1.55), (0.18, -4.0, 0.9), lens=32)
    elif name == "compare":
        idle(A, t, nervous=True); idle(B, t); show_sweat(A, t)
        BALL.location = hand_pos(A)
        BALL_B.location = hand_pos(B)
        look((-PITCH / 2 + 0.18, -9.0 + 0.15 * t, 2.6), (-PITCH / 2 + 0.18, -3.2, 0.75), lens=30)
    elif name == "mind":
        idle(A, t, nervous=True); show_sweat(A, t)
        BALL.location = hand_pos(A)
        look((0.6, -1.3 - 0.06 * t, 1.35), (0.18, -4.0, 1.0), lens=32)
    elif name == "slowmo":
        n = f1 - f0; i = f - f0
        u = min(1.0, i / (n * 0.82))
        approach(A, u)
        if u <= REL_U:
            BALL.location = hand_pos(A)
        else:
            approach(A, REL_U); p0 = hand_pos(A); approach(A, u)
            s = (u - REL_U) / (1 - REL_U) * 0.12
            BALL.location = path(s, p0.x)
            BALL.rotation_euler = (-(u - REL_U) * 30, 0, 0)
        ry = A["root"].location.y
        look((2.6, ry - 0.3, 0.9), (0.18, ry + 0.2, 0.55), lens=32)
    elif name == "pins":
        hit_t = 0.9
        s = 0.72 + 0.28 * min(1, t / hit_t)
        pb = path(s, 0.3)
        if t >= hit_t: pb = Vector((0.06 + 0.2 * (t - hit_t), L - 0.95 + 1.6 * (t - hit_t), BR))
        BALL.location = pb; BALL.rotation_euler = (-f * 0.5, 0, 0)
        pins_pose(PINS, t - hit_t)
        look((-1.1, L - 3.6, 0.6), (0.2, L - 0.7, 0.25), lens=40)
    elif name == "speed":
        s = min(1.0, 0.05 + t / 6.4)
        BALL.location = path(s, 0.3); BALL.rotation_euler = (-f * 0.5, 0, 0)
        BALL_B.location = path(s, 0.3 - PITCH, -PITCH); BALL_B.rotation_euler = (-f * 0.5, 0, 0)
        for c in (A, B): c["root"].location = (c["x"] + 0.18, YF, -5)   # 화면 밖
        y = path(s, 0.3).y
        look((-PITCH / 2, y - 5.5, 1.5), (-PITCH / 2, y + 2.5, 0.0), lens=27)
    elif name == "summary":
        idle(A, t)
        BALL.location = hand_pos(A)
        look((0.7, -1.0, 1.45), (0.18, -4.0, 0.98), lens=31)

if __name__ == "__main__":
    a, b = int(sys.argv[-2]), int(sys.argv[-1])
    step = int(os.environ.get("STEP", 1))
    for f in range(a, b):
        name = next(s for s in SHOTS if s[1] <= f < s[2])[0]
        # 정리 카드 뒤 장면은 2프레임마다 렌더하고 복사
        if name == "summary" and f % 2 == 1:
            continue
        if step > 1 and f % step: continue
        frame(f)
        sc.render.filepath = f"{OUT}/{f:04d}.png"
        bpy.ops.render.render(write_still=True)
        print("frame", f, flush=True)
