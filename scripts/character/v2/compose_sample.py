"""샘플 프레임(48fps 타임라인)을 24fps 영상으로 합성. 0~206 은 2프레임마다(정상 속도), 208~ 은 전부(0.5배 슬로모션).
사용법: python compose_sample.py FRAMES_DIR OUT.mp4
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import sfx  # noqa: E402

NORMAL = list(range(0, 207, 2))
SLOW = list(range(208, 331))


def main(src, out):
    tmp = tempfile.mkdtemp()
    seq = NORMAL + SLOW
    for i, f in enumerate(seq):
        shutil.copy(os.path.join(src, f"{f:04d}.png"), os.path.join(tmp, f"{i:04d}.png"))
    dur = len(seq) / 24
    t = lambda f: (NORMAL.index(f) if f in NORMAL else len(NORMAL) + SLOW.index(f)) / 24  # noqa: E731
    spec = {"duration": dur + 0.3, "events": [
        ["slide", t(100), 1.0],
        ["roll", t(116), t(206) - t(116) + 0.6, 0.8],
        ["whoosh", t(134) - 0.15, 0.6],
        ["whoosh", t(208) - 0.15, 0.6],
        ["pin_crash", t(222)],
        ["thud", t(222), 0.5],
    ]}
    wav = os.path.join(tmp, "a.wav")
    sfx.build(spec, wav)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", os.path.join(tmp, "%04d.png"),
                    "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("저장:", out, f"{dur:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
