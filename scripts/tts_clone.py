#!/usr/bin/env python3
"""CosyVoice 2 로 준서님 목소리를 복제해 narration.json 을 읽는다.
참고 음성은 Secrets 의 VOICE_REF_B64 (opus, base64) 에서 꺼내 쓰고 저장소에는 남기지 않는다.
사용법 (CosyVoice 폴더 안에서): python ../scripts/tts_clone.py ../posts/<폴더> <출력폴더이름>
"""
import base64, json, os, subprocess, sys, wave
from pathlib import Path
sys.path.insert(0, os.getcwd()); sys.path.append(os.path.join(os.getcwd(), "third_party/Matcha-TTS"))
import torchaudio
from cosyvoice.cli.cosyvoice import CosyVoice2

post = Path(sys.argv[1]); outname = sys.argv[2] if len(sys.argv) > 2 else "narration_clone"
Path("/tmp/ref.opus").write_bytes(base64.b64decode(os.environ["VOICE_REF_B64"]))
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "/tmp/ref.opus", "-ac", "1", "-ar", "16000", "/tmp/ref.wav"], check=True)

prompt_text = os.environ.get("VOICE_REF_TEXT", "").strip() or "안녕하세요, 앤볼입니다. 오늘은 압박감이 볼링 투구에 어떤 영향을 주는지, 실제 연구 결과로 알아보겠습니다."
if not prompt_text:
    from faster_whisper import WhisperModel
    segs, _ = WhisperModel("small", device="cpu", compute_type="int8").transcribe("/tmp/ref.wav", language="ko")
    prompt_text = " ".join(s.text.strip() for s in segs)
print("참고 음성 문장:", prompt_text)

cv = CosyVoice2("pretrained_models/CosyVoice2-0.5B", load_jit=False, load_trt=False, fp16=False)
prompt = "/tmp/ref.wav"  # 최신 CosyVoice 는 파일 경로를 받음
spec = json.loads((post / "narration.json").read_text(encoding="utf-8"))
out = post / outname; out.mkdir(exist_ok=True)
info = []
for i, line in enumerate(spec["lines"]):
    f = out / f"{i:02d}_{line['scene']}.wav"
    chunks = [r["tts_speech"] for r in cv.inference_zero_shot(line["text"], prompt_text, prompt, stream=False)]
    import torch
    torchaudio.save(str(f), torch.cat(chunks, dim=1), cv.sample_rate)
    with wave.open(str(f)) as w:
        d = w.getnframes() / w.getframerate()
    info.append({**line, "file": f.name, "duration": round(d, 3)})
    print(f.name, round(d, 2), line["text"], flush=True)
(out / "durations.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
