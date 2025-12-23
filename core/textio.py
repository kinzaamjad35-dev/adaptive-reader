"""Text input helpers: PDF, DOCX, TXT and OCR for photos."""
import io
import re


def clean_text(text: str) -> str:
    text = text.replace("\r", "")
    text = re.sub(r"-\n(\w)", r"\1", text)          # re-join hyphenated line breaks
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)     # single newlines -> spaces
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    return clean_text("\n\n".join((p.extract_text() or "") for p in reader.pages))


def extract_docx(data: bytes) -> str:
    import docx
    d = docx.Document(io.BytesIO(data))
    parts = [p.text for p in d.paragraphs if p.text.strip()]
    for t in d.tables:
        for row in t.rows:
            parts.append(" ".join(c.text for c in row.cells if c.text.strip()))
    return "\n\n".join(parts).strip()


def extract_txt(data: bytes) -> str:
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return clean_text(data.decode(enc))
        except UnicodeDecodeError:
            continue
    return ""


def extract_file(name: str, data: bytes) -> str:
    n = name.lower()
    if n.endswith(".pdf"):
        return extract_pdf(data)
    if n.endswith(".docx"):
        return extract_docx(data)
    if n.endswith((".txt", ".md")):
        return extract_txt(data)
    raise ValueError("Unsupported file type. Use PDF, DOCX or TXT.")


_ocr = None


def ocr_image(data: bytes, keep_lines: bool = False) -> str:
    """OCR with RapidOCR (ONNX, free, runs on Streamlit Cloud)."""
    global _ocr
    import numpy as np
    from PIL import Image, ImageOps
    if _ocr is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr = RapidOCR()
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    if max(img.size) > 2000:
        img.thumbnail((2000, 2000))
    result, _ = _ocr(np.array(img))
    if not result:
        return ""
    # sort boxes top-to-bottom, then left-to-right, group into lines
    boxes = sorted(result, key=lambda r: (r[0][0][1], r[0][0][0]))
    lines, cur, last_y = [], [], None
    for box, txt, _conf in boxes:
        y = box[0][1]
        h = abs(box[3][1] - box[0][1]) or 10
        if last_y is not None and abs(y - last_y) > h * 0.6:
            lines.append(" ".join(t for _, t in sorted(cur)))
            cur = []
        cur.append((box[0][0], txt))
        last_y = y
    if cur:
        lines.append(" ".join(t for _, t in sorted(cur)))
    return "\n".join(lines).strip() if keep_lines else clean_text("\n".join(lines))
