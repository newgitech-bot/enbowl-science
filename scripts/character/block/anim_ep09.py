"""EP.09 우레탄 볼 경도 규정 릴스 애니메이션. 샷 타이밍은 timeline.json(초 단위)을 따른다.
사용법: python anim_ep09.py TIMELINE.json OUT_DIR FRAMES   (FRAMES 예: 0,5,10 또는 0-100)
환경변수: RW, RH (해상도), SPP (샘플 수)
샷: hook(경도 검사대) · why(두 레인 위에서 본 무른 볼/단단한 볼) · soak(용제 통) · recover(검사대 반복 측정)
    rule(볼 거치대 따라가기) · field(볼 100개 격자, 1개만 빨강) · meaning(뒤에서 본 투구) · summary
"""
import json
import math
import os
import random
import sys

import bpy
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import world as W  # noqa: E402

random.seed(9)
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
BR = 0.17
GRAY = (120, 126, 142)

# ---------------- 경도 검사대 (x=0, y=-9.6) ----------------
TY = -9.6
W.box((0, TY, 0.75), (1.5, 0.75, 0.06), (245, 245, 248), 0.01)
for kx in (-1, 1):
    for ky in (-1, 1):
        W.box((0.68 * kx, TY + 0.3 * ky, 0.37), (0.05, 0.05, 0.74), (110, 110, 120), 0)
W.box((0, TY, 0.82), (0.5, 0.5, 0.08), (54, 58, 70), 0.01)                  # 받침
W.box((0, TY, 0.875), (0.2, 0.2, 0.03), (180, 184, 196), 0.005)            # 볼 컵
W.box((0, TY - 0.2, 1.24), (0.09, 0.09, 0.78), (190, 194, 206), 0.01)      # 기둥
W.box((0, TY - 0.1, 1.62), (0.09, 0.26, 0.08), (190, 194, 206), 0.01)      # 팔
W.box((0.17, TY + 0.252, 0.83), (0.14, 0.01, 0.05), (90, 255, 150), 0.003, emit=3.0)   # 화면
HEAD = W.empty("head_t", (0, TY, 1.42))
W.box((0, 0, 0.09), (0.15, 0.15, 0.2), (255, 114, 0), 0.015, P=HEAD)
W.box((0, 0, -0.04), (0.025, 0.025, 0.08), (40, 40, 44), 0.004, P=HEAD)
LED = W.box((0, 0.077, 0.13), (0.05, 0.01, 0.05), (255, 60, 60), 0.004, emit=4.0, P=HEAD)
BALL_Z = 0.89 + BR

# ---------------- 용제 통 (x=-2, y=-9.6) ----------------
BX = -W.PITCH
W.box((BX, TY, 0.75), (1.2, 0.75, 0.06), (245, 245, 248), 0.01)
for kx in (-1, 1):
    for ky in (-1, 1):
        W.box((BX + 0.55 * kx, TY + 0.3 * ky, 0.37), (0.05, 0.05, 0.74), (110, 110, 120), 0)
bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.3, depth=0.46, location=(BX, TY, 0.78 + 0.23))
bpy.context.object.data.materials.append(W.mat((235, 238, 244), 0.35, 0.3))
bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.27, depth=0.01, location=(BX, TY, 1.245))
bpy.context.object.data.materials.append(W.mat((40, 200, 255), 0.05, 0.8, emit=1.2))
bpy.ops.object.shade_smooth()
BUBBLES = [W.sphere((BX, TY, -5), 0.025 + 0.01 * (i % 3), (190, 230, 255), 0.05, 0.5, seg=12) for i in range(7)]
# 통 옆 시계 (15시간)
W.box((BX + 0.48, TY, 1.0), (0.26, 0.08, 0.26), (250, 250, 250), 0.02)
HAND_C = W.empty("clock_h", (BX + 0.48, TY + 0.045, 1.0))
W.box((0, 0, 0.05), (0.015, 0.01, 0.1), (30, 30, 34), 0, P=HAND_C)

# ---------------- 볼 100개 격자 (어프로치, 레인 0 ~ -2 사이) ----------------
GRID = []
PLAT = W.box((-1.0, -3.2, 0.06), (4.1, 4.1, 0.12), (245, 245, 248), 0.03)
cols = [(60, 70, 90), (70, 90, 120), (50, 60, 80), (90, 100, 130)]
for i in range(10):
    for j in range(10):
        red = (i, j) == (6, 3)
        c = (255, 50, 50) if red else random.choice(cols)
        o = W.sphere((-1.0 - 1.71 + i * 0.38, -4.9 + j * 0.38, 0.25), 0.13, c, 0.25, 0.6, seg=20)
        if red:
            RED = o
        GRID.append(o)
GLOW = W.box((-2.71 + 6 * 0.38, -4.9 + 3 * 0.38, 0.125), (0.34, 0.34, 0.01), (255, 80, 60), 0.0, emit=6.0)
GRID_OBJS = GRID + [GLOW, PLAT]


