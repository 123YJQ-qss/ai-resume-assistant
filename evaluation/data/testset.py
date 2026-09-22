"""评测测试集：JD + 简历 + 人工标注答案（ground truth）。

字段说明：
- jd: 岗位 JD 原文
- resume: 简历原文
- expected_skills: 岗位要求且应被识别出的技能/关键词（用于关键词匹配 & 技能识别）
- expected_gaps: 岗位要求但简历缺失的技能（用于缺口识别）
- expected_match_level: 人工标注的匹配等级（取值与系统 match_level 定义一致：
    overall∈{较高,中等,较低}；ability/experience∈{较强,中等,较弱}；risk∈{需要优化,风险较低,风险较高}）

仅用于评测，不参与业务逻辑。
"""

CATEGORIES = ["AI应用开发", "Python开发", "Java后端", "普通后端"]

TEST_CASES = [
    # ---------------- AI应用开发 ----------------
    {
        "id": "ai_01", "category": "AI应用开发",
        "jd": "负责大模型应用开发，要求熟练 Python、FastAPI、LLM API 调用与 Prompt Engineering，熟悉 RAG 与向量检索，具备模型部署经验。",
        "resume": "3 年 Python 后端，使用 FastAPI 开发接口，调用过 OpenAI/DeepSeek 接口，做过基于向量检索的 RAG demo，写过提示词模板。",
        "expected_skills": ["Python", "FastAPI", "LLM API", "Prompt Engineering", "RAG", "向量检索"],
        "expected_gaps": ["模型部署经验"],
        "expected_match_level": {"overall": "较高", "ability": "较强", "experience": "中等", "risk": "需要优化"},
    },
    {
        "id": "ai_02", "category": "AI应用开发",
        "jd": "AI 产品研发，要求掌握大模型 API、流式输出、token 计算，熟悉 Embedding 与向量数据库，能独立封装统一的 LLM 客户端。",
        "resume": "做过 LLM 调用与流式输出，了解 Embedding，用 FAISS 做过检索，封装过内部 LLM 工具，但对向量数据库运维不熟。",
        "expected_skills": ["大模型 API", "流式输出", "Embedding", "向量数据库", "LLM 客户端封装"],
        "expected_gaps": ["token 计算"],
        "expected_match_level": {"overall": "较高", "ability": "较强", "experience": "中等", "risk": "需要优化"},
    },
    {
        "id": "ai_03", "category": "AI应用开发",
        "jd": "NLP 应用工程师，要求掌握语言模型微调、检索增强生成 RAG、向量索引，熟悉 Python 与 PyTorch。",
        "resume": "Python 熟练，用过 sentence-transformers 做向量化，实现过简单 RAG，了解微调概念但未实际微调过模型。",
        "expected_skills": ["Python", "PyTorch", "RAG", "向量索引"],
        "expected_gaps": ["语言模型微调"],
        "expected_match_level": {"overall": "中等", "ability": "中等", "experience": "中等", "risk": "需要优化"},
    },
    {
        "id": "ai_04", "category": "AI应用开发",
        "jd": "智能对话系统研发，要求掌握 prompt 设计、多轮对话、流式 SSE、工具调用，熟悉 FastAPI 与异步编程。",
        "resume": "FastAPI 与 asyncio 基础扎实，实现过多轮对话与流式输出，写过多版系统提示词，但缺少工具调用实战。",
        "expected_skills": ["FastAPI", "流式 SSE", "多轮对话", "prompt 设计", "异步编程"],
        "expected_gaps": ["工具调用"],
        "expected_match_level": {"overall": "较高", "ability": "较强", "experience": "中等", "risk": "需要优化"},
    },
    {
        "id": "ai_05", "category": "AI应用开发",
        "jd": "AI 平台研发，要求熟悉大模型评测、量化、推理加速，掌握 Docker 部署与性能调优。",
        "resume": "熟悉 Docker 与 CI/CD，做过接口性能压测，了解大模型推理概念，但缺少评测与量化经验。",
        "expected_skills": ["Docker", "性能调优"],
        "expected_gaps": ["大模型评测", "量化", "推理加速"],
        "expected_match_level": {"overall": "较低", "ability": "较弱", "experience": "中等", "risk": "需要优化"},
    },
    {
        "id": "ai_06", "category": "AI应用开发",
        "jd": "生成式 AI 应用开发，要求掌握 LLM 输出结构化解析、JSON Schema 约束、异常重试与降级策略。",
        "resume": "做过 LLM 结构化输出解析，处理过 JSON 代码块提取，实现了重试和兜底降级，对 JSON Schema 约束了解。",
        "expected_skills": ["结构化解析", "JSON Schema", "异常重试", "降级策略"],
        "expected_gaps": [],
        "expected_match_level": {"overall": "较高", "ability": "较强", "experience": "较强", "risk": "风险较低"},
    },

    # ---------------- Python开发 ----------------
    {
        "id": "py_01", "category": "Python开发",
        "jd": "Python 后端开发，要求熟练 Django/Flask、MySQL、Redis，熟悉 RESTful API 设计与异步任务队列。",
        "resume": "熟悉 Flask 与 Django，熟练 MySQL 和 Redis，做过 RESTful API，用过 Celery 异步任务。",
        "expected_skills": ["Django", "Flask", "MySQL", "Redis", "RESTful API", "异步任务队列"],
        "expected_gaps": [],
        "expected_match_level": {"overall": "较高", "ability": "较强", "experience": "较强", "risk": "风险较低"},
    },
    {
        "id": "py_02", "category": "Python开发",
        "jd": "Python 数据处理工程师，要求 Pandas、NumPy、SQL，熟悉数据清洗与 ETL 流程。",
        "resume": "熟练 Pandas 和 NumPy，写过 SQL，做过数据清洗，对 ETL 有基础了解。",
        "expected_skills": ["Pandas", "NumPy", "SQL", "数据清洗", "ETL"],
        "expected_gaps": [],
        "expected_match_level": {"overall": "较高", "ability": "较强", "experience": "较强", "risk": "风险较低"},
    },
    {
        "id": "py_03", "category": "Python开发",
        "jd": "Python 爬虫工程师，要求 Scrapy、反爬对抗、分布式采集、数据入库。",
        "resume": "用过 Scrapy 写爬虫，了解简单反爬，做过数据入库，缺少分布式采集经验。",
        "expected_skills": ["Scrapy", "反爬对抗", "数据入库"],
        "expected_gaps": ["分布式采集"],
        "expected_match_level": {"overall": "中等", "ability": "中等", "experience": "中等", "risk": "需要优化"},
    },
    {
        "id": "py_04", "category": "Python开发",
        "jd": "Python 自动化测试工程师，要求 pytest、接口自动化、CI 集成、性能测试。",
        "resume": "熟练 pytest 与接口自动化，接入过 CI，写过简单性能脚本。",
        "expected_skills": ["pytest", "接口自动化", "CI 集成", "性能测试"],
        "expected_gaps": [],
        "expected_match_level": {"overall": "较高", "ability": "较强", "experience": "较强", "risk": "风险较低"},
    },
    {
        "id": "py_05", "category": "Python开发",
        "jd": "Python 运维开发，要求 Linux、Shell、Python 脚本、监控告警、容器编排 K8s。",
        "resume": "熟悉 Linux 与 Shell，写 Python 运维脚本，做过监控告警，了解 Docker，缺少 K8s 实践。",
        "expected_skills": ["Linux", "Shell", "Python 脚本", "监控告警"],
        "expected_gaps": ["K8s"],
        "expected_match_level": {"overall": "中等", "ability": "中等", "experience": "中等", "risk": "需要优化"},
    },
    {
        "id": "py_06", "category": "Python开发",
        "jd": "Python Web 全栈，要求 FastAPI、SQLAlchemy、前端 Vue/React、消息队列。",
        "resume": "FastAPI 与 SQLAlchemy 熟练，前端用过 Vue，了解消息队列概念但未实战。",
        "expected_skills": ["FastAPI", "SQLAlchemy", "Vue"],
        "expected_gaps": ["消息队列"],
        "expected_match_level": {"overall": "较高", "ability": "较强", "experience": "中等", "risk": "需要优化"},
    },

    # ---------------- Java后端 ----------------
    {
        "id": "java_01", "category": "Java后端",
        "jd": "Java 后端开发，要求 Spring Boot、MyBatis、MySQL、Redis、微服务架构。",
        "resume": "熟练 Spring Boot 与 MyBatis，MySQL/Redis 基础扎实，参与过微服务拆分。",
        "expected_skills": ["Spring Boot", "MyBatis", "MySQL", "Redis", "微服务"],
        "expected_gaps": [],
        "expected_match_level": {"overall": "较高", "ability": "较强", "experience": "较强", "risk": "风险较低"},
    },
    {
        "id": "java_02", "category": "Java后端",
        "jd": "Java 高并发开发，要求多线程、JVM 调优、消息中间件 Kafka、缓存穿透解决方案。",
        "resume": "了解多线程与锁，用过 Kafka，做过缓存，但对 JVM 调优经验不足。",
        "expected_skills": ["多线程", "Kafka", "缓存"],
        "expected_gaps": ["JVM 调优", "缓存穿透解决方案"],
        "expected_match_level": {"overall": "中等", "ability": "中等", "experience": "中等", "risk": "需要优化"},
    },
    {
        "id": "java_03", "category": "Java后端",
        "jd": "Java 电商开发，要求分布式事务、秒杀系统、限流降级、ES 搜索。",
        "resume": "做过交易系统，了解分布式事务，实现过限流，用 ES 做过搜索，缺秒杀系统经验。",
        "expected_skills": ["分布式事务", "限流", "ES 搜索"],
        "expected_gaps": ["秒杀系统"],
        "expected_match_level": {"overall": "中等", "ability": "中等", "experience": "较强", "risk": "需要优化"},
    },
    {
        "id": "java_04", "category": "Java后端",
        "jd": "Java 金融后端，要求严谨的事务处理、对账、资金安全、消息可靠性保证。",
        "resume": "做过支付对账流程，理解事务与幂等，了解资金安全设计，经验尚浅。",
        "expected_skills": ["事务处理", "对账", "幂等"],
        "expected_gaps": ["资金安全", "消息可靠性"],
        "expected_match_level": {"overall": "较低", "ability": "较弱", "experience": "较低", "risk": "需要优化"},
    },
    {
        "id": "java_05", "category": "Java后端",
        "jd": "Java 中间件开发，要求 Netty、RPC 框架、注册中心、负载均衡。",
        "resume": "了解 Netty 与 RPC 原理，用过注册中心，缺少中间件开发实战。",
        "expected_skills": ["Netty", "RPC", "注册中心"],
        "expected_gaps": ["负载均衡", "中间件开发"],
        "expected_match_level": {"overall": "较低", "ability": "较弱", "experience": "较低", "risk": "需要优化"},
    },
    {
        "id": "java_06", "category": "Java后端",
        "jd": "Java 数据平台，要求 Hadoop、Spark、Hive、数据仓库建模。",
        "resume": "写过 Spark 批处理，了解 Hive 与数仓建模，缺 Hadoop 集群运维经验。",
        "expected_skills": ["Spark", "Hive", "数据仓库建模"],
        "expected_gaps": ["Hadoop"],
        "expected_match_level": {"overall": "中等", "ability": "中等", "experience": "中等", "risk": "需要优化"},
    },

    # ---------------- 普通后端 ----------------
    {
        "id": "be_01", "category": "普通后端",
        "jd": "后端开发，要求掌握任一主流语言、RESTful API、数据库设计、接口文档与单元测试。",
        "resume": "熟练 Go 开发，设计过 RESTful API 与数据库表，写过接口文档和单元测试。",
        "expected_skills": ["RESTful API", "数据库设计", "接口文档", "单元测试"],
        "expected_gaps": [],
        "expected_match_level": {"overall": "较高", "ability": "较强", "experience": "较强", "risk": "风险较低"},
    },
    {
        "id": "be_02", "category": "普通后端",
        "jd": "后端研发，要求掌握缓存、消息队列、数据库索引优化、接口性能优化。",
        "resume": "用过 Redis 缓存与消息队列，做过索引优化，接口性能调优经验一般。",
        "expected_skills": ["缓存", "消息队列", "数据库索引优化"],
        "expected_gaps": ["接口性能优化"],
        "expected_match_level": {"overall": "中等", "ability": "中等", "experience": "中等", "risk": "需要优化"},
    },
    {
        "id": "be_03", "category": "普通后端",
        "jd": "后端开发，要求熟练 Linux、Git、日志排查、错误处理与代码审查。",
        "resume": "熟悉 Linux 命令与 Git 工作流，会排查日志，经历过代码审查。",
        "expected_skills": ["Linux", "Git", "日志排查", "代码审查"],
        "expected_gaps": [],
        "expected_match_level": {"overall": "较高", "ability": "较强", "experience": "较强", "risk": "风险较低"},
    },
    {
        "id": "be_04", "category": "普通后端",
        "jd": "后端开发，要求微服务、容器化 Docker、配置中心、服务监控链路追踪。",
        "resume": "了解微服务与 Docker，用过配置中心，缺少链路追踪经验。",
        "expected_skills": ["微服务", "Docker", "配置中心"],
        "expected_gaps": ["链路追踪"],
        "expected_match_level": {"overall": "中等", "ability": "中等", "experience": "中等", "risk": "需要优化"},
    },
    {
        "id": "be_05", "category": "普通后端",
        "jd": "后端开发，要求接口鉴权、安全防护、防注入、日志审计。",
        "resume": "做过登录鉴权，了解常见 Web 安全，做过日志记录，缺安全审计系统经验。",
        "expected_skills": ["接口鉴权", "安全防护", "日志审计"],
        "expected_gaps": ["防注入"],
        "expected_match_level": {"overall": "中等", "ability": "中等", "experience": "中等", "risk": "需要优化"},
    },
    {
        "id": "be_06", "category": "普通后端",
        "jd": "后端开发，要求掌握 HTTP/TCP 协议、接口幂等、分布式锁、定时任务。",
        "resume": "理解 HTTP/TCP，实现过接口幂等与定时任务，了解分布式锁原理。",
        "expected_skills": ["HTTP/TCP", "接口幂等", "定时任务"],
        "expected_gaps": ["分布式锁"],
        "expected_match_level": {"overall": "较高", "ability": "较强", "experience": "中等", "risk": "需要优化"},
    },
]