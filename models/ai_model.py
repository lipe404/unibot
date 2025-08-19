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
            # Usar modelo mais simples para demonstração
            model_name = "gpt2"

            # Verificar se CUDA está disponível
            device = 0 if torch.cuda.is_available() else -1

            # Criar pipeline com configurações mais conservadoras
            pipe = pipeline(
                "text-generation",
                model=model_name,
                tokenizer=model_name,
                max_length=200,  # Reduzido para evitar problemas
                temperature=0.7,
                do_sample=True,
                device=device,
                pad_token_id=50256,
                truncation=True
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
            logger.info(f"Processando pergunta: {user_question[:100]}...")

            # Buscar documentos relevantes
            relevant_docs = self.pdf_processor.search_similar_documents(
                user_question, k=3
            )

            logger.info(
                f"Encontrados {len(relevant_docs)} documentos relevantes")

            # Construir contexto
            context = self.build_context(relevant_docs)

            # Gerar resposta baseada no contexto
            if relevant_docs and context:
                response = self.generate_context_response(
                    user_question, context, relevant_docs)
            else:
                response = self.generate_fallback_response(
                    user_question, relevant_docs)

            # Adicionar à história da conversa
            self.add_to_history(user_question, response)

            logger.info(f"Resposta gerada: {response[:100]}...")
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
            # Aumentar limite para mais contexto
            content = doc.page_content[:400]
            source = doc.metadata.get('source', 'Documento')
            context_parts.append(f"[{source}]: {content}")

        context = "\n\n".join(context_parts)
        logger.debug(f"Contexto construído: {len(context)} caracteres")
        return context

    def generate_context_response(self, question: str, context: str, documents: List) -> str:
        """Gera resposta baseada no contexto dos documentos"""
        try:
            # Tentar usar o modelo de IA se disponível
            if self.llm:
                return self.generate_ai_response(question, context)
            else:
                # Usar resposta baseada em contexto sem IA
                return self.generate_smart_fallback_response(question, documents)

        except Exception as e:
            logger.error(f"Erro na geração com contexto: {str(e)}")
            return self.generate_smart_fallback_response(question, documents)

    def generate_ai_response(self, question: str, context: str) -> str:
        """Gera resposta usando o modelo de IA"""
        try:
            # Criar prompt mais estruturado
            prompt = f"""Com base no contexto fornecido, responda à pergunta de forma clara e objetiva.

Contexto:
{context[:800]}

Pergunta: {question}

Resposta:"""

            response = self.llm(prompt)
            cleaned_response = self.clean_response(response)

            # Se a resposta estiver muito curta ou não fizer sentido, usar fallback
            if len(cleaned_response) < 20 or not cleaned_response.strip():
                raise Exception("Resposta muito curta ou vazia")

            return cleaned_response

        except Exception as e:
            logger.error(f"Erro na geração AI: {str(e)}")
            return self.generate_smart_fallback_response(question, [])

    def generate_smart_fallback_response(self, question: str, documents: List) -> str:
        """Gera resposta inteligente baseada no contexto dos documentos"""
        question_lower = question.lower()

        # Se temos documentos relevantes, extrair informações específicas
        if documents:
            # Combinar conteúdo dos documentos
            combined_content = ""
            sources = []

            for doc in documents:
                combined_content += doc.page_content + " "
                source = doc.metadata.get('source', 'Documento')
                if source not in sources:
                    sources.append(source)

            combined_content = combined_content.strip()

            # Buscar informações específicas baseadas na pergunta
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
                preview = combined_content[:500]
                sources_text = ", ".join(sources)
                return f"""Com base nas informações disponíveis nos documentos ({sources_text}):

{preview}...

Para informações mais detalhadas, recomendo consultar a documentação completa ou entrar em contato com nossa equipe."""

        # Fallback para respostas sem contexto
        return self.generate_fallback_response(question, documents)

    def extract_modalidades_info(self, content: str, sources: List[str]) -> str:
        """Extrai informações sobre modalidades"""
        modalidades = []
        content_lower = content.lower()

        if 'presencial' in content_lower:
            modalidades.append('Presencial')
        if 'ead' in content_lower or 'distância' in content_lower or 'distancia' in content_lower:
            modalidades.append('EAD (Ensino a Distância)')
        if 'semipresencial' in content_lower or 'híbrido' in content_lower or 'hibrido' in content_lower:
            modalidades.append('Semipresencial/Híbrido')

        if modalidades:
            sources_text = ", ".join(sources)
            return f"""**Modalidades oferecidas** (conforme documentos: {sources_text}):

• {chr(10).join([f"**{mod}**" for mod in modalidades])}

{content[:300]}...

Para mais informações sobre cada modalidade, consulte nossa documentação completa."""

        return f"Com base nos documentos disponíveis ({', '.join(sources)}), encontrei informações sobre modalidades de ensino. Para detalhes específicos, recomendo consultar nossa equipe acadêmica."

    def extract_cursos_info(self, content: str, sources: List[str]) -> str:
        """Extrai informações sobre cursos"""
        # Buscar menções de cursos no texto
        cursos_encontrados = []
        content_lines = content.split('\n')

        for line in content_lines:
            if any(word in line.lower() for word in ['curso', 'graduação', 'bacharelado', 'licenciatura']):
                if len(line.strip()) < 200:  # Evitar linhas muito longas
                    cursos_encontrados.append(line.strip())

        sources_text = ", ".join(sources)

        if cursos_encontrados:
            cursos_text = '\n• '.join(
                cursos_encontrados[:5])  # Limitar a 5 cursos
            return f"""**Informações sobre nossos cursos** (fonte: {sources_text}):

• {cursos_text}

Para informações completas sobre grade curricular, duração e requisitos, consulte nosso catálogo acadêmico ou entre em contato conosco."""

        return f"""Com base nos documentos disponíveis ({sources_text}), oferecemos diversos cursos de graduação e pós-graduação. 

{content[:400]}...

Para informações detalhadas sobre cursos específicos, recomendo consultar nossa equipe acadêmica."""

    def extract_precos_info(self, content: str, sources: List[str]) -> str:
        """Extrai informações sobre preços"""
        sources_text = ", ".join(sources)

        # Buscar informações de preços no conteúdo
        price_info = []
        content_lines = content.split('\n')

        for line in content_lines:
            if any(word in line.lower() for word in ['r$', 'real', 'reais', 'valor', 'mensalidade', 'preço', 'custo']):
                if len(line.strip()) < 150:
                    price_info.append(line.strip())

        if price_info:
            prices_text = '\n• '.join(price_info[:3])
            return f"""**Informações sobre valores** (fonte: {sources_text}):

• {prices_text}

Para informações atualizadas sobre valores, formas de pagamento e possíveis descontos, entre em contato com nossa equipe comercial."""

        return f"""Para informações sobre valores e formas de pagamento, conforme documentado em {sources_text}, recomendo entrar em contato com nossa equipe comercial para obter:

• Valores atualizados dos cursos
• Formas de pagamento disponíveis
• Possíveis descontos e bolsas
• Condições especiais

Nossa equipe poderá fornecer todas as informações financeiras específicas para seu interesse."""

    def extract_horarios_info(self, content: str, sources: List[str]) -> str:
        """Extrai informações sobre horários"""
        return f"""Para informações sobre horários de funcionamento e atendimento, conforme documentação disponível ({', '.join(sources)}), recomendo:

• Consultar nossa secretaria acadêmica
• Verificar o portal do aluno
• Entrar em contato através dos canais oficiais

Nossa equipe poderá informar os horários específicos de:
- Secretaria e atendimento
- Aulas e laboratórios  
- Biblioteca e demais serviços"""

    def extract_matricula_info(self, content: str, sources: List[str]) -> str:
        """Extrai informações sobre matrícula"""
        return f"""**Informações sobre matrícula e inscrições** (baseado em {', '.join(sources)}):

Para realizar sua matrícula ou inscrição:

• Acesse nosso portal do aluno
• Consulte a secretaria acadêmica
• Verifique os documentos necessários
• Confirme prazos e procedimentos

{content[:300]}...

Nossa equipe acadêmica poderá orientá-lo sobre todo o processo de matrícula e os requisitos específicos."""

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

        else:
            return "Obrigado pela sua pergunta. Para obter informações mais específicas, recomendo entrar em contato com nossa equipe de suporte ou consultar nossa documentação oficial."

    def clean_response(self, response: str) -> str:
        """Limpa e formata a resposta"""
        if isinstance(response, list):
            response = response[0] if response else ""

        # Remover prompt da resposta se presente
        if "Resposta:" in response:
            response = response.split("Resposta:")[-1].strip()

        # Remover texto do prompt que pode ter vazado
        lines = response.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line and not any(skip in line.lower() for skip in ['contexto:', 'pergunta:', 'com base no contexto']):
                cleaned_lines.append(line)

        cleaned_response = '\n'.join(cleaned_lines)

        # Limitar tamanho da resposta
        if len(cleaned_response) > 800:
            cleaned_response = cleaned_response[:800] + "..."

        return cleaned_response if cleaned_response.strip() else "Não foi possível gerar uma resposta adequada."

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
