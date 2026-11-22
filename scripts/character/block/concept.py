"""블록 월드 배경 시안. python concept.py OUT_DIR"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import world as W  # noqa: E402

out = sys.argv[-1]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
xs = W.alley(5)
W.pin_set(0)
W.pin_set(-W.PITCH, "c")
for x in xs:
    if x not in (0, -W.PITCH):
        W.pin_set(x, f"o{x}")
A = W.character((0.18, -4.0, 0), math.pi, "nervous")
B = W.character((0.18 - W.PITCH, -4.0, 0), math.pi, "smile", shirt=(70, 190, 160), hair="cap")
for J in (A, B):
    J["shR"].rotation_euler = (math.radians(-35), 0, math.radians(8))
    J["shL"].rotation_euler = (math.radians(-35), 0, math.radians(-8))
    b = W.ball() if J is A else W.ball(rgb=(40, 110, 255), slash=None)
    b.parent = J["root"]
    b.location = (0, -0.42, 0.62)
W.lights_world()
cam = W.camera()
sc = W.setup_render(720, 1280, 40)
for name, loc, tgt, lens in (("hook", (0.75, -1.3, 1.5), (0.18, -4.0, 0.95), 30),
                             ("compare", (-0.82, -8.8, 2.7), (-0.82, -2.5, 0.7), 28),
                             ("pins", (-1.0, W.L - 3.8, 0.65), (0.2, W.L - 0.7, 0.3), 36)):
    W.look(cam, loc, tgt, lens)
    sc.render.filepath = os.path.join(out, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("saved", name, flush=True)
