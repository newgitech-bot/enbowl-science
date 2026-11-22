"""캐릭터 애니메이션풍 시안 스틸.
사용법: python toon.py OUT.png VARIANT   (VARIANT: cel | soft | flat)
  cel : 셀 셰이딩 + 굵은 외곽선 (애니메이션)
  soft: 둥글고 부드러운 3D 애니메이션 영화풍
  flat: 그림자 없는 평면 색 + 외곽선 (2.5D 모션그래픽)
"""
import math
import sys

import bpy
from mathutils import Vector

VAR = sys.argv[-1]
OUT = sys.argv[-2]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
OUTLINE = VAR in ("cel", "flat")


def srgb(c):
    return tuple(((v / 255) ** 2.2) for v in c) + (1,)


_mats = {}


def mat(name, rgb, rough=0.5, gloss=0.0):
    key = (name, VAR)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    col = srgb(rgb)
    if VAR == "flat":
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = col
        em.inputs["Strength"].default_value = 1.0
        nt.links.new(em.outputs[0], out.inputs[0])
    elif VAR == "cel":
        toon = nt.nodes.new("ShaderNodeBsdfToon")
        toon.inputs["Color"].default_value = col
        toon.inputs["Size"].default_value = 0.72
        toon.inputs["Smooth"].default_value = 0.03
        em = nt.nodes.new("ShaderNodeEmission")          # 그림자 쪽이 너무 어둡지 않게 바탕색을 살짝 띄움
        em.inputs["Color"].default_value = col
        em.inputs["Strength"].default_value = 0.3
        add = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(toon.outputs[0], add.inputs[0])
        nt.links.new(em.outputs[0], add.inputs[1])
        if gloss:
            g = nt.nodes.new("ShaderNodeBsdfToon")
            g.component = "GLOSSY"
            g.inputs["Size"].default_value = 0.12
            g.inputs["Smooth"].default_value = 0.02
            g.inputs["Color"].default_value = (1, 1, 1, 1)
            add2 = nt.nodes.new("ShaderNodeAddShader")
            mix = nt.nodes.new("ShaderNodeMixShader")
            mix.inputs[0].default_value = gloss
            nt.links.new(add.outputs[0], add2.inputs[0])
            nt.links.new(g.outputs[0], add2.inputs[1])
            nt.links.new(add.outputs[0], mix.inputs[1])
            nt.links.new(add2.outputs[0], mix.inputs[2])
            nt.links.new(mix.outputs[0], out.inputs[0])
        else:
            nt.links.new(add.outputs[0], out.inputs[0])
    else:  # soft
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        b.inputs["Base Color"].default_value = col
        b.inputs["Roughness"].default_value = rough
        b.inputs["Subsurface Weight"].default_value = 0.15 if name in ("skin",) else 0.0
        b.inputs["Sheen Weight"].default_value = 0.3 if name.startswith("shirt") else 0.0
        if gloss:
            b.inputs["Coat Weight"].default_value = gloss
        nt.links.new(b.outputs[0], out.inputs[0])
    _mats[key] = m
    return m


def outline_mat():
    if "outline" in bpy.data.materials:
        return bpy.data.materials["outline"]
    m = bpy.data.materials.new("outline")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = srgb((28, 24, 34))
    mix = nt.nodes.new("ShaderNodeMixShader")
    # 카메라 광선에서만 선을 그리고, 그림자·반사 광선에는 투명 (선 껍질이 빛을 가리지 않게)
    lp = nt.nodes.new("ShaderNodeLightPath")
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
    nt.links.new(lp.outputs["Is Camera Ray"], inv.inputs[1])
    nt.links.new(geo.outputs["Backfacing"], mx.inputs[0])
    nt.links.new(inv.outputs[0], mx.inputs[1])
    nt.links.new(mx.outputs[0], mix.inputs[0])
    nt.links.new(em.outputs[0], mix.inputs[1])   # 앞면(물체 뒤쪽 껍질) = 검은 선
    nt.links.new(tr.outputs[0], mix.inputs[2])   # 뒷면(카메라 쪽 껍질) = 투명
    nt.links.new(mix.outputs[0], out.inputs[0])
    return m


