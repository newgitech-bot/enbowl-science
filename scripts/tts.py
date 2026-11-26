#!/usr/bin/env python3
"""narration.json 의 문장을 MeloTTS(한국어)로 읽어 narration/ 에 wav 와 길이 정보를 저장한다.
GitHub Actions 에서 실행 (모델 다운로드에 인터넷 필요).
사용법: python scripts/tts.py posts/2026-11-27-EP07
"""
import json, sys, wave
from pathlib import Path
from melo.api import TTS

post = Path(sys.argv[1])
spec = json.loads((post / "narration.json").read_text(encoding="utf-8"))
out = post / "narration"; out.mkdir(exist_ok=True)
model = TTS(language="KR", device="cpu")
spk = model.hps.data.spk2id["KR"]
info = []
for i, line in enumerate(spec["lines"]):
    f = out / f"{i:02d}_{line['scene']}.wav"
    model.tts_to_file(line["text"], spk, str(f), speed=spec.get("speed", 1.0))
    with wave.open(str(f)) as w:
        dur = w.getnframes() / w.getframerate()
    info.append({**line, "file": f.name, "duration": round(dur, 3)})
    print(f"{f.name}: {dur:.2f}s  {line['text']}")
(out / "durations.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
