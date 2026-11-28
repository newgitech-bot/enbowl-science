"""EP.09 (우레탄 볼 경도 규정) 타임라인·오버레이·오디오를 나레이션 길이에 맞춰 만든다.
사용법: python scripts/character/block/build_ep09.py [NARRATION_DIR]
결과: posts/2026-12-01-EP09/timeline.json, content.json(overlay), audio.json
anim_ep09.py 의 동작 시점(why 핀 충돌 = 샷의 78%, meaning 릴리스 36% · 충돌 82%)과 효과음 시점을 맞춘다.
"""
import json
import sys
from pathlib import Path

POST = Path("posts/2026-12-01-EP09")
NDIR = Path(sys.argv[1]) if len(sys.argv) > 1 else POST / "narration_clone"
BASE = [("hook", 5.5), ("why", 7), ("soak", 7), ("recover", 7), ("rule", 7), ("field", 7), ("meaning", 7.5),
        ("summary", 8)]
LEAD, TAIL = 0.2, 0.45
nd = json.load(open(NDIR / "durations.json"))
dur = {d["scene"]: d["duration"] for d in nd}
files = {d["scene"]: d["file"] for d in nd}

shots, t = {}, 0.0
for name, base in BASE:
    ln = max(base, dur[name] + LEAD + (3.2 if name == "summary" else TAIL))
    shots[name] = (round(t, 3), round(t + ln, 3))
    t += ln
TOTAL = round(t, 2)


def at(name, x):
    """샷 시작 기준 x초 (x<0 이면 샷 끝 기준)"""
    a, b = shots[name]
    return round(a + x if x >= 0 else b + x, 3)


def frac(name, k):
    a, b = shots[name]
    return round(a + (b - a) * k, 3)


S = lambda n: shots[n][0]  # noqa: E731
E = lambda n: shots[n][1]  # noqa: E731

captions = [
    (S("hook"), E("hook"), "대회장에서 볼의\n*단단함*을 재요"),
    (S("why"), E("why"), "더 무른 볼이\n레인을 *더 세게* 잡아요"),
    (S("soak"), E("soak"), "용제에 *15시간*\n담가 봤더니"),
    (S("recover"), E("recover"), "몇 주 지나면\n*다시 단단해져요*"),
    (S("rule"), E("rule"), "그래서 올해부터\n*78D 이상*만 승인"),
    (S("field"), E("field"), "대회장에서\n직접 재 보니"),
    (S("meaning"), E("meaning"), "78D로 만든 볼은\n*대부분 73D 위*"),
]
chips = [
    (at("hook", 1.6), E("hook"), "단단함은 D로 표시, 숫자가 클수록 단단", 1300),
    (at("why", 2.2), E("why"), "무를수록 훅이 더 일찍, 더 크게", 1380),
    (at("soak", 2.6), E("soak"), "담근 직후 30.7D", 1180),
    (at("soak", 4.6), E("soak"), "훅은 21보드 넘게 늘어났어요", 1280),
    (at("rule", 1.4), E("rule"), "기름을 90분 넘게 천천히 먹는 볼", 1180),
    (at("rule", 2.6), E("rule"), "78D 이상으로 만들어야 승인", 1280),
    (at("rule", 4.6), E("rule"), "일부 전국 대회는 아예 사용 금지", 1380),
    (at("meaning", 1.2), E("meaning"), "78D로 만든 볼, 써도 대부분 73D 위", 1180),
    (at("meaning", 3.6), E("meaning"), "73D: 대회장 하한선으로 정할 계획", 1280),
]
labels = [
    {"start": at("why", 0.6), "end": E("why"), "text": "단단한 볼", "x": 300, "y": 700, "color": [60, 64, 80]},
    {"start": at("why", 1.0), "end": E("why"), "text": "무른 볼", "x": 800, "y": 700, "color": [0, 160, 180]},
]
gauges = {
    "start": at("recover", 0.4), "end": E("recover"),
    "title": "용제에 15시간 담근 우레탄 볼의 단단함",
    "rows": [
        {"label": "담근 직후", "from": 0, "to": 30.7 / 80, "tag": "30.7D"},
        {"label": "1주 뒤", "from": 0, "to": 59.2 / 80, "tag": "59.2D"},
        {"label": "3주 뒤", "from": 0, "to": 67 / 80, "tag": "67D", "color": [0, 160, 180]},
    ],
}
counter = {
    "start": at("field", 0.3), "end": E("field"),
    "label": "73D 아래로 내려간 볼", "from": 0, "to": 23, "unit": "개",
    "note": "2,043개 중 23개 (1.1%)\n2026 USBC 오픈 챔피언십 현장 측정",
}
summary = {
    "start": S("summary"),
    "result": "무른 볼이 더 휘어서\n*단단함 기준*과\n대회장 측정이 생겼어요",
    "tips_label": "연구 시사점",
    "tips": ["대회 요강의 *우레탄 볼 규정* 확인", "볼을 *용제에 담그지* 않기", "USBC 리그는 *승인 볼*이면 그대로"],
    "note": "미국볼링협회(USBC) 규정 · 현장 측정 보고서",
    "source": "USBC (2025, 2026), bowl.com",
}
ov = {
    "frames": int(round(TOTAL * 24)),
    "captions": [{"start": a, "end": b, "text": x} for a, b, x in captions],
    "chips": [{"start": a, "end": b, "text": x, "y": y} for a, b, x, y in chips],
    "labels": labels, "gauges": gauges, "counter": counter, "summary": summary,
    "caption_style": "stroke",
}

