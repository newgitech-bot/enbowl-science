import bpy, math
from mathutils import Vector

def mat(name, rgb, rough=0.5):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*[(c/255)**2.2 for c in rgb], 1)
    m.roughness = rough
    return m

def setmat(obj, m):
    obj.data.materials.clear(); obj.data.materials.append(m)

def sphere(name, loc, scale, m, parent=None, seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg//2, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale
    bpy.ops.object.shade_smooth(); setmat(o, m)
    if parent: o.parent = parent
    return o

def cyl(name, loc, r, h, m, rot=(0,0,0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name
    bpy.ops.object.shade_smooth(); setmat(o, m)
    if parent: o.parent = parent
    return o

def box(name, loc, size, m, parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object; o.name = name; o.scale = (size[0]/2, size[1]/2, size[2]/2)
    setmat(o, m)
    if bevel:
        bpy.ops.object.transform_apply(scale=True)
        b = o.modifiers.new("b", "BEVEL"); b.width = bevel; b.segments = 4
        bpy.ops.object.shade_smooth()
    if parent: o.parent = parent
    return o

def capsule(name, a, b, r, m, parent=None):
    """a,b: 끝점(로컬). 원통 + 양끝 구."""
    a, b = Vector(a), Vector(b)
    mid = (a+b)/2; d = b-a; L = d.length
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=r, depth=L, location=mid)
    o = bpy.context.object; o.name = name
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z','Y')
    bpy.ops.object.shade_smooth(); setmat(o, m)
    for p in (a, b):
        s = sphere(name+"_cap", p, (r,r,r), m, seg=24)
        s.parent = o; s.matrix_parent_inverse = o.matrix_world.inverted()
    if parent:
        o.parent = parent
    return o

SKIN=(250,214,184); HAIR=(30,28,34); ORANGE=(255,114,0); NAVY=(40,44,60); WHITE=(245,245,242)
CHEEK=(255,150,150); BLACK=(15,15,18); WOOD=(222,178,120); WOOD2=(205,160,104)

def character(name="bowler", shirt=ORANGE, origin=(0,0,0)):
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    root.location = origin
    ms, mh, msh, mp, mw, mb, mc = (mat("skin",SKIN), mat("hair",HAIR), mat("shirt_"+name,shirt),
        mat("pants",NAVY), mat("white",WHITE), mat("black",BLACK), mat("cheek",CHEEK))
    # 몸통
    torso = cyl("torso", (0,0,1.05), 0.34, 0.62, msh, parent=root)
    sphere("torso_top", (0,0,1.33), (0.34,0.34,0.16), msh, parent=root)
    sphere("torso_bot", (0,0,0.76), (0.34,0.34,0.12), mp, parent=root)
    # 다리
    legs = {}
    for s in (-1,1):
        hip = bpy.data.objects.new(f"hip{s}", None); bpy.context.collection.objects.link(hip)
        hip.parent = root; hip.location = (0.15*s,0,0.75)
        capsule(f"leg{s}", (0,0,0), (0,0,-0.57), 0.12, mp, parent=hip)
        box(f"shoe{s}", (0,-0.05,-0.68), (0.2,0.34,0.14), mat("shoe",ORANGE) if False else mw, parent=hip, bevel=0.05)
        legs[s] = hip
    # 머리
    head = bpy.data.objects.new("head", None); bpy.context.collection.objects.link(head)
    head.parent = root; head.location = (0,0,1.42)
    sphere("neck", (0,0,0.02), (0.11,0.11,0.1), ms, parent=head)
    sphere("skull", (0,0,0.42), (0.42,0.4,0.42), ms, parent=head)
    hair = sphere("hair", (0,0.02,0.46), (0.45,0.44,0.43), mh, parent=head, seg=48)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(hair.data)
    # 앞머리는 눈썹 위, 뒤로 갈수록 내려오는 바가지 머리
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0,0,-0.33), plane_no=(0,0.45,1), clear_inner=True)
    bm.to_mesh(hair.data); bm.free()
    for s in (-1,1):
        sphere(f"eye{s}", (0.14*s,-0.385,0.38), (0.045,0.03,0.055), mb, parent=head)
        sphere(f"cheek{s}", (0.25*s,-0.33,0.27), (0.075,0.03,0.05), mc, parent=head)
        sphere(f"ear{s}", (0.41*s,0,0.38), (0.06,0.08,0.09), ms, parent=head)
    sphere("mouth", (0,-0.40,0.24), (0.04,0.02,0.018), mat("mouth",(150,60,60)), parent=head)
    # 팔: 어깨 피벗
    arms = {}
    for s in (-1,1):
        sh = bpy.data.objects.new(f"shoulder{s}", None); bpy.context.collection.objects.link(sh)
        sh.parent = root; sh.location = (0.42*s,0,1.28)
        capsule(f"arm{s}", (0,0,0), (0.04*s,0,-0.5), 0.1, msh, parent=sh)
        hand = sphere(f"hand{s}", (0.05*s,0,-0.62), (0.11,0.11,0.11), ms, parent=sh)
        arms[s] = sh
    return root, head, arms, legs

def pin(name, loc):
    m = mat("pin", WHITE, 0.2); r = mat("pinred", (210,30,40))
    # 회전체 프로필로 핀 모양
    prof = [(0,0),(0.028,0),(0.045,0.04),(0.06,0.11),(0.058,0.17),(0.04,0.23),(0.026,0.27),(0.024,0.30),(0.032,0.34),(0.032,0.36),(0.02,0.38),(0,0.385)]
    s = 0.95
    verts=[]; faces=[]; N=24
    for i,(rr,z) in enumerate(prof):
        for k in range(N):
            a=2*math.pi*k/N; verts.append((rr*s*math.cos(a), rr*s*math.sin(a), z*s))
    for i in range(len(prof)-1):
        for k in range(N):
            a=i*N+k; b=i*N+(k+1)%N; c=(i+1)*N+(k+1)%N; d=(i+1)*N+k; faces.append((a,b,c,d))
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); o.location=loc
    o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth=True
    # 빨간 띠 두 줄
    for z in (0.255, 0.285):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.027*s, minor_radius=0.006, location=(0,0,z*s))
        t=bpy.context.object; setmat(t,r); t.parent=o
    return o

