"""
Módulo para processamento de documentos
"""
import PyPDF2
from docx import Document
import os
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path):
    """Extrai texto de um arquivo PDF"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        logger.error(f"Erro ao extrair texto do PDF: {str(e)}")
        raise

def extract_text_from_docx(docx_path):
    """Extrai texto de um arquivo DOCX"""
    try:
        doc = Document(docx_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        logger.error(f"Erro ao extrair texto do DOCX: {str(e)}")
        raise

def extract_text_from_txt(txt_path):
    """Extrai texto de um arquivo TXT"""
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Erro ao ler arquivo TXT: {str(e)}")
        raise

def process_document(file_path):
    """
    Processa um documento baseado em sua extensão
    Retorna o texto extraído e informações sobre o processamento
    """
    try:
        logger.info(f"Iniciando processamento do arquivo: {file_path}")

        # Determinar o tipo de arquivo e extrair texto
        if file_path.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        elif file_path.lower().endswith('.docx'):
            text = extract_text_from_docx(file_path)
        elif file_path.lower().endswith('.txt'):
            text = extract_text_from_txt(file_path)
        else:
            raise ValueError("Tipo de arquivo não suportado")

        # Aqui você enviaria o texto para a API de IA para indexação/processamento
        # Por exemplo: indexar o documento no seu sistema de busca

        return {
            'file_name': os.path.basename(file_path),
            'text_length': len(text),
            'processed': True
        }

    except Exception as e:
        logger.error(f"Erro ao processar documento: {str(e)}")
        raise

def query_ai_model(query):
    """
    Função para consultar o modelo de IA com a pergunta do usuário
    (Implemente a integração com a API de IA escolhida aqui)
    """
    # Exemplo de implementação básica - substitua pela sua API real
    # Você pode usar OpenAI, HuggingFace, ou outra API de sua escolha

    # Implementação fictícia - substitua pela chamada real à API
    if "horário" in query.lower():
        return "O horário de funcionamento do Centro Universitário Única é de segunda a sexta, das 8h às 22h."
    elif "curso" in query.lower():
        return "Oferecemos diversos cursos nas áreas de tecnologia, negócios e saúde. Posso te indicar o site com a lista completa."
    else:
        return "Entendi sua pergunta sobre: " + query + ". Estou aprendendo a responder melhor cada dia!"