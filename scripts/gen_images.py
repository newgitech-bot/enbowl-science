"""GPT Image로 카드뉴스 일러스트 생성.

requests/images/*.json 요청 파일을 읽어, 아직 결과가 없는 항목만 생성한다.
요청 형식:
{
  "character": "a chubby brown bear in a red bowling shirt",   # 에피소드마다 자유롭게
  "items": [
    {"out": "assets/gpt/ep06/01_cover.png", "prompt": "..."},
    {"out": "assets/gpt/ep06/02_vs.png",
     "refs": ["assets/gpt/ep06/01_cover.png"], "prompt": "..."}
  ]
}
- 캐릭터는 에피소드마다 바꾼다. 한 에피소드 안에서는 표지 그림을 refs로 넣어 같은 캐릭터를 유지한다.
- items는 위에서부터 순서대로 만들어지므로, 앞에서 만든 그림을 뒤 항목의 refs로 쓸 수 있다.
- 공통 화풍(흰 배경, 굵은 외곽선, 플랫 2D, 글자 없음)은 STYLE에 고정.
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
    "Flat cute 2D illustration, thick clean black outlines, simple soft shading, "
    "Korean Instagram card-news style. No text, no letters, no numbers anywhere in the image. "
)
KEEP = "Keep the character exactly the same as in the reference image (face, colors, outfit, proportions). "


def build_prompt(character, item):
    parts = [STYLE]
    if character:
        parts.append(f"Main character: {character}. ")
    if item.get("refs"):
        parts.append(KEEP)
    parts.append(item["prompt"])
    return "".join(parts)


def call(model, item, key, character=""):
    headers = {"Authorization": f"Bearer {key}"}
    data = {
        "model": model,
        "prompt": build_prompt(character, item),
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
        spec = json.load(open(req, encoding="utf-8"))
        character = spec.get("character", "")
        for item in spec["items"]:
            out = item["out"]
            if os.path.exists(out):
                print(f"skip {out} (이미 있음)")
                continue
            for model in MODELS:
                r = call(model, item, key, character)
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
