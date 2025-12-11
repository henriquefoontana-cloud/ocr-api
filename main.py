from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from PIL import Image
import pytesseract
import tempfile
import shutil
from pdf2image import convert_from_path
import os

app = FastAPI(
    title="OCR API",
    description="API simples para extrair texto de imagens e PDFs usando Tesseract",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


def ocr_image(path: str) -> str:
    image = Image.open(path)
    text = pytesseract.image_to_string(image, lang="por+eng")
    return text


def ocr_pdf(path: str) -> str:
    pages = convert_from_path(path)
    texts: List[str] = []
    for page in pages:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
            page.save(tmp_img.name, "PNG")
            texts.append(ocr_image(tmp_img.name))
            os.unlink(tmp_img.name)
    return "\n\n".join(texts)


@app.post("/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado.")

    content_type = file.content_type or ""

    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_path = os.path.join(tmp_dir, file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            if content_type.startswith("image/"):
                text = ocr_image(temp_path)
            elif content_type == "application/pdf":
                text = ocr_pdf(temp_path)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tipo de arquivo não suportado: {content_type}. Envie imagem ou PDF.",
                )
        finally:
            file.file.close()

    return JSONResponse({"text": text})