def lane(length=18.3, width=1.06):
    wood = mat("wood", WOOD, 0.3); wood2 = mat("wood2", WOOD2, 0.3)
    gut = mat("gutter", (70,72,80)); dark = mat("alley", (36,38,48))
    # 레인 판자 줄무늬
    n = 13
    for i in range(n):
        x = -width/2 + width*(i+0.5)/n
        box(f"board{i}", (x, length/2, -0.01), (width/n*0.98, length, 0.02), wood if i%2 else wood2)
    # 어프로치
    box("approach", (0, -2.5, -0.01), (width+0.5, 5, 0.02), wood2)
    box("foul", (0, 0, 0.001), (width+0.5, 0.03, 0.005), mat("foulline",(20,20,20)))
    for s in (-1,1):
        cyl(f"gutter{s}", (s*(width/2+0.12), length/2, 0.02), 0.12, length, gut, rot=(math.pi/2,0,0))
        box(f"cap{s}", (s*(width/2+0.5), length/2-2, 0.1), (0.4, length+5, 0.2), dark)
    # 화살표(스팟)
    for k in range(7):
        x = -width/2 + width*(k+0.5)/7*0.9 + width*0.05
        y = 4.6 + abs(k-3)*0.3
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.05, depth=0.004, location=(x, y, 0.002))
        o=bpy.context.object; setmat(o, mat("arrow",(120,60,30)))
    # 배경
    box("floor", (0, 6, -0.05), (30, 40, 0.04), dark)
    box("backwall", (0, length+1.5, 2), (30, 0.2, 6), mat("wall",(26,28,40)))
    box("masking", (0, length-0.6, 1.6), (3, 0.3, 0.9), mat("mask",(255,114,0)))
    return length

def pins(length=18.3):
    sp = 0.3048
    out=[]
    rows=[[0],[-0.5,0.5],[-1,0,1],[-1.5,-0.5,0.5,1.5]]
    for r,row in enumerate(rows):
        for x in row:
            out.append(pin(f"pin{len(out)}", (x*sp, length-0.86+r*sp*0.866, 0)))
    return out

def ball(name="ball", loc=(0,0,0), rgb=(255,114,0)):
    m = mat(name, rgb, 0.15)
    b = sphere(name, loc, (0.109,0.109,0.109), m, seg=48)
    for (x,z) in ((-0.03,0.06),(0.03,0.06),(0,0.0)):
        sphere(name+"_hole", (0,0,0), (0.018,0.006,0.018), mat("hole",(10,10,10)), parent=b).location=(x/0.109, -1.0, z/0.109)
    return b

def setup_render(w=1080, h=1920, samples=16):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sh = sc.display.shading
    sh.light = 'STUDIO'; sh.studio_light = 'paint.sl'; sh.color_type = 'MATERIAL'
    sh.show_shadows = True; sh.shadow_intensity = 0.35
    sh.show_cavity = False
    sh.show_specular_highlight = True
    sc.display.shadow_focus = 0.6
    sc.display.render_aa = '16'
    sh.background_type = 'VIEWPORT' if hasattr(sh,'background_type') else sh.background_type
    sc.render.film_transparent = True
    sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'Standard'
    return sc

def camera(loc, look, lens=35):
    bpy.ops.object.camera_add(location=loc)
    c = bpy.context.object; c.data.lens = lens
    d = Vector(look) - Vector(loc)
    c.rotation_mode='QUATERNION'; c.rotation_quaternion = d.to_track_quat('-Z','Y')
    bpy.context.scene.camera = c
    return c


# ---------- 밝은 볼링장 ----------
LANE_W = 1.06
PITCH = 2.0          # 레인 간격 (거터·캐핑 포함)

