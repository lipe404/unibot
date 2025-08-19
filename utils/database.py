import sqlite3
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path='data/unibot.db'):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()

    def init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Tabela para perguntas e respostas
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        question TEXT NOT NULL,
                        response TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Tabela para PDFs carregados
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS uploaded_pdfs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        filepath TEXT NOT NULL,
                        upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'active'
                    )
                ''')

                # Tabela para estatísticas
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_value INTEGER DEFAULT 0,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.commit()
                logger.info("Banco de dados inicializado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {str(e)}")

    def log_question(self, question):
        """Registra uma pergunta no banco"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO conversations (question) VALUES (?)",
                    (question,)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao registrar pergunta: {str(e)}")

    def log_response(self, question, response):
        """Atualiza a resposta para uma pergunta"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """UPDATE conversations
                       SET response = ?
                       WHERE question = ? AND response IS NULL
                       ORDER BY timestamp DESC LIMIT 1""",
                    (response, question)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao registrar resposta: {str(e)}")

    def log_pdf_upload(self, filename, filepath):
        """Registra um PDF carregado no banco"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO uploaded_pdfs (filename, filepath) VALUES (?, ?)",
                    (filename, filepath)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao registrar PDF: {str(e)}")

    def get_stats(self):
        """Obtém estatísticas do sistema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Total de perguntas
                cursor.execute(
                    "SELECT COUNT(*) FROM conversations WHERE response IS NOT NULL")
                total_questions = cursor.fetchone()[0]

                # Total de PDFs
                cursor.execute(
                    "SELECT COUNT(*) FROM uploaded_pdfs WHERE status = 'active'")
                total_pdfs = cursor.fetchone()[0]

                # Estimativa de chunks (assumindo média de 10 chunks por PDF)
                total_chunks = total_pdfs * 10

                return {
                    'total_questions': total_questions,
                    'total_pdfs': total_pdfs,
                    'total_chunks': total_chunks
                }

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return {
                'total_questions': 0,
                'total_pdfs': 0,
                'total_chunks': 0
            }

    def get_trained_documents(self):
        """Obtém lista de documentos treinados"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT filename, upload_date, status
                       FROM uploaded_pdfs
                       ORDER BY upload_date DESC"""
                )

                docs = []
                for row in cursor.fetchall():
                    docs.append({
                        'filename': row[0],
                        'upload_date': row[1],
                        'status': row[2]
                    })

                return docs

        except Exception as e:
            logger.error(f"Erro ao obter documentos: {str(e)}")
            return []
