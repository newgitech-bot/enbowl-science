#!/usr/bin/env python3
"""CosyVoice 2 로 준서님 목소리를 복제해 narration.json 을 읽는다.
참고 음성은 voice/ref.flac.gpg 를 Secrets 의 VOICE_KEY 로 복호화해서 쓴다 (원본은 저장소에 없음).
사용법 (CosyVoice 폴더 안에서): python ../scripts/tts_clone.py ../posts/<폴더> <출력폴더이름>
"""
import base64, json, os, subprocess, sys, wave
from pathlib import Path
sys.path.insert(0, os.getcwd()); sys.path.append(os.path.join(os.getcwd(), "third_party/Matcha-TTS"))
import soundfile as sf
from cosyvoice.cli.cosyvoice import CosyVoice2

REF_TEXT = ("안녕하세요, 앤볼입니다. 볼링을 오래 치다 보면, 연습 때는 잘 되던 투구가 중요한 순간에만 흔들릴 때가 있죠? "
            "저도 선수 생활을 하면서 그런 순간을 정말 많이 겪었습니다. 그래서 오늘은 그 이유를 실제 연구 결과로 알아보려고 해요. "
            "세계 랭커 열한 명이 참여한 실험인데요, 결과를 보면 생각보다 간단한 데서 답을 찾을 수 있습니다. "
            "끝까지 보시고, 다음 게임에 꼭 적용해 보세요!")
post = Path(sys.argv[1]); outname = sys.argv[2] if len(sys.argv) > 2 else "narration_clone"
# 참고 음성: 저장소의 voice/ref.flac.gpg 를 Secrets 의 VOICE_KEY 로 복호화
enc = Path(__file__).resolve().parent.parent / "voice" / "ref.flac.gpg"
subprocess.run(["gpg", "--batch", "--yes", "--pinentry-mode", "loopback", "--passphrase", os.environ["VOICE_KEY"],
                "-o", "/tmp/ref.flac", "-d", str(enc)], check=True)
src = "/tmp/ref.flac"
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-ac", "1", "-ar", "24000", "/tmp/ref.wav"], check=True)

prompt_text = os.environ.get("VOICE_REF_TEXT", "").strip() or REF_TEXT
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
    sf.write(str(f), torch.cat(chunks, dim=1).squeeze(0).cpu().numpy(), cv.sample_rate, subtype="PCM_16")
    with wave.open(str(f)) as w:
        d = w.getnframes() / w.getframerate()
    info.append({**line, "file": f.name, "duration": round(d, 3)})
    print(f.name, round(d, 2), line["text"], flush=True)
(out / "durations.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