def finish(o, m, line=0.018):
    o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = True
    if OUTLINE and line:
        o.data.materials.append(outline_mat())
        s = o.modifiers.new("ol", "SOLIDIFY")
        s.thickness = -line
        s.use_flip_normals = True
        s.material_offset = 1
        s.use_rim = False
    return o


def sphere(name, loc, scale, m, line=0.018, parent=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    finish(o, m, line)
    if parent:
        o.parent = parent
    return o


def capsule(name, a, b, r, m, line=0.018, parent=None):
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r, depth=d.length, location=(a + b) / 2)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    finish(o, m, line)
    for p in (a, b):
        sphere(name + "c", p, (r, r, r), m, line)
    return o


def rbox(name, loc, size, m, bevel=0.08, line=0.018, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        bv = o.modifiers.new("b", "BEVEL")
        bv.width = bevel
        bv.segments = 6
    finish(o, m, line)
    return o


def plane(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, 1)
    o.data.materials.append(m)
    return o


# ---------- 캐릭터 (2등신 꼬마 볼러) ----------
SKIN = (255, 220, 192)
HAIR = (44, 34, 40)
SHIRT = (255, 120, 40)
PANTS = (52, 64, 110)
WHITE = (250, 250, 250)


def bowler(x=0.0, y=0.0):
    sk, hr, sh, pa, wh = mat("skin", SKIN, 0.55), mat("hair", HAIR, 0.4, 0.3), mat("shirt", SHIRT, 0.7), \
        mat("pants", PANTS, 0.7), mat("white", WHITE, 0.4)
    blk = mat("black", (20, 18, 24), 0.2, 0.6)
    # 몸통 (짧고 둥글게)
    sphere("body", (x, y, 0.62), (0.34, 0.3, 0.36), sh)
    rbox("collar", (x, y - 0.02, 0.92), (0.26, 0.2, 0.06), wh, bevel=0.03, line=0.012)
    sphere("hips", (x, y, 0.38), (0.3, 0.27, 0.16), pa)
    # 다리
    for s in (-1, 1):
        capsule(f"leg{s}", (x + 0.14 * s, y, 0.36), (x + 0.16 * s, y - 0.02, 0.14), 0.1, pa)
        sphere(f"shoe{s}", (x + 0.17 * s, y - 0.07, 0.08), (0.13, 0.19, 0.09), mat("shoe", (255, 255, 255), 0.4))
        sphere(f"sole{s}", (x + 0.17 * s, y - 0.07, 0.035), (0.135, 0.195, 0.04), mat("sole", (255, 90, 60)), line=0.01)
    # 머리 (크게)
    hz = 1.42
    sphere("head", (x, y, hz), (0.52, 0.48, 0.5), sk)
    hair = sphere("hair", (x, y + 0.04, hz + 0.1), (0.55, 0.52, 0.48), hr)
    # 앞머리 아래를 잘라 얼굴 드러내기
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(hair.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(x, y, hz + 0.05),
                           plane_no=(0, 0.55, 1), clear_inner=True)
    bm.to_mesh(hair.data)
    bm.free()
    # 삐침 머리
    for i, (dx, dz, a) in enumerate(((-0.05, 0.6, -25), (0.08, 0.58, 20))):
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.08, depth=0.24, location=(x + dx, y + 0.02, hz + dz),
                                        rotation=(math.radians(-10), math.radians(a), 0))
        finish(bpy.context.object, hr)
    # 얼굴 (-y 방향)
    fy = y - 0.47
    for s in (-1, 1):
        sphere(f"eyeW{s}", (x + 0.17 * s, fy + 0.03, hz - 0.02), (0.1, 0.05, 0.13), wh, line=0.012)
        sphere(f"pupil{s}", (x + 0.165 * s, fy - 0.005, hz - 0.03), (0.07, 0.04, 0.095), blk, line=0)
        sphere(f"hl{s}", (x + 0.14 * s, fy - 0.03, hz + 0.02), (0.025, 0.012, 0.03), mat("hl", (255, 255, 255)), line=0)
        sphere(f"cheek{s}", (x + 0.3 * s, fy + 0.07, hz - 0.17), (0.08, 0.03, 0.05), mat("cheek", (255, 140, 140)), line=0)
        capsule(f"brow{s}", (x + 0.1 * s, fy + 0.02, hz + 0.16), (x + 0.24 * s, fy + 0.04, hz + 0.19 - 0.0 * s), 0.018,
                hr, line=0)
        sphere(f"ear{s}", (x + 0.51 * s, y, hz - 0.03), (0.07, 0.09, 0.1), sk)
    # 웃는 입 (반원)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=(x, fy + 0.02, hz - 0.2))
    mo = bpy.context.object
    mo.scale = (0.1, 0.04, 0.07)
    bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new()
    bm.from_mesh(mo.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(x, fy, hz - 0.2),
                           plane_no=(0, 0, 1), clear_outer=True)
    bm.to_mesh(mo.data)
    bm.free()
    finish(mo, mat("mouth", (150, 40, 60)), line=0.01)
    sphere("tongue", (x, fy + 0.0, hz - 0.245), (0.05, 0.02, 0.025), mat("tongue", (255, 110, 120)), line=0)
    # 팔: 볼을 들어 올리는 포즈 (오른손 볼, 왼손 받침)
    bx, bz = x - 0.36, 0.7
    capsule("armR", (x - 0.3, y, 0.82), (bx - 0.02, y - 0.22, bz - 0.08), 0.085, sh)
    capsule("armL", (x + 0.3, y, 0.82), (bx + 0.16, y - 0.3, bz + 0.02), 0.085, sh)
    sphere("handR", (bx - 0.02, y - 0.26, bz - 0.14), (0.095, 0.095, 0.095), sk)
    sphere("handL", (bx + 0.17, y - 0.36, bz + 0.03), (0.095, 0.095, 0.095), sk)
    # 볼 (가슴 옆, 얼굴을 가리지 않게)
    ball = sphere("ball", (bx, y - 0.36, bz), (0.2, 0.2, 0.2), mat("ball", (40, 110, 255), 0.1, 0.8), line=0.012)
    for dx, dz in ((-0.05, 0.08), (0.05, 0.08), (0, -0.02)):
        sphere("hole", (bx + dx, y - 0.555, bz + dz), (0.025, 0.012, 0.025), blk, line=0)
    return ball