def grid_show(on):
    for o in GRID_OBJS:
        o.hide_render = not on


# ---------------- 캐릭터 ----------------
A = W.character((0.75, -9.2, 0), math.pi + 0.64, "smile")
O = W.character((-0.5, -10.2, 0), math.pi - 0.3, "smile", shirt=GRAY, hair="cap")
FACE = {"A": "smile"}
BALL = W.ball()                                   # 앤볼 볼(검사·투구)
SOFT = W.ball(rgb=(0, 170, 190), slash=None)      # 무른 볼
HARD = W.ball(rgb=(60, 64, 80), slash=None)       # 단단한 볼
SOAKB = W.ball(rgb=(150, 90, 220), slash=None)    # 용제에 담글 볼
W.lights_world()
cam = W.camera()
sc = W.setup_render(int(os.environ.get("RW", 1080)), int(os.environ.get("RH", 1920)), int(os.environ.get("SPP", 32)))
Y0, YF, REL_U = -4.0, -0.6, 0.86
HIDE = (0, 0, -6)


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


def reset(J, loc, rz):
    J["root"].location = loc
    J["root"].rotation_euler = (0, 0, rz)
    for k in ("hips", "head", "legL", "legR", "shL", "shR"):
        J[k].rotation_euler = (0, 0, 0)
    J["root"].scale = (1, 1, 1)


def hold(J):
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


def breathe(J, t, sp=2.5):
    J["root"].location.z = 0.012 * abs(math.sin(t * sp))
    J["head"].rotation_euler = (0.04 * math.sin(t * 1.3), 0, 0.1 * math.sin(t * 0.9))


def press(t, period=1.6, phase=0.0):
    """검사기 머리가 내려와 볼을 누르는 주기 동작. 0=위, 1=누름"""
    u = ((t - phase) % period) / period
    return keys(u, [(0, 0), (0.25, 1), (0.6, 1), (0.85, 0), (1, 0)])


def set_press(k):
    HEAD.location.z = 1.42 - 0.17 * k
    LED.data.materials[0] = W.mat((90, 255, 150) if k > 0.95 else (255, 60, 60), 0.7, emit=4.0)


def approach(J, x, u):
    reset(J, (x, Y0, 0), math.pi)
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


def path(s, x0, lane_x=0.0, bp=0.62, out=0.42, end=0.06):
    a = Vector((x0, 0.4, BR))
    m = Vector((lane_x + out, L * bp, BR))
    b = Vector((lane_x + end, L - 0.95, BR))
    return (1 - s) ** 2 * a + 2 * (1 - s) * s * m + s * s * b


def pins_pose(pins, t_after, lane_x=0.0, standing=(), hit_x=0.06):
    hit = Vector((lane_x + hit_x, L - 0.86, 0))
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


A_HOME = ((0.7, -9.35, 0), math.pi + 0.9)
O_HOME = ((-0.5, -10.2, 0), math.pi - 0.3)