def lane_at(x0, length, idx):
    wood = mat("wood", (232, 196, 140), 0.25); wood2 = mat("wood2", (220, 182, 126), 0.25)
    gut = mat("gutter", (190, 194, 204)); cap = mat("capping", (245, 246, 248))
    n = 13
    for i in range(n):
        x = x0 - LANE_W/2 + LANE_W*(i+0.5)/n
        box(f"board{idx}_{i}", (x, length/2, -0.01), (LANE_W/n*0.985, length, 0.02), wood if i % 2 else wood2)
    box(f"appr{idx}", (x0, -3, -0.01), (LANE_W+0.5, 6, 0.02), wood2)
    box(f"foul{idx}", (x0, 0, 0.001), (LANE_W+0.5, 0.03, 0.005), mat("foulline", (30, 30, 30)))
    for s in (-1, 1):
        cyl(f"gut{idx}{s}", (x0+s*(LANE_W/2+0.12), length/2, 0.02), 0.12, length, gut, rot=(math.pi/2, 0, 0))
    for k in range(7):
        x = x0 - LANE_W/2 + LANE_W*(k+0.5)/7*0.9 + LANE_W*0.05
        y = 4.6 + abs(k-3)*0.3
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.05, depth=0.004, location=(x, y, 0.002))
        setmat(bpy.context.object, mat("arrow", (150, 80, 40)))
    return cap

def alley(n=5, length=18.3):
    cap = mat("capping", (245, 246, 248))
    xs = [(i - n//2) * PITCH for i in range(n)]
    colors = [(0, 170, 190), (255, 196, 0), (255, 114, 0), (130, 90, 230), (0, 190, 120)]
    for i, x in enumerate(xs):
        lane_at(x, length, i)
        # 핀 데크 위 마스킹 패널 (레인마다 색)
        box(f"mask{i}", (x, length-0.5, 1.45), (PITCH-0.06, 0.25, 0.8), mat(f"mask{i}", colors[i % len(colors)]), bevel=0.04)
        # 핀 뒤 검은 커튼
        box(f"pit{i}", (x, length+0.6, 0.5), (PITCH-0.1, 0.1, 1.0), mat("pit", (40, 42, 52)))
    # 레인 사이 캐핑 & 볼 리턴
    for i in range(n+1):
        x = (i - n//2 - 0.5) * PITCH
        box(f"capping{i}", (x, length/2-1, 0.03), (PITCH-LANE_W-0.24, length+2, 0.06), cap)
        if i in (1, n - 1):
            box(f"ret{i}", (x, -3.6, 0.45), (0.55, 1.2, 0.9), mat("ret", (60, 120, 220)), bevel=0.12)
            box(f"rethood{i}", (x, -3.6, 0.95), (0.6, 1.0, 0.2), mat("hood", (240, 240, 245)), bevel=0.08)
    W = n * PITCH + 6
    # 바닥, 벽, 천장
    box("concourse", (0, -9, -0.03), (W, 6, 0.02), mat("carpet", (52, 70, 120)))
    box("floor", (0, 6, -0.05), (W, 40, 0.02), mat("floor", (200, 200, 205)))
    box("backwall", (0, length+1.2, 2.5), (W, 0.2, 5), mat("backwall", (238, 240, 246)))
    box("frontwall", (0, -12, 2.5), (W, 0.2, 5), mat("frontwall", (245, 246, 250)))
    box("stripe_o", (0, -11.85, 1.2), (W, 0.05, 0.35), mat("stripe", (255, 114, 0)))
    box("stripe_b", (0, -11.85, 1.7), (W, 0.05, 0.12), mat("stripe2", (0, 170, 190)))
    for s in (-1, 1):
        box(f"sidewall{s}", (s*W/2, 3, 2.5), (0.2, 32, 5), mat("side", (236, 238, 244)))
    # 오버헤드 점수 모니터
    for i, x in enumerate(xs):
        box(f"mon{i}", (x, -1.2, 3.0), (1.4, 0.12, 0.8), mat("monframe", (30, 32, 40)), bevel=0.03)
        box(f"scr{i}", (x, -1.27, 3.0), (1.28, 0.02, 0.68), mat("screen", (40, 120, 230)))
    # 뒤쪽 의자
    for i, x in enumerate(xs):
        for k in (-0.5, 0.5):
            box(f"seat{i}{k}", (x + k, -7.2, 0.25), (0.8, 0.8, 0.5), mat(f"seat{i%3}", [(255,114,0),(0,170,190),(255,196,0)][i % 3]), bevel=0.15)
    return xs

def pins_at(x0, length=18.3, tag=""):
    sp = 0.3048; out = []
    rows = [[0], [-0.5, 0.5], [-1, 0, 1], [-1.5, -0.5, 0.5, 1.5]]
    for r, row in enumerate(rows):
        for x in row:
            out.append(pin(f"pin{tag}{len(out)}", (x0 + x*sp, length-0.86+r*sp*0.866, 0)))
    return out
