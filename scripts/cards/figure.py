"""코드로 그리는 볼러 실루엣 (오른손 볼러 옆모습, 오른쪽을 향함).
좌표는 키 1.0 기준. n_ = 보는 쪽(왼쪽): 슬라이드 다리·균형 팔 / f_ = 뒤쪽(오른쪽): 볼 든 팔·뒤로 빠지는 다리.
hi 에 부위 이름을 주면 그 부위만 강조색으로 칠한다. 부위: torso, n_thigh, n_shin, f_thigh, f_shin,
n_uarm, n_farm, f_uarm, f_farm, glute(엉덩이), chest(가슴), shoulder(어깨), back(등), calf(종아리).
"""

POSES = {
    "push": dict(head=(0.50, 0.09), sh=(0.48, 0.20), hip=(0.47, 0.50),
                 n_knee=(0.53, 0.71), n_ank=(0.52, 0.93), n_toe=(0.61, 0.94),
                 f_knee=(0.45, 0.72), f_ank=(0.43, 0.93), f_toe=(0.52, 0.94),
                 n_elb=(0.55, 0.33), n_wr=(0.64, 0.29), f_elb=(0.54, 0.34), f_wr=(0.63, 0.30), ball=(0.68, 0.28)),
    "down": dict(head=(0.53, 0.10), sh=(0.50, 0.21), hip=(0.47, 0.50),
                 n_knee=(0.55, 0.71), n_ank=(0.56, 0.93), n_toe=(0.65, 0.94),
                 f_knee=(0.42, 0.72), f_ank=(0.37, 0.93), f_toe=(0.45, 0.95),
                 n_elb=(0.58, 0.33), n_wr=(0.67, 0.40), f_elb=(0.50, 0.40), f_wr=(0.48, 0.57), ball=(0.47, 0.63)),
    "back": dict(head=(0.55, 0.12), sh=(0.52, 0.23), hip=(0.47, 0.51),
                 n_knee=(0.57, 0.71), n_ank=(0.57, 0.93), n_toe=(0.66, 0.94),
                 f_knee=(0.40, 0.72), f_ank=(0.33, 0.92), f_toe=(0.39, 0.94),
                 n_elb=(0.61, 0.36), n_wr=(0.70, 0.40), f_elb=(0.42, 0.30), f_wr=(0.33, 0.25), ball=(0.28, 0.22)),
    "release": dict(head=(0.62, 0.22), sh=(0.57, 0.31), hip=(0.46, 0.54),
                    n_knee=(0.62, 0.68), n_ank=(0.60, 0.92), n_toe=(0.72, 0.93),
                    f_knee=(0.32, 0.73), f_ank=(0.17, 0.86), f_toe=(0.12, 0.91),
                    n_elb=(0.44, 0.37), n_wr=(0.30, 0.40), f_elb=(0.58, 0.50), f_wr=(0.66, 0.66), ball=(0.70, 0.72)),
    "follow": dict(head=(0.62, 0.22), sh=(0.57, 0.31), hip=(0.46, 0.54),
                   n_knee=(0.62, 0.68), n_ank=(0.60, 0.92), n_toe=(0.72, 0.93),
                   f_knee=(0.32, 0.73), f_ank=(0.17, 0.86), f_toe=(0.12, 0.91),
                   n_elb=(0.44, 0.37), n_wr=(0.30, 0.40), f_elb=(0.70, 0.22), f_wr=(0.74, 0.08), ball=None),
}
TH = dict(torso=0.12, thigh=0.075, shin=0.055, foot=0.04, uarm=0.05, farm=0.042)


def _cap(d, a, b, w, col):
    d.line((a, b), fill=col, width=int(w))
    r = w / 2
    for p in (a, b):
        d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=col)


def _mix(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def draw(d, pose, ox, oy, h, near, far, hi=None, hi_col=(255, 114, 0)):
    P = {k: (None if v is None else (ox + v[0] * h, oy + v[1] * h)) for k, v in POSES[pose].items()}
    t = {k: v * h for k, v in TH.items()}
    hi = set(hi or [])

    def seg(name, a, b, w, base):
        _cap(d, P[a], P[b], w, hi_col if name in hi else base)

    seg("f_uarm", "sh", "f_elb", t["uarm"], far)
    seg("f_farm", "f_elb", "f_wr", t["farm"], far)
    seg("f_thigh", "hip", "f_knee", t["thigh"], far)
    seg("f_shin", "f_knee", "f_ank", t["shin"], far)
    seg("f_foot", "f_ank", "f_toe", t["foot"], far)
    if P["ball"]:
        bx, by = P["ball"]; br = 0.06 * h
        d.ellipse((bx - br, by - br, bx + br, by + br), fill=far)
    seg("torso", "sh", "hip", t["torso"], near)
    seg("n_thigh", "hip", "n_knee", t["thigh"], near)
    seg("n_shin", "n_knee", "n_ank", t["shin"], near)
    seg("n_foot", "n_ank", "n_toe", t["foot"], near)
    hx, hy = P["head"]; r = 0.065 * h
    d.ellipse((hx - r, hy - r, hx + r, hy + r), fill=near)
    seg("n_uarm", "sh", "n_elb", t["uarm"], near)
    seg("n_farm", "n_elb", "n_wr", t["farm"], near)
    # 몸통 위 부위 표시 (작은 타원)
    spots = {
        "glute": (_mix(P["hip"], P["sh"], 0.10), 0.05, -1.4),
        "back": (_mix(P["hip"], P["sh"], 0.55), 0.04, -1),
        "chest": (_mix(P["hip"], P["sh"], 0.78), 0.04, 1),
        "shoulder": (P["sh"], 0.038, 0),
        "calf": (_mix(P["n_knee"], P["n_ank"], 0.35), 0.03, -1),
    }
    for name, (c, rr, side) in spots.items():
        if name in hi:
            x, y = c; x += side * 0.03 * h; rr *= h
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=hi_col)
    return P
