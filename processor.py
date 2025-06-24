import os
import json
import requests
import pytesseract
from io import BytesIO
from PIL import Image
from pdf2image import convert_from_path
from langdetect import detect
from dotenv import load_dotenv

# ─── Load secrets ───────────────────────────────────────────────
load_dotenv()
DS_KEY = os.getenv("DEEPSEEK_API_KEY")
OR_KEY = os.getenv("OPENROUTER_API_KEY")

HEADERS_DS = {"Authorization": f"Bearer {DS_KEY}"}
HEADERS_OR = {"Authorization": f"Bearer {OR_KEY}"}

# ─── Helpers: PDF → Image and OCR ───────────────────────────────
def pdf_to_img(path):
    return convert_from_path(path)[0]

def ocr_deepseek_raw(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    resp = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers=HEADERS_DS,
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Extract all text from the image."},
                {"role": "user", "content": "<image>", "image": buf.getvalue()}
            ]
        },
        timeout=60
    )
    return resp.json()["choices"][0]["message"]["content"]

def ocr_puterjs_raw(img: Image.Image) -> str:
    from base64 import b64encode
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = b64encode(buf.getvalue()).decode()
    resp = requests.post(
        "https://api.puter.ai/img2txt",
        json={"image": b64},
        timeout=60
    )
    return resp.json().get("text", "")

def ocr_pytesseract_raw(img: Image.Image) -> str:
    return pytesseract.image_to_string(img, lang="eng+fra+deu+ara+spa+ita+por+rus+chi_sim+jpn+kor", config="--psm 6 --oem 3")

def fallback_full_ocr(img: Image.Image) -> str:
    """
    Try DeepSeek OCR → Tesseract → Puter.js until we get >20 chars.
    """
    for fn in (ocr_deepseek_raw, ocr_pytesseract_raw, ocr_puterjs_raw):
        try:
            txt = fn(img)
            if txt and len(txt) > 20:
                return txt
        except:
            continue
    return ""

# ─── AI Extraction: DeepSeek & OpenRouter ──────────────────────
def ask_deepseek_json(text: str) -> str:
    prompt = (
        "You are a god-like extra good document analysis assistant. "
        "Given the full invoice text below, identify and extract all relevant fields  "
        "(such as invoice number, dates, totals, parties, payment details, line items, taxes, etc.) "
        "and return a single JSON object with key:value pairs for each field you find.\n\n"
        f"{text}"
    )
    resp = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers=HEADERS_DS,
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=60
    )
    return resp.json()["choices"][0]["message"]["content"]

def ask_openrouter_json(text: str) -> str:
    prompt = (
        "You are a very smart invoice parser. Analyze the following invoice text and automatically "
        "extract every meaningful field you can find—no predefined list required. "
        "Return your output as a single JSON object (key:value pairs).\n\n"
        f"{text}"
    )
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=HEADERS_OR,
        json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=60
    )
    return resp.json()["choices"][0]["message"]["content"]

def analyze_text(text: str) -> dict:
    """
    Try DeepSeek JSON extraction first, then OpenRouter.
    If both fail to produce valid JSON, return a minimal fallback.
    """
    for fn in (ask_deepseek_json, ask_openrouter_json):
        try:
            raw = fn(text)
            data = json.loads(raw)
            return data
        except:
            continue
    # Final fallback
    return {"raw_text": text[:2000], "note": "analysis failed"}

# ─── Main Entry ─────────────────────────────────────────────────
def process_invoice(path: str):
    """
    1. Load PDF or image
    2. OCR → raw_text
    3. detect language
    4. analyze_text → structured JSON
    5. convert to list of rows
    """
    ext = os.path.splitext(path)[1].lower()
    img = pdf_to_img(path) if ext == ".pdf" else Image.open(path).convert("RGB")

    raw_text = fallback_full_ocr(img)
    lang = detect(raw_text) if raw_text else "unknown"
    structured = analyze_text(raw_text)

    # Always include detected language
    structured.setdefault("language", lang)

    # Build rows: field/value/confidence
    rows = [{"field": k, "value": v, "confidence": "ai"} for k, v in structured.items()]
    return img, rows
