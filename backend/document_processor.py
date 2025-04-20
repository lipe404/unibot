"""
Módulo para processamento de documentos e interação com modelo de IA
"""
import os
import logging
import PyPDF2
from docx import Document
import openai
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente e define a chave da API
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Cache de textos extraídos
document_text_cache = {}

def extract_text_from_pdf(pdf_path):
    """Extrai texto de um arquivo PDF"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            return text.strip()
    except Exception as e:
        logger.error(f"Erro ao extrair texto do PDF: {str(e)}")
        raise

def extract_text_from_docx(docx_path):
    """Extrai texto de um arquivo DOCX"""
    try:
        doc = Document(docx_path)
        return "\n".join([para.text for para in doc.paragraphs if para.text]).strip()
    except Exception as e:
        logger.error(f"Erro ao extrair texto do DOCX: {str(e)}")
        raise

def extract_text_from_txt(txt_path):
    """Extrai texto de um arquivo TXT"""
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except Exception as e:
        logger.error(f"Erro ao ler arquivo TXT: {str(e)}")
        raise

def process_document(file_path):
    """
    Processa um documento baseado em sua extensão
    Retorna um dicionário com informações do arquivo processado
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError("Arquivo não encontrado")

        logger.info(f"Iniciando processamento do arquivo: {file_path}")

        if file_path.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        elif file_path.lower().endswith('.docx'):
            text = extract_text_from_docx(file_path)
        elif file_path.lower().endswith('.txt'):
            text = extract_text_from_txt(file_path)
        else:
            raise ValueError("Tipo de arquivo não suportado")

        filename = os.path.basename(file_path)
        document_text_cache[filename] = text

        return {
            'file_name': filename,
            'text_length': len(text),
            'processed': True
        }

    except Exception as e:
        logger.error(f"Erro ao processar documento: {str(e)}")
        return {
            'file_name': os.path.basename(file_path),
            'text_length': 0,
            'processed': False,
            'error': str(e)
        }

def query_ai_model(query, filename=None):
    """
    Consulta o modelo de IA com a pergunta do usuário e contexto (se disponível)
    """
    try:
        context = document_text_cache.get(filename, "") if filename else ""
        full_prompt = f"Contexto:\n{context}\n\nPergunta: {query}" if context else query

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é o UniBot, assistente virtual do Centro Universitário Única. Responda de forma educada e útil."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message['content'].strip()

    except Exception as e:
        logger.error(f"Erro ao consultar OpenAI: {str(e)}")
        return "Desculpe, estou tendo dificuldades para processar sua pergunta no momento."