def pin(name, loc, scale=1.0, tilt=(0, 0, 0)):
    prof = [(0, 0), (0.05, 0), (0.08, 0.04), (0.105, 0.14), (0.1, 0.24), (0.07, 0.33), (0.048, 0.39), (0.046, 0.43),
            (0.058, 0.48), (0.06, 0.52), (0.05, 0.57), (0.03, 0.6), (0, 0.61)]
    N = 32
    verts, faces = [], []
    for rr, z in prof:
        for k in range(N):
            a = 2 * math.pi * k / N
            verts.append((rr * scale * math.cos(a), rr * scale * math.sin(a), z * scale))
    for i in range(len(prof) - 1):
        for k in range(N):
            a = i * N + k
            b = i * N + (k + 1) % N
            faces.append((a, b, (i + 1) * N + (k + 1) % N, (i + 1) * N + k))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = tilt
    o.data.materials.append(mat("pin", (252, 252, 250), 0.3, 0.5))
    o.data.materials.append(mat("pinred", (235, 50, 60), 0.4))
    for p in o.data.polygons:
        p.use_smooth = True
        zc = sum(o.data.vertices[v].co.z for v in p.vertices) / len(p.vertices) / scale
        if 0.395 < zc < 0.415 or 0.435 < zc < 0.455:
            p.material_index = 1
    if OUTLINE:
        o.data.materials.append(outline_mat())
        s = o.modifiers.new("ol", "SOLIDIFY")
        s.thickness = -0.014
        s.use_flip_normals = True
        s.material_offset = 2
    return o


