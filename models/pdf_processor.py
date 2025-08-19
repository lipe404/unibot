import PyPDF2
import os
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
import logging
import chromadb

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

        # Inicializar embeddings
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=config.EMBEDDING_MODEL,
                # Forçar CPU para evitar problemas
                model_kwargs={'device': 'cpu'}
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
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

                return text.strip()
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
                "file_path": pdf_path,
                "type": "pdf"
            }
        )

        # Dividir em chunks
        chunks = self.text_splitter.split_documents([document])

        # Adicionar metadados específicos a cada chunk
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "chunk_id": i,
                "total_chunks": len(chunks),
                "source": filename
            })

        logger.info(f"PDF {filename} processado: {len(chunks)} chunks criados")
        return chunks

    def load_vectorstore(self):
        """Carrega ou cria o vectorstore"""
        if self.embeddings is None:
            logger.error(
                "Embeddings não disponíveis - vectorstore não pode ser carregado")
            return

        try:
            # Criar diretório se não existir
            os.makedirs(self.config.VECTORSTORE_PATH, exist_ok=True)

            # Tentar carregar vectorstore existente
            self.vectorstore = Chroma(
                persist_directory=self.config.VECTORSTORE_PATH,
                embedding_function=self.embeddings,
                collection_name="unibot_documents"
            )

            # Verificar se tem documentos
            try:
                collection = self.vectorstore._collection
                count = collection.count()
                logger.info(f"Vectorstore carregado com {count} documentos")
            except:
                logger.info("Novo vectorstore criado")

        except Exception as e:
            logger.error(f"Erro ao carregar vectorstore: {str(e)}")
            try:
                # Tentar criar um novo vectorstore
                self.vectorstore = Chroma(
                    persist_directory=self.config.VECTORSTORE_PATH,
                    embedding_function=self.embeddings,
                    collection_name="unibot_documents"
                )
                logger.info("Novo vectorstore criado após erro")
            except Exception as e2:
                logger.error(f"Erro ao criar novo vectorstore: {str(e2)}")
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
            # Filtrar documentos vazios
            valid_docs = [doc for doc in documents if doc.page_content.strip()]

            if not valid_docs:
                logger.warning("Nenhum documento válido para adicionar")
                return False

            # Adicionar documentos
            self.vectorstore.add_documents(valid_docs)

            # Persistir mudanças
            self.vectorstore.persist()

            logger.info(
                f"{len(valid_docs)} documentos adicionados ao vectorstore")
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

        if not query.strip():
            logger.warning("Query vazia para busca")
            return []

        try:
            # Realizar busca por similaridade
            docs = self.vectorstore.similarity_search(
                query,
                k=k,
                filter=None  # Pode adicionar filtros se necessário
            )

            logger.info(
                f"Busca por '{query[:50]}...' retornou {len(docs)} documentos")

            # Log dos documentos encontrados para debug
            for i, doc in enumerate(docs):
                source = doc.metadata.get('source', 'Desconhecido')
                preview = doc.page_content[:100].replace('\n', ' ')
                logger.debug(f"Doc {i+1}: {source} - {preview}...")

            return docs

        except Exception as e:
            logger.error(f"Erro na busca de documentos: {str(e)}")
            return []

    def train_with_pdf(self, pdf_path: str, filename: str) -> bool:
        """Treina a IA com um novo PDF"""
        try:
            logger.info(f"Iniciando treinamento com PDF: {filename}")

            # Processar PDF
            documents = self.process_pdf(pdf_path, filename)

            if not documents:
                logger.warning(f"Nenhum documento processado para {filename}")
                return False

            # Adicionar ao vectorstore
            success = self.add_documents_to_vectorstore(documents)

            if success:
                logger.info(
                    f"Treinamento concluído com sucesso para {filename}")
            else:
                logger.error(f"Falha no treinamento para {filename}")

            return success

        except Exception as e:
            logger.error(f"Erro ao treinar com PDF {filename}: {str(e)}")
            return False

    def get_vectorstore_stats(self):
        """Obtém estatísticas do vectorstore"""
        if self.vectorstore is None:
            return {"total_documents": 0, "collections": 0}

        try:
            collection = self.vectorstore._collection
            count = collection.count()
            return {
                "total_documents": count,
                "collections": 1
            }
        except Exception as e:
            logger.error(
                f"Erro ao obter estatísticas do vectorstore: {str(e)}")
            return {"total_documents": 0, "collections": 0}
