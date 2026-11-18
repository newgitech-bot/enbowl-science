"""카드뉴스용 캐릭터 포즈 스틸 (투명 배경 PNG)"""
import bpy, math, sys, os
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scene import *
OUT = "/home/claude/b3d/poses"; os.makedirs(OUT, exist_ok=True)

def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = setup_render(900, 900); sc.display.render_aa = "16"
    root, head, arms, legs = character(origin=(0, 0, 0))
    root.rotation_euler = (0, 0, 0)  # 카메라(-y)를 바라봄
    b = ball(rgb=(30, 60, 200), r=0.2)
    cam = camera((0, -6.5, 1.3), (0, 0, 1.05), lens=50)
    return sc, root, head, arms, legs, b, cam

def hand(s=-1):
    bpy.context.view_layer.update()
    return bpy.data.objects[f"hand{s}"].matrix_world.translation.copy()

def shot(name, fn):
    sc, root, head, arms, legs, b, cam = setup()
    fn(root, head, arms, legs, b, cam)
    sc.render.filepath = f"{OUT}/{name}.png"
    bpy.ops.render.render(write_still=True)

def fresh(root, head, arms, legs, b, cam):
    # 자신감: 볼을 가슴 앞에, 고개 살짝 들고
    arms[-1].rotation_euler = (-1.05, -0.45, 0); arms[1].rotation_euler = (-1.05, 0.45, 0)
    head.rotation_euler = (0.08, 0, 0)
    bpy.context.view_layer.update()
    b.location = (hand(-1) + hand(1)) / 2 + Vector((0, -0.18, 0.02))

def tired(root, head, arms, legs, b, cam):
    # 지침: 고개 숙이고 볼 든 팔 축 처짐, 땀
    arms[-1].rotation_euler = (0, 0, -0.08); arms[1].rotation_euler = (0, 0, 0.1)
    head.rotation_euler = (0.35, 0, 0.12)
    root.rotation_euler = (-0.08, 0, 0)
    bpy.context.view_layer.update()
    b.location = hand(-1) + Vector((0, 0, -0.22))
    sphere("sweat", (0.42, -0.25, 1.95), (0.05, 0.04, 0.075), mat("sweat", (150, 210, 255), 0.05))
    sphere("sweat2", (-0.4, -0.3, 1.75), (0.04, 0.03, 0.06), mat("sweat", (150, 210, 255), 0.05))

def think(root, head, arms, legs, b, cam):
    # 갸우뚱: 한 손 턱, 볼은 다른 손
    arms[1].rotation_euler = (-2.0, 0.75, 0)
    head.rotation_euler = (0, 0.25, 0.1)
    bpy.context.view_layer.update()
    b.location = hand(-1) + Vector((0, 0, -0.22))

def cheer(root, head, arms, legs, b, cam):
    arms[-1].rotation_euler = (0, 2.5, 0); arms[1].rotation_euler = (0, -2.5, 0)
    head.rotation_euler = (0.15, 0, 0)
    b.location = (0.75, -0.3, 0.2)

def release(root, head, arms, legs, b, cam):
    # 투구 릴리스 (측면 카메라)
    root.rotation_euler = (0.3, 0, math.pi / 2)
    root.location.z = -0.15
    arms[-1].rotation_euler = (-0.5, 0, 0); arms[1].rotation_euler = (0, -1.1, 0)
    legs[1].rotation_euler = (-0.6, 0, 0); legs[-1].rotation_euler = (1.0, 0, 0)
    bpy.context.view_layer.update()
    b.location = hand(-1) + Vector((0, 0, -0.2))
    cam.location = (0.3, -6.5, 1.0)

if __name__ == "__main__":
    for n in sys.argv[1:]:
        shot(n, globals()[n])
