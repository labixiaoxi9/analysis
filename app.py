import os
from typing import Any, Dict

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from requests.exceptions import ConnectTimeout, ConnectionError, ReadTimeout, RequestException

load_dotenv()

API_URL = "https://832fcrwjv4.coze.site/run"
API_TOKEN = os.getenv("COZE_API_TOKEN")
TIMEOUT = (10, 360)  # connect, read

app = FastAPI(title="Industry Analysis API Proxy")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    industry_name: str = Field(..., min_length=1)


@app.get("/")
def serve_index() -> FileResponse:
    return FileResponse("index.html")


@app.post("/api/run")
@app.post("/run")
def run_api(req: RunRequest) -> Dict[str, Any]:
    if not API_TOKEN:
        raise HTTPException(status_code=500, detail="服务端未配置 COZE_API_TOKEN")

    payload = {"industry_name": req.industry_name.strip()}
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=TIMEOUT)
    except (ReadTimeout, ConnectTimeout):
        raise HTTPException(status_code=504, detail="上游接口超时，请稍后重试")
    except ConnectionError:
        raise HTTPException(status_code=502, detail="连接上游接口失败")
    except RequestException as e:
        raise HTTPException(status_code=500, detail=f"请求异常: {str(e)}")

    try:
        data = resp.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="上游返回非 JSON，无法解析 report_url")

    report_url = data.get("report_url") if isinstance(data, dict) else None
    if not report_url and isinstance(data, dict):
        nested_data = data.get("data")
        if isinstance(nested_data, dict):
            report_url = nested_data.get("report_url")

    if not report_url:
        raise HTTPException(status_code=502, detail="上游响应中未找到 report_url")

    return {"report_url": report_url}