c = json.load(open(POST / "content.json", encoding="utf-8")) if (POST / "content.json").exists() else {}
c.update({
    "format": "reel", "style": "block-character", "ep": 9, "publish_date": "2026-12-01", "kind": "볼링 뉴스",
    "thumb_offset_ms": 1500, "overlay": ov,
    "source": {
        "short": "USBC (2025, 2026)",
        "citation": "USBC (2025.9). Tournament Rule Changes on Slow Oil-Absorbing High-Performance Balls: Key Points and FAQ / "
                    "USBC (2025.9). Report on Bowling Ball Hardness Governance, History, Research and Competitive Impact / "
                    "USBC (2026.7). Hardness Field Testing Research Report",
        "url": "https://bowl.com/equipment-specifications/ball-hardness-research",
    },
    "narration": {"voice": "clone", "dir": NDIR.name},
})
json.dump(c, open(POST / "content.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

ev = []
for n, _ in BASE[1:]:
    ev.append(["whoosh", round(S(n) - 0.25, 3), 0.9])
for a, *_ in captions + chips:
    ev.append(["pop", round(a + 0.05, 3), 0.8])
for lb in labels:
    ev.append(["pop", lb["start"], 0.9])
# hook: 검사기 누름 (anim press 주기 2.2초, 0.6초 시작, 누름 정점 25%)
k = 0
while S("hook") + 0.6 + 0.55 + 2.2 * k < E("hook") - 0.3:
    ev.append(["thud", round(S("hook") + 0.6 + 0.55 + 2.2 * k, 3), 0.45])
    ev.append(["tick", round(S("hook") + 0.6 + 0.6 + 2.2 * k, 3), 1.0])
    k += 1
# why: 두 볼 굴러감 + 충돌
hit = frac("why", 0.78)
ev += [["roll", S("why"), round(hit - S("why"), 3), 0.7], ["pin_crash", round(hit + 0.05, 3), 1.0]]
# soak: 볼 담그기 + 기포
ev.append(["thud", at("soak", 1.5), 0.6])
for i in range(6):
    ev.append(["drip", round(at("soak", 1.9) + i * 0.8, 3), 0.8])
# recover: 세 번 누름 + 게이지
rd = E("recover") - S("recover")
per = (rd - 0.6) / 3
for i in range(3):
    ev.append(["thud", round(S("recover") + 0.2 + per * (i + 0.25), 3), 0.45])
for i in range(3):
    ev.append(["rise", round(at("recover", 0.7 + i * 0.35), 3), 0.8])
# field: 숫자 tick
for i in range(12):
    ev.append(["tick", round(at("field", 0.6 + i * 0.13), 3), 1.0])
ev.append(["heartbeat", at("field", 2.6), 0.5])
# meaning: 투구
md = E("meaning") - S("meaning")
rel = S("meaning") + md * 0.36
mhit = frac("meaning", 0.82)
ev += [["slide", round(rel - 0.9, 3), 1.0], ["thud", round(rel + 0.1, 3), 0.8],
       ["roll", round(rel + 0.1, 3), round(mhit - rel - 0.1, 3), 0.8], ["pin_crash", round(mhit + 0.05, 3), 1.0]]
ev.append(["chime", S("summary"), 1.0])
for name, _ in BASE:
    ev.append(["voice", round(S(name) + LEAD, 3), str(NDIR / files[name])])
json.dump({"duration": TOTAL, "events": ev}, open(POST / "audio.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"shots": [{"name": n, "start": shots[n][0], "end": shots[n][1]} for n, _ in BASE], "total": TOTAL},
          open(POST / "timeline.json", "w"), indent=1)
print("총 길이", TOTAL, "초 /", ov["frames"], "프레임")
for n, _ in BASE:
    a, b = shots[n]
    print(f"{n:8s} {a:6.2f} ~ {b:6.2f}  ({b - a:.2f}s, 나레이션 {dur[n]:.2f}s)")
