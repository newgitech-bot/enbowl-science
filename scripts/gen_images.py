"""GPT Image로 카드뉴스 일러스트 생성.

requests/images/*.json 요청 파일을 읽어, 아직 결과가 없는 항목만 생성한다.
요청 형식:
{
  "items": [
    {"out": "assets/gpt/ep06_cover.png",
     "refs": ["assets/character/ref_think.png"],
     "prompt": "...",
     "size": "1024x1024", "quality": "medium"}
  ]
}
기준 캐릭터 이미지(refs)를 함께 보내 매번 같은 캐릭터가 나오게 한다.
"""
import base64
import glob
import json
import os
import sys

import requests

API = "https://api.openai.com/v1/images"
MODELS = ["gpt-image-2", "gpt-image-1.5", "gpt-image-1"]

STYLE = (
    "Keep the character from the reference image exactly the same: same face, "
    "black bowl-cut hair, rosy cheeks, orange sweater, navy pants, white sneakers, "
    "thick black outlines, flat cute 2D illustration style. "
    "No text, no letters, no numbers anywhere in the image. "
)


def call(model, item, key):
    headers = {"Authorization": f"Bearer {key}"}
    data = {
        "model": model,
        "prompt": STYLE + item["prompt"],
        "size": item.get("size", "1024x1024"),
        "quality": item.get("quality", "medium"),
        "n": "1",
    }
    refs = item.get("refs", [])
    if refs:
        files = [("image[]", (os.path.basename(p), open(p, "rb"), "image/png")) for p in refs]
        r = requests.post(f"{API}/edits", headers=headers, data=data, files=files, timeout=300)
    else:
        r = requests.post(f"{API}/generations", headers=headers, json={**data, "n": 1}, timeout=300)
    return r


def main():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("OPENAI_API_KEY 없음")
    done = 0
    for req in sorted(glob.glob("requests/images/*.json")):
        for item in json.load(open(req, encoding="utf-8"))["items"]:
            out = item["out"]
            if os.path.exists(out):
                print(f"skip {out} (이미 있음)")
                continue
            for model in MODELS:
                r = call(model, item, key)
                if r.ok:
                    break
                print(f"{model} 실패 {r.status_code}: {r.text[:500]}")
                # 모델이 없거나 권한 문제일 때만 다음 모델로
                if r.status_code not in (400, 403, 404):
                    break
            if not r.ok:
                sys.exit(1)
            body = r.json()
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "wb") as f:
                f.write(base64.b64decode(body["data"][0]["b64_json"]))
            print(f"ok {out} ({model}) usage={json.dumps(body.get('usage', {}))}")
            done += 1
    print(f"생성 {done}장")


if __name__ == "__main__":
    main()
