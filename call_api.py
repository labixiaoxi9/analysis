import os
import json
import time
import requests
from dotenv import load_dotenv
from requests.exceptions import ReadTimeout, ConnectTimeout, ConnectionError, RequestException

load_dotenv()

API_URL = "https://832fcrwjv4.coze.site/run"
API_TOKEN = os.getenv("COZE_API_TOKEN")

if not API_TOKEN:
    raise ValueError("请先在 .env 中设置 COZE_API_TOKEN")

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}

industry_name = input("请输入行业名称（必填，例如：新能源汽车）：").strip()
if not industry_name:
    raise ValueError("industry_name 为必填，请输入行业名称")

user_input = input("请输入补充说明（可选，直接回车跳过）：").strip()

payload = {
    "industry_name": industry_name,
    "input": user_input,
}

# 超时策略：连接超时 10 秒，读取超时 120 秒
TIMEOUT = (10, 360)
MAX_RETRIES = 3
RETRY_SLEEP_SECONDS = 2

resp = None
for attempt in range(1, MAX_RETRIES + 1):
    try:
        print(f"\n第 {attempt}/{MAX_RETRIES} 次请求中...")
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=TIMEOUT)
        break
    except (ReadTimeout, ConnectTimeout) as e:
        print(f"请求超时: {e}")
        if attempt < MAX_RETRIES:
            print(f"{RETRY_SLEEP_SECONDS} 秒后重试...")
            time.sleep(RETRY_SLEEP_SECONDS)
        else:
            raise SystemExit(
                "多次请求超时。建议：\n"
                "1) 稍后重试；\n"
                "2) 减少 input 内容长度；\n"
                "3) 检查网络/代理；\n"
                "4) 如接口处理时间较长，可继续增大读取超时。"
            )
    except ConnectionError as e:
        raise SystemExit(f"网络连接失败: {e}")
    except RequestException as e:
        raise SystemExit(f"请求异常: {e}")

if resp is None:
    raise SystemExit("请求未成功发出")

print("status:", resp.status_code)
try:
    print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
except ValueError:
    print(resp.text)
