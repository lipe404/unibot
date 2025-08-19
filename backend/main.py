from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from document_processor import process_document, query_ai_model
import os
import shutil

app = FastAPI()

# Permitir acesso do seu front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["../frontend/js/script.js"],  # ou especifique o domínio do seu front-end
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = process_document(file_path)
    return result

@app.post("/ask/")
async def ask_question(question: str = Form(...), filename: str = Form(...)):
    answer = query_ai_model(question, filename)
    return {"answer": answer}
