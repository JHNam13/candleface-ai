import os
import json
import base64
import requests
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

today = datetime.now().strftime("%Y-%m-%d")

prompt = f"""
오늘 날짜: {today}

한국·미국 주요 대형주/중형주 뉴스 중 가장 화제성이 높은 종목 1개를 고르고,
캔들관상소 텔레그램 콘텐츠를 JSON만 출력하라.

규칙:
- 투자 권유 금지
- 뉴스 단순 요약 금지
- 재치 있는 차트 관상 콘셉트
- 특정 인물 비방 금지
- 이미지 프롬프트는 영어
- 이미지 오브젝트는 2~4개만
- 캡션은 이모지 1개 포함 2줄 + 관상평

출력 JSON 형식:
{{
  "top_stock": "",
  "gwansang_name": "",
  "main_text": "",
  "key_facts": ["", "", ""],
  "image_prompt_en": "",
  "caption": "",
  "news_links": ["", ""]
}}
"""

response = client.responses.create(
    model="gpt-4.1-mini",
    tools=[{"type": "web_search_preview"}],
    input=prompt,
)

raw_text = response.output_text.strip()

try:
    data = json.loads(raw_text)
except json.JSONDecodeError:
    print("JSON parsing failed.")
    print(raw_text)
    raise

image_prompt = f"""
{data["image_prompt_en"]}

Meme cartoon style, bold graphic design, 1:1 square composition.
Use only 2 to 4 key objects.
Minimal Korean text only: "{data["main_text"]}".
Add a subtle candlestick chart background.
Thumbnail-worthy, instantly readable, witty financial news parody.
No investment advice.
"""

img = client.images.generate(
    model="gpt-image-1",
    prompt=image_prompt,
    size="1024x1024"
)

image_bytes = base64.b64decode(img.data[0].b64_json)
image_path = "candleface_today.png"

with open(image_path, "wb") as f:
    f.write(image_bytes)

caption = data["caption"].strip()

if data.get("news_links"):
    caption += "\n\n📰 참고 뉴스:\n" + "\n".join(data["news_links"][:2])

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"

with open(image_path, "rb") as photo:
    result = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": caption,
        },
        files={"photo": photo},
        timeout=60,
    )

print(result.status_code)
print(result.text)

if not result.ok:
    raise RuntimeError("Telegram send failed.")