def frame(f):
    name, f0, f1 = next(s for s in SHOTS if s[1] <= f < s[2]) if f < SHOTS[-1][2] else SHOTS[-1]
    t = (f - f0) / FPS
    dur = (f1 - f0) / FPS
    reset(A, *A_HOME)
    reset(O, *O_HOME)
    face(A, "A", "smile")
    for b in (BALL, SOFT, HARD, SOAKB):
        b.location = HIDE
        b.rotation_euler = (0, 0, 0)
    for b in BUBBLES:
        b.location = HIDE
    pins_pose(PINS, 0)
    pins_pose(PINS_C, 0, -W.PITCH)
    grid_show(False)
    set_press(0)
    HAND_C.rotation_euler = (0, 0, 0)
    O["shL"].rotation_euler = (R(-70), 0, R(-25))   # 검사기 쪽으로 손
    if name == "hook":
        BALL.location = (0, TY, BALL_Z)
        BALL.rotation_euler = (0, 0, R(-90))
        set_press(press(t, 2.2, 0.6))
        breathe(A, t)
        breathe(O, t + 1)
        A["head"].rotation_euler.z = R(-25)
        k = smooth(t / dur)
        W.look(cam, (-0.85 + 0.2 * k, -7.75, 1.7 - 0.15 * k), (0.12, TY - 0.15, 1.05), 28 + 6 * k)
    elif name == "why":
        A["root"].location.z = -6
        O["root"].location.z = -6
        hit_t = dur * 0.78
        s = min(1.0, t / hit_t)
        SOFT.location = path(s, 0.3, 0.0, bp=0.48, out=0.40, end=0.06)
        HARD.location = path(s, 0.3 - W.PITCH, -W.PITCH, bp=0.78, out=0.42, end=0.22)
        SOFT.rotation_euler = (-f * 0.5, 0, 0)
        HARD.rotation_euler = (-f * 0.5, 0, 0)
        if t >= hit_t:
            dt = t - hit_t
            SOFT.location = Vector((0.06 - 0.1 * dt, L - 0.95 + 1.6 * dt, BR))
            HARD.location = Vector((-W.PITCH + 0.22 + 0.05 * dt, L - 0.95 + 1.6 * dt, BR))
            pins_pose(PINS, dt)
            pins_pose(PINS_C, dt, -W.PITCH, standing=(2, 5, 9), hit_x=0.22)
        y = min(SOFT.location.y, L - 1.5)
        W.look(cam, (-1.0, y - 3.4, 3.5), (-1.0, y + 2.2, 0.0), 22)
    elif name == "soak":
        reset(A, (BX - 0.6, TY - 0.55, 0), math.pi - 0.5)
        face(A, "A", "wow")
        breathe(A, t, 4)
        A["shL"].rotation_euler = (R(-40), 0, R(-10))
        A["shR"].rotation_euler = (R(-40), 0, R(10))
        A["head"].rotation_euler.x = R(10)
        k = smooth(t / 1.6)
        SOAKB.location = (BX, TY, 1.62 - 0.62 * k)
        SOAKB.rotation_euler = (0, 0, R(30) * k)
        if t > 1.2:
            for i, b in enumerate(BUBBLES):
                u = ((t * 0.8 + i * 0.37) % 1)
                b.location = (BX + 0.17 * math.cos(i * 2.1), TY + 0.17 * math.sin(i * 2.1), 1.25 + 0.25 * u)
                b.scale = (1 - u,) * 3
        HAND_C.rotation_euler = (0, -smooth((t - 1.2) / (dur - 1.4)) * 2 * math.pi * 1.25, 0)
        a = R(-30) + R(40) * smooth(t / dur)
        W.look(cam, (BX + 1.9 * math.sin(a), TY + 1.9 * math.cos(a), 2.45), (BX + 0.1, TY - 0.2, 1.05), 30)
    elif name == "recover":
        BALL.location = HIDE
        SOAKB.location = (0, TY, BALL_Z)
        SOAKB.rotation_euler = (0, 0, R(-60))
        n = 3
        period = (dur - 0.6) / n
        set_press(press(t, period, 0.2) if t < dur - 0.4 else 0)
        breathe(O, t)
        breathe(A, t + 0.5)
        A["head"].rotation_euler.z = R(-30)
        W.look(cam, (-1.45, -8.55, 1.45), (0.0, TY, 0.98), 34)
    elif name == "rule":
        A["root"].location.z = -6
        O["root"].location.z = -6
        k = smooth(t / dur)
        x = (5 * W.PITCH + 8) / 2 - 0.5
        y = -6.6 + 3.4 * k
        W.look(cam, (x - 1.7, y - 1.0, 1.25), (x, y + 0.5, 0.85), 30)
    elif name == "field":
        grid_show(True)
        A["root"].location.z = -6
        O["root"].location.z = -6
        k = smooth(t / (dur * 0.8))
        gx, gy = -2.71 + 6 * 0.38, -4.9 + 3 * 0.38
        cz = 0.9 + 2.5 * k
        tx = gx + (-1.0 - gx) * k
        ty = gy + (-3.2 - gy) * k
        GLOW.scale = (1 + 0.15 * math.sin(t * 6),) * 3
        W.look(cam, (tx + 0.3, ty - 1.2 - 1.6 * k, cz + 0.12), (tx, ty + 0.3 * k, 0.22), 30 - 4 * k)
    elif name == "meaning":
        O["root"].location.z = -6
        face(A, "A", "focus")
        tr = dur * 0.36
        if t < tr:
            u = t / tr * REL_U
            approach(A, 0.18, u)
            BALL.location = hand_pos(A)
        else:
            approach(A, 0.18, REL_U)
            p0 = hand_pos(A)
            u = min(1.0, REL_U + (t - tr) / 0.5 * (1 - REL_U))
            approach(A, 0.18, u)
            hit_t = dur * 0.82
            s = min(1.0, (t - tr) / (hit_t - tr))
            BALL.location = path(s, p0.x, 0.0, bp=0.62, out=0.42, end=0.06)
            BALL.rotation_euler = (-f * 0.5, 0, 0)
            if t >= hit_t:
                dt = t - hit_t
                BALL.location = Vector((0.06 - 0.1 * dt, L - 0.95 + 1.6 * dt, BR))
                pins_pose(PINS, dt)
        by = BALL.location.y if t >= tr else -2
        cy = max(-6.2, min(by - 6.0, L - 8.5))
        W.look(cam, (0.7, cy - 0.6, 2.9), (0.1, cy + 7.0, 0.1), 28)
    else:  # summary
        face(A, "A", "happy")
        reset(A, (0.55, -8.85, 0), math.pi + 0.35)
        hold(A)
        breathe(A, t)
        breathe(O, t + 1)
        BALL.location = HIDE
        SOAKB.location = (0, TY, BALL_Z)
        O["shR"].rotation_euler = (0, R(150), 0)      # 엄지척 대신 손 들기
        W.look(cam, (1.0, -6.9, 1.7), (0.1, -9.4, 1.0), 32)
    if name == "summary":
        ball_at_chest(A, BALL)


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
