"""
rag_knowledge.py - 岗位知识库 Embedding 与向量检索模块
技术栈：sentence-transformers + FAISS + numpy
支持模块导入（供 Workflow 调用）与命令行两种方式。
"""
import os
import sys
import json
from pathlib import Path

import numpy as np

BACKEND_DIR = Path(__file__).resolve().parent.parent          # backend/
PROJECT_ROOT = BACKEND_DIR.parent                              # 项目根

KB_PATH = BACKEND_DIR / "rag" / "knowledge_base.json"
INDEX_DIR = BACKEND_DIR / "rag" / "vector_index"
INDEX_PATH = INDEX_DIR / "index.faiss"
META_PATH = INDEX_DIR / "meta.json"

# ModelScope 中文语义模型（小模型，约60MB，512维）
MODEL_SCOPE_ID = "iic/nlp_gte_sentence-embedding_chinese-small"
# 复用项目根目录下的模型缓存，避免重复下载
os.environ.setdefault("MODELSCOPE_HOME", str(PROJECT_ROOT / ".modelscope"))
os.environ.setdefault("MODELSCOPE_CACHE", str(PROJECT_ROOT / ".modelscope" / "cache"))

DEFAULT_TOP_K = 3
# 相似度阈值：低于该值的召回不注入，避免噪声知识污染 Prompt。
# 依据：域内JD top-3 最低分 0.8835，域外查询最高分 0.869（gte chinese-small 余弦相似度）。
# 可用环境变量 RAG_MIN_SCORE 覆盖。
DEFAULT_MIN_SCORE = 0.875
_model = None


def get_min_score():
    """读取相似度阈值（环境变量 RAG_MIN_SCORE 可覆盖默认值）。"""
    try:
        v = float(os.getenv("RAG_MIN_SCORE", str(DEFAULT_MIN_SCORE)))
        return max(0.0, min(1.0, v))
    except (TypeError, ValueError):
        return DEFAULT_MIN_SCORE


def _cached_model_dir():
    root = os.environ.get("MODELSCOPE_HOME", str(PROJECT_ROOT / ".modelscope"))
    dirname = MODEL_SCOPE_ID.replace("/", "--")
    return os.path.join(root, "cache", "models", dirname, "snapshots", "master")


def resolve_model_path():
    cached = _cached_model_dir()
    if os.path.isdir(cached) and os.path.exists(os.path.join(cached, "config.json")):
        return cached
    from modelscope import snapshot_download
    return snapshot_download(MODEL_SCOPE_ID)


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(resolve_model_path())
    return _model


def load_docs():
    if not KB_PATH.exists():
        raise FileNotFoundError("知识库文件不存在: {}".format(KB_PATH))
    with open(KB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    docs = data.get("documents", [])
    if not docs:
        raise ValueError("知识库内容为空")
    return docs


def build_index():
    import faiss
    docs = load_docs()
    model = get_model()
    texts = [d["content"] for d in docs]
    vectors = model.encode(texts, show_progress_bar=False).astype("float32")
    faiss.normalize_L2(vectors)

    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    _write_index(index, INDEX_PATH)
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False)
    return len(docs)


def _write_index(index, path):
    import faiss
    data = faiss.serialize_index(index)
    with open(str(path), "wb") as f:
        f.write(bytes(data))


def _read_index(path):
    import faiss
    with open(str(path), "rb") as f:
        data = f.read()
    return faiss.deserialize_index(np.frombuffer(data, dtype=np.uint8))


def _load_index_and_docs():
    if not (INDEX_PATH.exists() and META_PATH.exists()):
        build_index()
    index = _read_index(INDEX_PATH)
    with open(META_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)
    return index, docs


def search(query, top_k=DEFAULT_TOP_K, min_score=None):
    import faiss
    if not query or not query.strip():
        return []
    top_k = max(1, int(top_k))
    if min_score is None:
        min_score = get_min_score()
    index, docs = _load_index_and_docs()
    top_k = min(top_k, len(docs))

    model = get_model()
    qv = model.encode([query]).astype("float32")
    faiss.normalize_L2(qv)

    scores, idxs = index.search(qv, top_k)
    results = []
    for i in range(len(idxs[0])):
        j = int(idxs[0][i])
        d = docs[j]
        results.append({
            "id": d.get("id", ""),
            "category": d.get("category", ""),
            "content": d.get("content", ""),
            "keywords": d.get("keywords", []),
            "score": round(float(scores[0][i]), 4),
        })

    # 相似度阈值过滤：低于阈值的不注入（打印阈值判定过程，便于观测）
    passed = [r for r in results if r["score"] >= min_score]
    print(f"[RAG] 检索: query={query[:30]}... top_k={top_k} 阈值={min_score}")
    for r in results:
        flag = "通过" if r["score"] >= min_score else "低于阈值(不注入)"
        print(f"[RAG]   [{r['id']}] score={r['score']} {flag}")
    print(f"[RAG] 最终注入 {len(passed)}/{len(results)} 条: "
          + (", ".join(r["id"] for r in passed) if passed else "无"))
    return passed


def search_knowledge(query, top_k=DEFAULT_TOP_K, min_score=None):
    """供 Workflow 调用的友好封装：失败时返回空列表，不抛出异常"""
    try:
        return search(query, top_k, min_score=min_score)
    except Exception as e:
        print("[RAG] 检索失败:", e)
        return []


if __name__ == "__main__":
    args = sys.argv[1:]
    try:
        if len(args) >= 2 and args[0] == "search":
            query = " ".join(args[1:])
            print(json.dumps(search(query), ensure_ascii=False))
        else:
            count = build_index()
            print(json.dumps({"ok": True, "indexed": count}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)