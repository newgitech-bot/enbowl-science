"""새 나레이션 길이에 맞춰 EP05 타임라인·오버레이·오디오를 다시 짠다.
사용법: python build_ep05.py NARRATION_DIR   (예: posts/2026-11-27-EP05/narration_clone_fun)
결과: posts/.../timeline.json, content.json(overlay 갱신), audio.json
"""
import json
import subprocess
import sys
from pathlib import Path

POST = Path("posts/2026-11-27-EP05")
NDIR = Path(sys.argv[1])
OLD = [("hook", 0, 3), ("intro", 3, 8), ("compare", 8, 15), ("mind", 15, 20), ("slowmo", 20, 27),
       ("pins", 27, 32), ("speed", 32, 38), ("summary", 38, 46)]
LEAD, TAIL = 0.2, 0.45
dur = {d["scene"]: d["duration"] for d in json.load(open(NDIR / "durations.json"))}

new, t = [], 0.0
for name, a, b in OLD:
    base = b - a
    ln = max(base, dur[name] + LEAD + TAIL) if name != "summary" else max(base, dur[name] + LEAD + 3.2)
    new.append((name, t, t + ln))
    t += ln
TOTAL = round(t, 2)


def remap(x):
    for (n, a, b), (_, na, nb) in zip(OLD, new):
        if a <= x <= b:
            return round(na + (x - a) / (b - a) * (nb - na), 3)
    return round(x - OLD[-1][2] + new[-1][2], 3)


old_c = json.loads(subprocess.run(["git", "show", f"main:{POST}/content.json"], capture_output=True, text=True,
                                  check=True).stdout)
old_a = json.loads(subprocess.run(["git", "show", f"main:{POST}/audio.json"], capture_output=True, text=True,
                                  check=True).stdout)
ov = old_c["overlay"]
TXT = {   # 해요체 자막
    "세계 랭커 *11명*이\n실험에 참여했습니다": "세계 랭커 *11명*이\n직접 실험했어요",
    "같은 선수에게\n*두 번* 던지게 했습니다": "같은 선수가\n*두 번* 던졌어요",
    "압박 조건에는\n*이런 장치*를 걸었습니다": "압박 조건엔\n*이런 장치*를 걸었어요",
    "마음은 어떻게\n변했을까?": "마음은 어떻게\n변했을까요?",
    "그런데 *몸은 먼저*\n서둘렀습니다": "그런데 *몸이 먼저*\n서둘렀어요",
    "스트라이크든 아니든\n볼 속도는 *똑같았습니다*": "스트라이크든 아니든\n볼 속도는 *똑같았어요*",
    "문제는 힘이 아니라\n*리듬*입니다": "힘이 아니라\n*리듬* 문제였어요",
}
for c in ov["captions"]:
    c["text"] = TXT.get(c["text"], c["text"])
for key in ("captions", "chips", "labels"):
    for c in ov.get(key, []):
        c["start"], c["end"] = remap(c["start"]), remap(c["end"])
for key in ("gauges", "counter"):
    ov[key]["start"], ov[key]["end"] = remap(ov[key]["start"]), remap(ov[key]["end"])
sm = ov["summary"]
sm["start"] = remap(sm["start"])
sm["result"] = sm["result"].replace("서두릅니다", "서둘러요")
sm["tips_label"] = "연구 시사점"
sm["tips"] = [x.replace("있다", "있어요").replace("만든다", "만들어요") for x in sm["tips"]]
ov["frames"] = int(round(TOTAL * 24))
ov["caption_style"] = "stroke"
c = json.load(open(POST / "content.json", encoding="utf-8"))
c["overlay"] = ov
c["style"] = "block-character"
json.dump(c, open(POST / "content.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

ev = []
for e in old_a["events"]:
    if e[0] == "voice":
        continue
    e = list(e)
    e[1] = remap(e[1])
    if e[0] == "roll":   # 길이도 비율대로
        e[2] = round(e[2] * 1.0, 3)
    ev.append(e)
files = {d["scene"]: d["file"] for d in json.load(open(NDIR / "durations.json"))}
for name, a, b in new:
    ev.append(["voice", round(a + LEAD, 3), str(NDIR / files[name])])
json.dump({"duration": TOTAL, "events": ev}, open(POST / "audio.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"shots": [{"name": n, "start": round(a, 3), "end": round(b, 3)} for n, a, b in new], "total": TOTAL},
          open(POST / "timeline.json", "w"), indent=1)
print("총 길이", TOTAL, "초 /", ov["frames"], "프레임")
for n, a, b in new:
    print(f"{n:8s} {a:6.2f} ~ {b:6.2f}  ({b - a:.2f}s, 나레이션 {dur[n]:.2f}s)")
