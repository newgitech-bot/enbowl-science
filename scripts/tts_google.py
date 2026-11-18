#!/usr/bin/env python3
"""Google Cloud TTS 로 나레이션 생성.
  python scripts/tts_google.py --samples            한국어 목소리 샘플들을 samples/voices/ 에 생성
  python scripts/tts_google.py posts/<폴더>         narration.json 의 voice(google:<이름>) 로 생성
환경변수 GCP_TTS_KEY: 서비스 계정 JSON 내용
"""
import json, os, sys, wave, io
from pathlib import Path
from google.oauth2 import service_account
from google.cloud import texttospeech as tts

creds = service_account.Credentials.from_service_account_info(json.loads(os.environ["GCP_TTS_KEY"]))
client = tts.TextToSpeechClient(credentials=creds)

def synth(text, voice, path, rate=1.0):
    res = client.synthesize_speech(
        input=tts.SynthesisInput(text=text),
        voice=tts.VoiceSelectionParams(language_code="ko-KR", name=voice),
        audio_config=tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16, sample_rate_hertz=24000,
                                     speaking_rate=rate))
    Path(path).write_bytes(res.audio_content)
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()

if sys.argv[1] == "--samples":
    out = Path("samples/voices"); out.mkdir(parents=True, exist_ok=True)
    text = "중요한 프레임만 되면, 공이 꼭 빗나가죠? 세계 랭커 열한 명이 이 문제로 실험에 참여했습니다."
    voices = [v.name for v in client.list_voices(language_code="ko-KR").voices]
    pick = [v for v in voices if "Chirp3-HD" in v][:10] + [v for v in voices if "Neural2" in v]
    for v in pick:
        d = synth(text, v, out / f"google_{v}.wav")
        print(v, round(d, 2))
    (out / "google_voices.txt").write_text("\n".join(voices), encoding="utf-8")
else:
    post = Path(sys.argv[1])
    spec = json.loads((post / "narration.json").read_text(encoding="utf-8"))
    voice = spec["voice"].split(":", 1)[1]
    out = post / "narration"; out.mkdir(exist_ok=True)
    info = []
    for i, line in enumerate(spec["lines"]):
        f = out / f"{i:02d}_{line['scene']}.wav"
        d = synth(line["text"], voice, f, spec.get("speed", 1.0))
        info.append({**line, "file": f.name, "duration": round(d, 3)})
        print(f.name, round(d, 2))
    (out / "durations.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