# ---------- 배경: 단순하고 밝은 볼링장 ----------
def stage():
    lane = mat("lane", (246, 206, 150), 0.25, 0.3)
    lane2 = mat("lane2", (236, 192, 134), 0.25, 0.3)
    for i in range(9):
        plane(f"bd{i}", (-1.2 + i * 0.3, 4, 0), (0.29, 14, 1), lane if i % 2 else lane2)
    gut = mat("gutter", (150, 160, 190), 0.4)
    for s in (-1, 1):
        plane(f"g{s}", (s * 1.55, 4, -0.01), (0.4, 14, 1), gut)
        plane(f"side{s}", (s * 3.0, 4, -0.02), (2.5, 14, 1), mat("floor2", (120, 200, 230), 0.6))
    wall = mat("wall", (130, 205, 240), 0.8) if VAR != "soft" else mat("wall", (120, 200, 245), 0.9)
    plane("wall", (0, 8.5, 4.0), (16, 8, 1), wall, rot=(math.radians(90), 0, 0))
    cols = [(255, 196, 40), (255, 120, 40), (120, 100, 240), (60, 200, 140)]
    for i, c in enumerate(cols):
        rbox(f"panel{i}", (-2.4 + i * 1.6, 8.3, 2.3), (1.4, 0.1, 0.7), mat(f"pan{i}", c, 0.5), bevel=0.06, line=0.02)
    rbox("pit", (0, 8.2, 0.55), (3.2, 0.1, 1.1), mat("pit", (40, 44, 70), 0.8), bevel=0.04, line=0.0)
    # 핀 (뒤쪽, 일부 쓰러지는 중)
    sp = 0.32
    rows = [[0], [-0.5, 0.5], [-1, 0, 1], [-1.5, -0.5, 0.5, 1.5]]
    k = 0
    for r, row in enumerate(rows):
        for xx in row:
            tilt = (0, 0, 0)
            pin(f"pin{k}", (xx * sp + 0.25, 6.4 + r * sp * 0.87, 0), 0.62, tilt)
            k += 1
    # 반짝이 별 장식
    for (px, pz, s) in ((-1.1, 2.3, 0.09), (1.0, 2.0, 0.07), (1.25, 1.55, 0.05)):
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=s, depth=0.01, location=(px, 2.0, pz),
                                        rotation=(math.radians(90), 0, 0))
        finish(bpy.context.object, mat("spark", (255, 230, 80)), line=0.008)


def lights():
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.85, 0.92, 1.0, 1)
    bg.inputs["Strength"].default_value = 0.6 if VAR == "soft" else 0.25
    def area(loc, rot, size, e, col=(1, 1, 1)):
        ld = bpy.data.lights.new("a", "AREA")
        ld.size = size
        ld.energy = e
        ld.color = col
        o = bpy.data.objects.new("a", ld)
        o.location = loc
        o.rotation_euler = rot
        sc.collection.objects.link(o)
    if VAR == "soft":
        area((-2.2, -2.5, 3.0), (math.radians(50), 0, math.radians(-40)), 3.0, 900, (1, 0.95, 0.88))
        area((2.5, -1.5, 1.8), (math.radians(70), 0, math.radians(55)), 2.0, 300, (0.85, 0.9, 1))
        area((0, 2.0, 3.0), (math.radians(-120), 0, 0), 2.0, 500, (1, 0.9, 0.8))  # 림 라이트
    else:
        area((0.6, -3.2, 2.6), (math.radians(65), 0, math.radians(10)), 2.5, 420)
        area((0, 2.0, 3.0), (math.radians(-120), 0, 0), 1.5, 120)


def camera():
    cd = bpy.data.cameras.new("c")
    cd.lens = 40
    c = bpy.data.objects.new("c", cd)
    sc.collection.objects.link(c)
    c.location = (0.75, -4.3, 1.4)
    t = bpy.data.objects.new("t", None)
    sc.collection.objects.link(t)
    t.location = (-0.05, 0.6, 0.95)
    tr = c.constraints.new("TRACK_TO")
    tr.target = t
    tr.track_axis = "TRACK_NEGATIVE_Z"
    tr.up_axis = "UP_Y"
    if VAR == "soft":
        cd.dof.use_dof = True
        cd.dof.focus_distance = 3.8
        cd.dof.aperture_fstop = 2.8
    sc.camera = c


stage()
bowler(-0.15, 0.0)
lights()
camera()
sc.render.engine = "CYCLES"
sc.cycles.samples = 24 if VAR == "flat" else 64
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 720, 1280
sc.view_settings.view_transform = "Standard"
if VAR == "soft":
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("saved", OUT)
