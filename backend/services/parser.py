"""
parser.py - 简历文件解析（PDF / Word(docx)）
"""
import io


def parse_file(filename, content_bytes):
    """根据文件扩展名解析为文本。支持 .pdf 与 .docx。"""
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return _parse_pdf(content_bytes)
    if name.endswith(".docx"):
        return _parse_docx(content_bytes)
    if name.endswith(".doc"):
        raise ValueError("旧版 .doc 暂不支持，请上传 .docx 或 PDF 文件")
    raise ValueError("不支持的文件格式，请上传 PDF 或 Word(docx) 文件")


def _parse_pdf(content_bytes):
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(content_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


def _parse_docx(content_bytes):
    from docx import Document
    doc = Document(io.BytesIO(content_bytes))
    return "\n".join(p.text for p in doc.paragraphs).strip()