"""EP.05 블록 리메이크 애니메이션. 샷 타이밍은 timeline.json(초 단위)을 따른다.
사용법: python anim_ep05.py TIMELINE.json OUT_DIR FRAMES   (FRAMES 예: 0,5,10 또는 0-100)
환경변수: RW, RH (해상도), SPP (샘플 수)
"""
import json
import math
import os
import sys

import bpy
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import world as W  # noqa: E402

R = math.radians
FPS = 24
tl = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
SHOTS = [(s["name"], round(s["start"] * FPS), round(s["end"] * FPS)) for s in tl["shots"]]

bpy.ops.wm.read_factory_settings(use_empty=True)
xs = W.alley(5)
L = W.L
PINS = W.pin_set(0)
PINS_C = W.pin_set(-W.PITCH, "c")
for x in xs:
    if x not in (0, -W.PITCH):
        W.pin_set(x, f"o{x}")
P0 = {p.name: p.location.copy() for p in PINS + PINS_C}
A = W.character((0.18, -4.0, 0), math.pi, "nervous")
B = W.character((0.18 - W.PITCH, -4.0, 0), math.pi, "smile", shirt=(70, 190, 160), hair="cap")
FACE = {"A": "nervous", "B": "smile"}
BALL = W.ball()
BALL_B = W.ball(rgb=(40, 110, 255), slash=None)
BR = 0.17
sweat = W.box((0, 0, -5), (0.05, 0.05, 0.08), (120, 200, 255), 0.02, 0.1)
W.lights_world()
cam = W.camera()
sc = W.setup_render(int(os.environ.get("RW", 1080)), int(os.environ.get("RH", 1920)), int(os.environ.get("SPP", 32)))
Y0, YF, REL_U = -4.0, -0.6, 0.86


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def keys(u, pts):
    if u <= pts[0][0]:
        return pts[0][1]
    for (u0, v0), (u1, v1) in zip(pts, pts[1:]):
        if u <= u1:
            return v0 + (v1 - v0) * smooth((u - u0) / (u1 - u0))
    return pts[-1][1]


def face(J, key, kind):
    if FACE[key] != kind:
        W.set_face(J, kind)
        FACE[key] = kind


def reset(J, x, y=Y0):
    J["root"].location = (x, y, 0)
    J["root"].rotation_euler = (0, 0, math.pi)
    for k in ("hips", "head", "legL", "legR", "shL", "shR"):
        J[k].rotation_euler = (0, 0, 0)
    J["root"].scale = (1, 1, 1)


def hold(J):
    """볼을 가슴 앞에 든 자세"""
    J["shR"].rotation_euler = (R(-35), 0, R(8))
    J["shL"].rotation_euler = (R(-35), 0, R(-8))


def ball_at_chest(J, ball):
    bpy.context.view_layer.update()
    ball.location = J["root"].matrix_world @ Vector((0, -0.42, 0.62))


def hand_pos(J):
    bpy.context.view_layer.update()
    sh = J["shR"].matrix_world.translation
    h = J["handR"].matrix_world.translation
    return h + (h - sh).normalized() * (BR * 0.9)


def idle(J, x, t, nervous=False):
    reset(J, x)
    hold(J)
    J["root"].location.z = 0.015 * abs(math.sin(t * (7 if nervous else 3)))
    if nervous:
        J["root"].rotation_euler.z = math.pi + 0.03 * math.sin(t * 23)
        J["head"].rotation_euler = (0, 0, 0.18 * math.sin(t * 3.5))
    else:
        J["head"].rotation_euler = (0.04 * math.sin(t * 1.5), 0, 0.1 * math.sin(t * 1.1))


def show_sweat(J, t, on=True):
    if not on:
        sweat.location = (0, 0, -5)
        return
    k = (t * 0.9) % 1
    bpy.context.view_layer.update()
    sweat.location = J["head"].matrix_world @ Vector((-0.36, -0.1, 0.5 - 0.35 * k))


def approach(J, x, u):
    reset(J, x)
    y = Y0 + (YF - Y0) * min(1, u / 0.9) ** 1.2
    J["root"].location = (x, y, -0.03 * smooth((u - 0.7) / 0.2))
    J["hips"].rotation_euler.x = R(-20) * smooth((u - 0.6) / 0.3)
    ph = min(u, 0.75) / 0.75 * 4 * math.pi
    amp = R(26) * (1 - smooth((u - 0.7) / 0.1))
    k = smooth((u - 0.7) / 0.2)
    J["legL"].rotation_euler.x = amp * math.sin(ph) + R(35) * k
    J["legR"].rotation_euler.x = -amp * math.sin(ph) - R(55) * k
    a = keys(u, [(0, 35), (0.18, 50), (0.38, -5), (0.62, -75), (0.82, 5), (REL_U, 35), (1.0, 125)])
    J["shR"].rotation_euler = (R(a), 0, 0)
    J["shL"].rotation_euler = (R(-20) * (1 - smooth((u - 0.3) / 0.3)), R(-75) * smooth((u - 0.3) / 0.4), 0)


def path(s, x0, lane_x=0.0):
    a = Vector((x0, 0.4, BR))
    m = Vector((lane_x + 0.42, L * 0.62, BR))
    b = Vector((lane_x + 0.06, L - 0.95, BR))
    return (1 - s) ** 2 * a + 2 * (1 - s) * s * m + s * s * b


