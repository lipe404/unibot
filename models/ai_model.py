from typing import List, Dict, Optional
from .pdf_processor import PDFProcessor
import logging
import re

logger = logging.getLogger(__name__)


class UnibotAI:
    def __init__(self, config):
        self.config = config
        self.pdf_processor = PDFProcessor(config)
        self.conversation_history = []
        logger.info("UnibotAI inicializado com sucesso")

    def generate_response(self, user_question: str) -> str:
        """Gera resposta para a pergunta do usuário"""
        try:
            logger.info(f"Processando pergunta: {user_question[:50]}...")

            # Buscar documentos relevantes
            relevant_docs = self.pdf_processor.search_similar_documents(
                user_question, k=3
            )

            logger.info(
                f"Encontrados {len(relevant_docs)} documentos relevantes")

            # Gerar resposta baseada no contexto
            if relevant_docs:
                response = self.generate_context_response(
                    user_question, relevant_docs)
            else:
                response = self.generate_fallback_response(user_question)

            # Adicionar à história da conversa
            self.add_to_history(user_question, response)

            logger.info(f"Resposta gerada com sucesso")
            return response

        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {str(e)}")
            return "Desculpe, ocorreu um erro ao processar sua pergunta. Tente novamente."

    def generate_context_response(self, question: str, documents: List) -> str:
        """Gera resposta baseada no contexto dos documentos"""
        try:
            # Combinar conteúdo dos documentos
            combined_content = ""
            sources = []

            for doc in documents:
                combined_content += doc.page_content + " "
                source = doc.metadata.get('source', 'Documento')
                if source not in sources:
                    sources.append(source)

            combined_content = combined_content.strip()
            question_lower = question.lower()

            # Análise inteligente baseada na pergunta
            if any(word in question_lower for word in ['modalidade', 'modalidades', 'tipos', 'formas']):
                return self.extract_modalidades_info(combined_content, sources)

            elif any(word in question_lower for word in ['curso', 'cursos', 'graduação', 'graduacao']):
                return self.extract_cursos_info(combined_content, sources)

            elif any(word in question_lower for word in ['preço', 'preco', 'valor', 'mensalidade', 'custo', 'pagamento']):
                return self.extract_precos_info(combined_content, sources)

            elif any(word in question_lower for word in ['horário', 'horario', 'funcionamento', 'atendimento']):
                return self.extract_horarios_info(combined_content, sources)

            elif any(word in question_lower for word in ['matrícula', 'matricula', 'inscrição', 'inscricao']):
                return self.extract_matricula_info(combined_content, sources)

            else:
                # Resposta genérica com contexto
                preview = combined_content[:400]
                sources_text = ", ".join(sources)
                return f"""Com base nas informações disponíveis nos documentos ({sources_text}):

{preview}...

Para informações mais detalhadas, recomendo consultar a documentação completa ou entrar em contato com nossa equipe."""

        except Exception as e:
            logger.error(f"Erro ao gerar resposta com contexto: {str(e)}")
            return self.generate_fallback_response(question)

    def extract_modalidades_info(self, content: str, sources: List[str]) -> str:
        """Extrai informações sobre modalidades"""
        modalidades = []
        content_lower = content.lower()

        if 'presencial' in content_lower:
            modalidades.append('• **Presencial**')
        if 'ead' in content_lower or 'distância' in content_lower or 'distancia' in content_lower:
            modalidades.append('• **EAD (Ensino a Distância)**')
        if 'semipresencial' in content_lower or 'híbrido' in content_lower or 'hibrido' in content_lower:
            modalidades.append('• **Semipresencial/Híbrido**')

        sources_text = ", ".join(sources)

        if modalidades:
            return f"""**Modalidades oferecidas** (conforme {sources_text}):

{chr(10).join(modalidades)}

Para mais informações sobre cada modalidade, consulte nossa documentação completa ou entre em contato conosco."""

        return f"Com base nos documentos disponíveis ({sources_text}), temos informações sobre modalidades de ensino. Para detalhes específicos, recomendo consultar nossa equipe acadêmica."

    def extract_cursos_info(self, content: str, sources: List[str]) -> str:
        """Extrai informações sobre cursos"""
        # Buscar menções de cursos
        cursos_patterns = [
            r'curso[s]?\s+de\s+([A-Za-z\s]+)',
            r'graduação\s+em\s+([A-Za-z\s]+)',
            r'bacharelado\s+em\s+([A-Za-z\s]+)',
            r'licenciatura\s+em\s+([A-Za-z\s]+)'
        ]

        cursos_encontrados = set()
        for pattern in cursos_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 3:  # Evitar matches muito curtos
                    cursos_encontrados.add(match.strip().title())

        sources_text = ", ".join(sources)

        if cursos_encontrados:
            cursos_list = list(cursos_encontrados)[:5]  # Limitar a 5
            cursos_text = '\n• '.join(cursos_list)
            return f"""**Cursos disponíveis** (fonte: {sources_text}):

• {cursos_text}

Para informações completas sobre grade curricular, duração e requisitos, consulte nosso catálogo acadêmico."""

        return f"""Oferecemos diversos cursos de graduação e pós-graduação conforme documentado em {sources_text}.

Para informações detalhadas sobre cursos específicos, entre em contato com nossa equipe acadêmica."""

    def extract_precos_info(self, content: str, sources: List[str]) -> str:
        """Extrai informações sobre preços"""
        sources_text = ", ".join(sources)

        # Buscar valores monetários
        price_patterns = [
            r'R\$\s*[\d.,]+',
            r'valor[es]?\s*[:.]?\s*R\$\s*[\d.,]+',
            r'mensalidade[s]?\s*[:.]?\s*R\$\s*[\d.,]+'
        ]

        precos_encontrados = set()
        for pattern in price_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            precos_encontrados.update(matches)

        if precos_encontrados:
            return f"""**Informações sobre valores** (fonte: {sources_text}):

Valores encontrados na documentação:
• {chr(10).join([f"• {preco}" for preco in list(precos_encontrados)[:3]])}

Para informações atualizadas sobre valores, formas de pagamento e possíveis descontos, entre em contato com nossa equipe comercial."""

        return f"""Para informações sobre valores e formas de pagamento (conforme {sources_text}):

• Entre em contato com nossa equipe comercial
• Consulte valores atualizados dos cursos
• Verifique formas de pagamento disponíveis
• Informe-se sobre possíveis descontos e bolsas"""

    def extract_horarios_info(self, content: str, sources: List[str]) -> str:
        """Extrai informações sobre horários"""
        return f"""**Informações sobre horários** (baseado em {', '.join(sources)}):

Para horários específicos de:
• Secretaria e atendimento
• Aulas e laboratórios
• Biblioteca e demais serviços

Recomendamos consultar nossa secretaria acadêmica ou verificar o portal do aluno."""

    def extract_matricula_info(self, content: str, sources: List[str]) -> str:
        """Extrai informações sobre matrícula"""
        return f"""**Processo de matrícula** (conforme {', '.join(sources)}):

Para realizar sua matrícula:
• Acesse nosso portal do aluno
• Consulte a secretaria acadêmica
• Verifique documentos necessários
• Confirme prazos e procedimentos

Nossa equipe acadêmica poderá orientá-lo sobre todo o processo."""

    def generate_fallback_response(self, question: str) -> str:
        """Gera resposta de fallback quando não há contexto"""
        question_lower = question.lower()

        if any(word in question_lower for word in ['horário', 'horarios', 'funcionamento']):
            return "Para informações sobre horários de funcionamento, consulte nossa secretaria acadêmica ou acesse nosso portal."

        elif any(word in question_lower for word in ['curso', 'cursos', 'graduação']):
            return "Oferecemos diversos cursos de graduação e pós-graduação. Para informações detalhadas, consulte nosso catálogo acadêmico."

        elif any(word in question_lower for word in ['matrícula', 'inscrição']):
            return "Para informações sobre matrículas e inscrições, acesse nosso portal do aluno ou consulte a secretaria acadêmica."

        elif any(word in question_lower for word in ['preço', 'valor', 'mensalidade']):
            return "Para informações sobre valores e formas de pagamento, entre em contato com nossa equipe comercial."

        else:
            return "Obrigado pela sua pergunta. Para informações específicas, recomendo entrar em contato com nossa equipe ou consultar nossa documentação."

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
        logger.info("Histórico de conversas limpo")
