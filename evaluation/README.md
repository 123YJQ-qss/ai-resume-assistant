# Evaluation 框架使用说明

本目录实现「AI 简历优化助手」的 **Baseline vs Improved** 自动化评测，用于把简历中想写的
「量化指标」转化为可复现、可验证的真实测量，杜绝手工填写数字。

## 目录结构

```
evaluation/
├── README.md                # 本文件
├── data/
│   └── testset.py           # 24 组标注测试数据（JD + 简历 + 人工标注答案）
├── metrics.py               # 8 项指标计算方法（纯函数）
├── llm_backends.py          # 评测后端（RealBackend / MockBackend）
├── run_eval.py              # Baseline vs Improved 自动对照主脚本
├── availability_test.py     # 接口可用性 / 故障注入真实测量
└── results/                 # 运行结果 JSON（eval_result / fault / malformed）
```

## 快速开始

```bash
# 1. 干净运行（结构指标 + 管道自检）
python evaluation/run_eval.py --backend mock

# 2. 故障注入（LLM 故障率 25%，验证降级）
python evaluation/run_eval.py --backend mock --fault-rate 0.25 --out evaluation/results/fault.json

# 3. 畸形 JSON 注入（解析健壮性）
python evaluation/run_eval.py --backend mock --malformed-rate 0.25 --out evaluation/results/malformed.json

# 4. 真实 LLM（需先在项目根配置 .env 真实凭证）
python evaluation/run_eval.py --backend real
```

## 接口可用性测量（需先启动服务）

```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8007   # 另开终端
# 回到项目根
python evaluation/availability_test.py --base http://127.0.0.1:8007 --n 200
```

## 关键约束（务必理解）

- **MockBackend 不是真实模型**：它按人工标注返回确定性 JSON，用于验证评测管道本身与测量
  结构/机械指标（JSON 解析率、字段完整率、Workflow 成功率、响应时间、输入 token 量）。
  用它得到的「匹配准确率 = 1.0」是**自检值**，不代表模型真实能力，**不可写入简历**。
- **内容正确性指标**（匹配准确率、技能识别、建议可执行性）必须使用 `--backend real` 且
  配置真实 LLM 凭证后才有意义。
- 结果文件 `results/*.json` 可复现；修改 `data/testset.py` 的人工标注即可扩充或调整评测集。