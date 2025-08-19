from typing import List, Dict, Optional
from langchain_community.llms import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from .pdf_processor import PDFProcessor
import logging

logger = logging.getLogger(__name__)


class UnibotAI:
    def __init__(self, config):
        self.config = config
        self.pdf_processor = PDFProcessor(config)
        self.llm = None
        self.conversation_history = []
        self.load_model()

    def load_model(self):
        """Carrega o modelo de linguagem"""
        try:
            # Usando um modelo menor e mais simples para demonstração
            model_name = "gpt2"

            # Verificar se CUDA está disponível
            device = 0 if torch.cuda.is_available() else -1

            # Criar pipeline
            pipe = pipeline(
                "text-generation",
                model=model_name,
                tokenizer=model_name,
                max_length=256,
                temperature=0.7,
                do_sample=True,
                device=device,
                pad_token_id=50256  # Token de padding para GPT-2
            )

            self.llm = HuggingFacePipeline(pipeline=pipe)
            logger.info("Modelo de IA carregado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {str(e)}")
            # Fallback para respostas baseadas em regras
            self.llm = None

    def generate_response(self, user_question: str) -> str:
        """Gera resposta para a pergunta do usuário"""
        try:
            # Buscar documentos relevantes
            relevant_docs = self.pdf_processor.search_similar_documents(
                user_question, k=3
            )

            # Construir contexto
            context = self.build_context(relevant_docs)

            # Gerar resposta
            if self.llm and context:
                response = self.generate_ai_response(user_question, context)
            else:
                response = self.generate_fallback_response(
                    user_question, relevant_docs)

            # Adicionar à história da conversa
            self.add_to_history(user_question, response)

            return response

        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {str(e)}")
            return "Desculpe, ocorreu um erro ao processar sua pergunta. Tente novamente."

    def build_context(self, documents: List) -> str:
        """Constrói contexto a partir dos documentos relevantes"""
        if not documents:
            return ""

        context_parts = []
        for doc in documents:
            content = doc.page_content[:300]  # Limitar tamanho
            source = doc.metadata.get('source', 'Documento')
            context_parts.append(f"[{source}]: {content}")

        return "\n\n".join(context_parts)

    def generate_ai_response(self, question: str, context: str) -> str:
        """Gera resposta usando o modelo de IA"""
        try:
            prompt = f"Pergunta: {question}\nContexto: {context}\nResposta:"

            response = self.llm(prompt)
            return self.clean_response(response)

        except Exception as e:
            logger.error(f"Erro na geração AI: {str(e)}")
            return self.generate_fallback_response(question, [])

    def generate_fallback_response(self, question: str, documents: List) -> str:
        """Gera resposta de fallback baseada em regras"""
        question_lower = question.lower()

        # Respostas baseadas em palavras-chave
        if any(word in question_lower for word in ['horário', 'horarios', 'funcionamento']):
            return "Para informações sobre horários de funcionamento, consulte a documentação oficial ou entre em contato com nossa equipe."

        elif any(word in question_lower for word in ['curso', 'cursos', 'graduação']):
            return "Oferecemos diversos cursos de graduação e pós-graduação. Para informações detalhadas sobre nossos cursos, consulte nosso catálogo acadêmico."

        elif any(word in question_lower for word in ['matrícula', 'inscrição', 'inscrever']):
            return "Para informações sobre matrículas e inscrições, acesse nosso portal do aluno ou entre em contato com a secretaria acadêmica."

        elif any(word in question_lower for word in ['preço', 'valor', 'mensalidade', 'custo']):
            return "Para informações sobre valores e formas de pagamento, consulte nossa equipe comercial ou acesse nosso site oficial."

        # Se temos documentos relevantes, usar informações deles
        elif documents:
            content_preview = documents[0].page_content[:300]
            return f"Com base nas informações disponíveis: {content_preview}... Para mais detalhes, consulte a documentação completa."

        else:
            return "Obrigado pela sua pergunta. Para obter informações mais específicas, recomendo entrar em contato com nossa equipe de suporte ou consultar nossa documentação oficial."

    def clean_response(self, response: str) -> str:
        """Limpa e formata a resposta"""
        if isinstance(response, list):
            response = response[0] if response else ""

        # Remover prompt da resposta se presente
        if "Resposta:" in response:
            response = response.split("Resposta:")[-1].strip()

        # Limitar tamanho da resposta
        if len(response) > 500:
            response = response[:500] + "..."

        return response if response else "Não foi possível gerar uma resposta adequada."

    def add_to_history(self, question: str, response: str):
        """Adiciona interação ao histórico"""
        self.conversation_history.append({
            'question': question,
            'response': response,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        })

        # Manter apenas as últimas 10 interações
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

    def get_conversation_history(self) -> List[Dict]:
        """Retorna histórico da conversa"""
        return self.conversation_history

    def clear_history(self):
        """Limpa histórico da conversa"""
        self.conversation_history = []
