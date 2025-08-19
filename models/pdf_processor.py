import PyPDF2
import os
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError

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

        self.embeddings = None
        self.vectorstore = None
        self._init_embeddings()

    def _init_embeddings(self):
        """Inicializa embeddings com timeout"""
        try:
            logger.info("Carregando embeddings...")
            # Usar um modelo mais leve e rápido
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={
                    'device': 'cpu',
                    'trust_remote_code': False
                },
                encode_kwargs={
                    'normalize_embeddings': True,
                    'batch_size': 16  # Processar em lotes menores
                }
            )
            logger.info("Embeddings carregados com sucesso")
            self.load_vectorstore()
        except Exception as e:
            logger.error(f"Erro ao carregar embeddings: {str(e)}")
            self.embeddings = None

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrai texto de um arquivo PDF"""
        try:
            logger.info(f"Extraindo texto de: {pdf_path}")
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""

                total_pages = len(pdf_reader.pages)
                logger.info(f"PDF tem {total_pages} páginas")

                for page_num in range(total_pages):
                    try:
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"

                        # Log de progresso a cada 10 páginas
                        if (page_num + 1) % 10 == 0:
                            logger.info(
                                f"Processadas {page_num + 1}/{total_pages} páginas")

                    except Exception as e:
                        logger.warning(f"Erro na página {page_num}: {str(e)}")
                        continue

                logger.info(f"Texto extraído: {len(text)} caracteres")
                return text

        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF {pdf_path}: {str(e)}")
            return ""

    def process_pdf(self, pdf_path: str, filename: str) -> List[Document]:
        """Processa um PDF e retorna documentos chunked"""
        try:
            logger.info(f"Processando PDF: {filename}")
            text = self.extract_text_from_pdf(pdf_path)

            if not text.strip():
                logger.warning(f"Nenhum texto extraído do arquivo {filename}")
                return []

            # Limitar tamanho do texto se muito grande
            if len(text) > 500000:  # 500KB de texto
                logger.warning(
                    f"Texto muito grande ({len(text)} chars), truncando...")
                text = text[:500000]

            # Criar documento
            document = Document(
                page_content=text,
                metadata={
                    "source": filename,
                    "file_path": pdf_path,
                    "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            )

            # Dividir em chunks
            logger.info("Dividindo em chunks...")
            chunks = self.text_splitter.split_documents([document])

            # Limitar número de chunks se muito grande
            if len(chunks) > 200:
                logger.warning(
                    f"Muitos chunks ({len(chunks)}), limitando a 200")
                chunks = chunks[:200]

            logger.info(
                f"PDF {filename} processado: {len(chunks)} chunks criados")
            return chunks

        except Exception as e:
            logger.error(f"Erro ao processar PDF {filename}: {str(e)}")
            return []

    def load_vectorstore(self):
        """Carrega ou cria o vectorstore"""
        if self.embeddings is None:
            logger.error(
                "Embeddings não disponíveis - vectorstore não será carregado")
            return

        try:
            logger.info("Carregando vectorstore...")

            # Criar diretório se não existir
            os.makedirs(self.config.VECTORSTORE_PATH, exist_ok=True)

            self.vectorstore = Chroma(
                persist_directory=self.config.VECTORSTORE_PATH,
                embedding_function=self.embeddings,
                collection_name="unibot_docs"
            )

            # Verificar se tem documentos
            try:
                collection = self.vectorstore._collection
                count = collection.count()
                logger.info(f"Vectorstore carregado com {count} documentos")
            except:
                logger.info("Vectorstore vazio ou novo")

        except Exception as e:
            logger.error(f"Erro ao carregar vectorstore: {str(e)}")
            self.vectorstore = None

    def add_documents_to_vectorstore(self, documents: List[Document]) -> bool:
        """Adiciona documentos ao vectorstore com timeout"""
        if not documents:
            logger.warning("Nenhum documento para adicionar")
            return False

        if self.vectorstore is None or self.embeddings is None:
            logger.error("Vectorstore ou embeddings não disponíveis")
            return False

        try:
            logger.info(
                f"Adicionando {len(documents)} documentos ao vectorstore...")

            # Processar em lotes menores para evitar timeout
            batch_size = 10
            total_batches = (len(documents) + batch_size - 1) // batch_size

            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                batch_num = (i // batch_size) + 1

                logger.info(
                    f"Processando lote {batch_num}/{total_batches} ({len(batch)} documentos)")

                try:
                    # Usar timeout para cada lote
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(
                            self.vectorstore.add_documents, batch)
                        future.result(timeout=60)  # 60 segundos por lote

                    logger.info(f"Lote {batch_num} processado com sucesso")

                except TimeoutError:
                    logger.error(f"Timeout no lote {batch_num}")
                    return False
                except Exception as e:
                    logger.error(f"Erro no lote {batch_num}: {str(e)}")
                    return False

            # Persistir mudanças
            logger.info("Persistindo vectorstore...")
            self.vectorstore.persist()

            logger.info(
                f"Todos os {len(documents)} documentos foram adicionados com sucesso")
            return True

        except Exception as e:
            logger.error(
                f"Erro ao adicionar documentos ao vectorstore: {str(e)}")
            return False

    def search_similar_documents(self, query: str, k: int = 3) -> List[Document]:
        """Busca documentos similares à query"""
        if self.vectorstore is None:
            logger.warning("Vectorstore não disponível para busca")
            return []

        if not query.strip():
            logger.warning("Query vazia")
            return []

        try:
            logger.info(f"Buscando documentos para: '{query[:50]}...'")

            # Usar timeout para busca
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    self.vectorstore.similarity_search, query, k)
                docs = future.result(timeout=30)  # 30 segundos para busca

            logger.info(f"Encontrados {len(docs)} documentos similares")
            return docs

        except TimeoutError:
            logger.error("Timeout na busca de documentos")
            return []
        except Exception as e:
            logger.error(f"Erro na busca de documentos: {str(e)}")
            return []

    def train_with_pdf(self, pdf_path: str, filename: str) -> bool:
        """Treina a IA com um novo PDF"""
        try:
            logger.info(f"=== INICIANDO TREINAMENTO: {filename} ===")
            start_time = time.time()

            # Verificar se arquivo existe
            if not os.path.exists(pdf_path):
                logger.error(f"Arquivo não encontrado: {pdf_path}")
                return False

            # Verificar tamanho do arquivo
            file_size = os.path.getsize(pdf_path)
            logger.info(
                f"Tamanho do arquivo: {file_size / 1024 / 1024:.2f} MB")

            if file_size > 50 * 1024 * 1024:  # 50MB
                logger.warning("Arquivo muito grande, pode causar problemas")

            # Processar PDF
            documents = self.process_pdf(pdf_path, filename)

            if not documents:
                logger.error(f"Nenhum documento processado para {filename}")
                return False

            # Adicionar ao vectorstore
            success = self.add_documents_to_vectorstore(documents)

            end_time = time.time()
            duration = end_time - start_time

            logger.info(f"=== TREINAMENTO CONCLUÍDO: {filename} ===")
            logger.info(f"Tempo total: {duration:.2f} segundos")
            logger.info(f"Sucesso: {success}")

            return success

        except Exception as e:
            logger.error(
                f"Erro crítico no treinamento de {filename}: {str(e)}")
            return False
