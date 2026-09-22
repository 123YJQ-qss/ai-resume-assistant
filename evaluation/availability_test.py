"""availability_test.py - 接口可用性 / 故障注入真实测量。

测量项（短时窗口快照，不等同于长期 SLA uptime）：
- 可用性(2xx)       = 返回 2xx 的请求占比
- 可用性(无5xx)     = 返回 2xx 或 4xx（服务正确响应，即使业务拒绝）占比
- 5xx 率 / 连接错误率
- 平均响应时间与 P95

用法（需先启动 FastAPI）：
    python evaluation/availability_test.py --base http://127.0.0.1:8005 --n 200
"""
import argparse
import json
import statistics
import time

import httpx

VALID_ANALYZE_BODY = {
    "job_description": "负责AI产品的需求分析、方案设计与落地，要求具备3年以上产品经验，熟悉机器学习与大模型应用开发，具备沟通和团队协作能力。",
    "resume_text": "我是一名AI产品经理，负责过多个人工智能产品的规划与设计。",
}


def request(client, method, url, **kwargs):
    t0 = time.perf_counter()
    err = None
    status = None
    try:
        r = client.request(method, url, **kwargs)
        status = r.status_code
    except Exception as e:
        err = type(e).__name__
    latency = (time.perf_counter() - t0) * 1000
    return status, err, latency


def run(base, n_health, n_analyze, n_invalid):
    results = {"2xx": 0, "4xx": 0, "5xx": 0, "conn_error": 0, "latencies": []}
    with httpx.Client(timeout=30, trust_env=False) as client:
        # 健康检查
        for _ in range(n_health):
            s, e, lat = request(client, "GET", base + "/api/health")
            results["latencies"].append(lat)
            _bump(results, s, e)
        # 有效分析请求（当前无 LLM 凭证 → 应返回 200 + mock_fallback）
        for _ in range(n_analyze):
            s, e, lat = request(client, "POST", base + "/api/analyze", json=VALID_ANALYZE_BODY)
            results["latencies"].append(lat)
            _bump(results, s, e)
        # 无效 JD（应被服务正确拒绝 → 400，属于服务正确处理，不计 5xx）
        for _ in range(n_invalid):
            s, e, lat = request(client, "POST", base + "/api/analyze", json={"job_description": "短", "resume_text": "x"})
            results["latencies"].append(lat)
            _bump(results, s, e)

    total = n_health + n_analyze + n_invalid
    lat = sorted(results["latencies"])
    summary = {
        "total_requests": total,
        "2xx": results["2xx"],
        "4xx": results["4xx"],
        "5xx": results["5xx"],
        "conn_error": results["conn_error"],
        "availability_2xx": round(results["2xx"] / total, 4) if total else 0,
        "availability_no_5xx": round((results["2xx"] + results["4xx"]) / total, 4) if total else 0,
        "avg_latency_ms": round(statistics.mean(lat), 2) if lat else 0,
        "p95_latency_ms": round(lat[int(len(lat) * 0.95)] if lat else 0, 2),
    }
    return summary


def _bump(results, status, err):
    if err:
        results["conn_error"] += 1
    elif status is not None and 200 <= status < 300:
        results["2xx"] += 1
    elif status is not None and 400 <= status < 500:
        results["4xx"] += 1
    elif status is not None and status >= 500:
        results["5xx"] += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8005")
    ap.add_argument("--n", type=int, default=200)
    args = ap.parse_args()
    summary = run(args.base, args.n, int(args.n / 2), int(args.n / 4))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()