import PyPDF2
import os
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFProcessor:
    def __init__(self, config):
        self.config = config
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            length_function=len,
        )

        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=config.EMBEDDING_MODEL
            )
            logger.info("Embeddings carregados com sucesso")
        except Exception as e:
            logger.error(f"Erro ao carregar embeddings: {str(e)}")
            self.embeddings = None

        self.vectorstore = None
        self.load_vectorstore()

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrai texto de um arquivo PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""

                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"

                return text
        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF {pdf_path}: {str(e)}")
            return ""

    def process_pdf(self, pdf_path: str, filename: str) -> List[Document]:
        """Processa um PDF e retorna documentos chunked"""
        text = self.extract_text_from_pdf(pdf_path)

        if not text.strip():
            logger.warning(f"Nenhum texto extraído do arquivo {filename}")
            return []

        # Criar documento
        document = Document(
            page_content=text,
            metadata={
                "source": filename,
                "file_path": pdf_path
            }
        )

        # Dividir em chunks
        chunks = self.text_splitter.split_documents([document])

        logger.info(f"PDF {filename} processado: {len(chunks)} chunks criados")
        return chunks

    def load_vectorstore(self):
        """Carrega ou cria o vectorstore"""
        if self.embeddings is None:
            logger.error(
                "Embeddings não disponíveis - vectorstore não será carregado")
            return

        try:
            if os.path.exists(self.config.VECTORSTORE_PATH) and os.listdir(self.config.VECTORSTORE_PATH):
                self.vectorstore = Chroma(
                    persist_directory=self.config.VECTORSTORE_PATH,
                    embedding_function=self.embeddings
                )
                logger.info("Vectorstore carregado com sucesso")
            else:
                self.vectorstore = Chroma(
                    persist_directory=self.config.VECTORSTORE_PATH,
                    embedding_function=self.embeddings
                )
                logger.info("Novo vectorstore criado")
        except Exception as e:
            logger.error(f"Erro ao carregar vectorstore: {str(e)}")
            self.vectorstore = None

    def add_documents_to_vectorstore(self, documents: List[Document]):
        """Adiciona documentos ao vectorstore"""
        if not documents:
            logger.warning("Nenhum documento para adicionar")
            return False

        if self.vectorstore is None:
            logger.error("Vectorstore não disponível")
            return False

        try:
            self.vectorstore.add_documents(documents)
            self.vectorstore.persist()
            logger.info(
                f"{len(documents)} documentos adicionados ao vectorstore")
            return True
        except Exception as e:
            logger.error(
                f"Erro ao adicionar documentos ao vectorstore: {str(e)}")
            return False

    def search_similar_documents(self, query: str, k: int = 5) -> List[Document]:
        """Busca documentos similares à query"""
        if self.vectorstore is None:
            logger.warning("Vectorstore não disponível para busca")
            return []

        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            logger.info(
                f"Encontrados {len(docs)} documentos similares para a query")
            return docs
        except Exception as e:
            logger.error(f"Erro na busca de documentos: {str(e)}")
            return []

    def train_with_pdf(self, pdf_path: str, filename: str) -> bool:
        """Treina a IA com um novo PDF"""
        try:
            logger.info(f"Iniciando treinamento com PDF: {filename}")
            documents = self.process_pdf(pdf_path, filename)

            if documents:
                success = self.add_documents_to_vectorstore(documents)
                logger.info(
                    f"Treinamento concluído para {filename}: {'Sucesso' if success else 'Falhou'}")
                return success
            else:
                logger.warning(f"Nenhum documento processado para {filename}")
                return False

        except Exception as e:
            logger.error(f"Erro ao treinar com PDF {filename}: {str(e)}")
            return False
