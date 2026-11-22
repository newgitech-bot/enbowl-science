"""새 나레이션 길이에 맞춰 EP05 타임라인·오버레이·오디오를 다시 짠다.
사용법: python build_ep05.py NARRATION_DIR   (예: posts/2026-11-27-EP05/narration_clone_fun)
결과: posts/.../timeline.json, content.json(overlay 갱신), audio.json
"""
import json
import subprocess
import sys
from pathlib import Path

POST = Path("posts/2026-11-27-EP05")
NDIR = Path(sys.argv[1]) if len(sys.argv) > 1 else POST / "narration_clone"
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
CAPS = [   # 대본과 같은 말·같은 용어(부담)로 다시 쓴 자막 (원래 순서대로 9개)
    "중요한 프레임에서만\n공이 *빠질 때*",
    "세계 100위 안 선수\n*11명*이 확인했어요",
    "같은 선수가\n*두 번* 던졌어요",
    "부담 조건엔\n*이런 장치*를 걸었어요",
    "마음은\n어떻게 달라졌을까요?",
    "*몸이 먼저*\n빨라졌어요",
    "그 결과",
    "볼 속도는\n*거의 같았어요*",
    "힘보다 *리듬*이\n중요할 수 있어요",
]
for c, txt in zip(ov["captions"], CAPS):
    c["text"] = txt
for c in ov["chips"]:
    c["text"] = c["text"].replace("두 경우 모두 7.58 m/s", "스트라이크·아닌 공 모두 7.58 m/s")
for c in ov["labels"]:
    c["text"] = c["text"].replace("압박", "부담")
ov["gauges"]["title"] = ov["gauges"]["title"].replace("압박", "부담")
ov["counter"]["note"] = ov["counter"]["note"].replace("압박", "부담")
for key in ("captions", "chips", "labels"):
    for c in ov.get(key, []):
        c["start"], c["end"] = remap(c["start"]), remap(c["end"])
for key in ("gauges", "counter"):
    ov[key]["start"], ov[key]["end"] = remap(ov[key]["start"]), remap(ov[key]["end"])
sm = ov["summary"]
sm["start"] = remap(sm["start"])
sm["result"] = "부담을 받으면\n마음보다 *몸이 먼저*\n빨라져요"
sm["tips_label"] = "연구 시사점"
sm["tips"] = ["포스텝~슬라이드는 *평소 속도*로", "자신 있어도 *몸은 서두를 수* 있어요", "힘보다 *리듬*을 지키기"]
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