def pins_pose(pins, t_after, lane_x=0.0, standing=(9,)):
    hit = Vector((lane_x + 0.06, L - 0.86, 0))
    for i, p in enumerate(pins):
        base = P0[p.name]
        p.rotation_mode = "QUATERNION"
        p.location = base.copy()
        p.rotation_quaternion = Quaternion()
        if i in standing or t_after <= 0:
            continue
        d = base - hit
        d.z = 0
        dist = d.length
        d = (d.normalized() if dist > 1e-3 else Vector((0, 1, 0))) + Vector((0, 0.6, 0))
        d.normalize()
        k = smooth((t_after - dist / 3.0) / 0.35)
        if k <= 0:
            continue
        p.rotation_quaternion = Quaternion(Vector((0, 0, 1)).cross(d).normalized(), math.pi / 2 * k + 0.25 * k * (i % 3))
        p.location = base + d * 0.4 * k + Vector((0, 0, 0.08 * math.sin(math.pi * k)))


def frame(f):
    name, f0, f1 = next(s for s in SHOTS if s[1] <= f < s[2]) if f < SHOTS[-1][2] else SHOTS[-1]
    t = (f - f0) / FPS
    ax, bx = 0.18, 0.18 - W.PITCH
    reset(A, ax)
    reset(B, bx)
    hold(A)
    hold(B)
    show_sweat(A, t, False)
    BALL_B.location = (bx, -4.42, 0.62)
    pins_pose(PINS, 0)
    pins_pose(PINS_C, 0, -W.PITCH)
    BALL.rotation_euler = (0, 0, 0)
    BALL_B.rotation_euler = (0, 0, 0)
    face(A, "A", "nervous")
    if name == "hook":
        idle(A, ax, t, True)
        idle(B, bx, t)
        show_sweat(A, t)
        W.look(cam, (0.75, -1.3, 1.5), (0.18, -4.0, 0.95), 30 + 1.2 * t)
    elif name == "intro":
        idle(A, ax, t, True)
        idle(B, bx, t)
        a = 0.4 * math.sin(t * 0.45)
        W.look(cam, (0.18 + 3.0 * math.sin(a), -4.0 + 3.0 * math.cos(a), 1.5), (0.18, -4.0, 0.9), 30)
    elif name == "compare":
        idle(A, ax, t, True)
        idle(B, bx, t)
        show_sweat(A, t)
        W.look(cam, (-0.82, -8.8 + 0.15 * t, 2.7), (-0.82, -2.5, 0.7), 28)
    elif name == "mind":
        idle(A, ax, t, True)
        show_sweat(A, t)
        W.look(cam, (0.5, -2.2 - 0.05 * t, 1.3), (0.18, -4.0, 1.05), 36)
    elif name == "slowmo":
        face(A, "A", "focus")
        n = f1 - f0
        u = min(1.0, (f - f0) / (n * 0.82))
        approach(A, ax, u)
        if u <= REL_U:
            BALL.location = hand_pos(A)
        else:
            approach(A, ax, REL_U)
            p0 = hand_pos(A)
            approach(A, ax, u)
            s = (u - REL_U) / (1 - REL_U) * 0.12
            BALL.location = path(s, p0.x)
            BALL.rotation_euler = (-(u - REL_U) * 30, 0, 0)
        ry = A["root"].location.y
        w = smooth((u - REL_U) / (1 - REL_U))      # 릴리스 후에는 카메라가 볼을 따라감
        by = BALL.location.y
        ty = (ry + 0.5) * (1 - w) + (by - 0.3) * w
        W.look(cam, (3.3, ty - 1.9, 1.15), (0.3 + 0.1 * w, ty, 0.5 - 0.2 * w), 30)
    elif name == "pins":
        hit_t = 0.9
        s = 0.72 + 0.28 * min(1, t / hit_t)
        pb = path(s, 0.3)
        if t >= hit_t:
            pb = Vector((0.06 + 0.2 * (t - hit_t), L - 0.95 + 1.6 * (t - hit_t), BR))
        BALL.location = pb
        BALL.rotation_euler = (-f * 0.5, 0, 0)
        pins_pose(PINS, t - hit_t)
        W.look(cam, (-1.1, L - 4.6, 0.75), (0.15, L - 0.8, 0.25), 34)
    elif name == "speed":
        s = min(1.0, 0.05 + t / 6.4)
        BALL.location = path(s, 0.3)
        BALL.rotation_euler = (-f * 0.5, 0, 0)
        BALL_B.location = path(s, 0.3 - W.PITCH, -W.PITCH)
        BALL_B.rotation_euler = (-f * 0.5, 0, 0)
        A["root"].location.z = -5
        B["root"].location.z = -5
        y = path(s, 0.3).y
        W.look(cam, (-W.PITCH / 2, y - 5.5, 1.6), (-W.PITCH / 2, y + 2.5, 0.0), 27)
    else:  # summary
        face(A, "A", "smile")
        idle(A, ax, t)
        W.look(cam, (0.75, -1.3, 1.5), (0.18, -4.0, 0.95), 31)
    if name not in ("slowmo", "pins", "speed"):
        ball_at_chest(A, BALL)
        ball_at_chest(B, BALL_B) if name != "mind" else None


def parse(spec):
    out = []
    for part in spec.split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b) + 1)) if b else [int(a)]
    return out


if __name__ == "__main__":
    for f in parse(sys.argv[3]):
        frame(f)
        sc.render.filepath = os.path.join(OUT, f"{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        print("frame", f, flush=True)
