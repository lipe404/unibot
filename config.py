import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or 'dev-secret-key-change-in-production'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///unibot.db'
    UPLOAD_FOLDER = 'data/pdfs'
    VECTORSTORE_PATH = 'data/vectorstore'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # IA Configuration
    EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    # OpenAI API (opcional - para modelos mais avançados)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
