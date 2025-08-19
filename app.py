from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import os
import logging
from werkzeug.utils import secure_filename
from config import Config
from models.ai_model import UnibotAI
from utils.database import Database
import json
import signal
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def signal_handler(sig, frame):
    """Handler para interrupção do programa"""
    logger.info("Recebido sinal de interrupção. Encerrando...")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def create_app():
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    CORS(app)

    logger.info("Inicializando componentes...")

    # Inicializar componentes
    try:
        db = Database()
        logger.info("Database inicializado")

        config_instance = Config()
        logger.info("Config carregado")

        # Criar diretórios necessários
        os.makedirs(config_instance.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(config_instance.VECTORSTORE_PATH, exist_ok=True)
        logger.info("Diretórios criados")

        unibot_ai = UnibotAI(config_instance)
        logger.info("UnibotAI inicializado")

    except Exception as e:
        logger.error(f"Erro na inicialização: {str(e)}")
        raise

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

    @app.route('/')
    def index():
        """Página principal do chat"""
        return render_template('index.html')

    @app.route('/admin')
    def admin():
        """Página administrativa"""
        return render_template('admin.html')

    @app.route('/chat', methods=['POST'])
    def chat():
        """Endpoint para processar mensagens do chat"""
        try:
            data = request.get_json()
            user_message = data.get('message', '').strip()

            if not user_message:
                return jsonify({
                    'success': False,
                    'error': 'Mensagem vazia'
                })

            logger.info(f"Recebida pergunta: {user_message[:50]}...")

            # Registrar pergunta no banco
            db.log_question(user_message)

            # Gerar resposta com timeout
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        unibot_ai.generate_response, user_message)
                    response = future.result(timeout=30)  # 30 segundos timeout
            except TimeoutError:
                logger.error("Timeout na geração de resposta")
                response = "Desculpe, a consulta está demorando mais que o esperado. Tente novamente com uma pergunta mais específica."

            # Registrar resposta no banco
            db.log_response(user_message, response)

            logger.info(f"Resposta enviada com sucesso")

            return jsonify({
                'success': True,
                'response': response
            })

        except Exception as e:
            logger.error(f"Erro no chat: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            })

    @app.route('/upload', methods=['POST'])
    def upload_files():
        """Endpoint para upload e treinamento com PDFs"""
        try:
            logger.info("=== INICIANDO UPLOAD DE ARQUIVOS ===")

            if 'files' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'Nenhum arquivo enviado'
                })

            files = request.files.getlist('files')
            uploaded_files = []
            training_results = []

            logger.info(f"Recebidos {len(files)} arquivos para upload")

            for i, file in enumerate(files):
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(
                        config_instance.UPLOAD_FOLDER, filename)

                    logger.info(
                        f"Processando arquivo {i+1}/{len(files)}: {filename}")

                    try:
                        # Salvar arquivo
                        file.save(filepath)
                        uploaded_files.append(filename)

                        # Verificar tamanho do arquivo
                        file_size = os.path.getsize(filepath)
                        logger.info(
                            f"Arquivo salvo: {file_size / 1024 / 1024:.2f} MB")

                        # Treinar IA com timeout mais longo
                        logger.info(f"Iniciando treinamento para: {filename}")

                        try:
                            with ThreadPoolExecutor(max_workers=1) as executor:
                                future = executor.submit(
                                    unibot_ai.pdf_processor.train_with_pdf,
                                    filepath,
                                    filename
                                )
                                success = future.result(
                                    timeout=300)  # 5 minutos timeout
                        except TimeoutError:
                            logger.error(
                                f"Timeout no treinamento de {filename}")
                            success = False

                        training_results.append({
                            'filename': filename,
                            'success': success
                        })

                        # Registrar no banco
                        if success:
                            db.log_pdf_upload(filename, filepath)
                            logger.info(f"✅ {filename} processado com SUCESSO")
                        else:
                            logger.error(
                                f"❌ {filename} FALHOU no processamento")

                    except Exception as e:
                        logger.error(f"Erro ao processar {filename}: {str(e)}")
                        training_results.append({
                            'filename': filename,
                            'success': False,
                            'error': str(e)
                        })

            logger.info("=== UPLOAD CONCLUÍDO ===")

            return jsonify({
                'success': True,
                'uploaded_files': uploaded_files,
                'training_results': training_results
            })

        except Exception as e:
            logger.error(f"Erro crítico no upload: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Erro ao processar arquivos: {str(e)}'
            })

    @app.route('/stats')
    def get_stats():
        """Endpoint para obter estatísticas"""
        try:
            stats = db.get_stats()
            return jsonify({
                'success': True,
                'stats': stats
            })
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Erro ao obter estatísticas'
            })

    @app.route('/trained-docs')
    def get_trained_docs():
        """Endpoint para obter lista de documentos treinados"""
        try:
            docs = db.get_trained_documents()
            return jsonify({
                'success': True,
                'documents': docs
            })
        except Exception as e:
            logger.error(f"Erro ao obter documentos: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Erro ao obter documentos'
            })

    @app.route('/clear-history', methods=['POST'])
    def clear_history():
        """Endpoint para limpar histórico"""
        try:
            unibot_ai.clear_history()
            return jsonify({
                'success': True,
                'message': 'Histórico limpo com sucesso'
            })
        except Exception as e:
            logger.error(f"Erro ao limpar histórico: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Erro ao limpar histórico'
            })

    @app.errorhandler(404)
    def not_found(error):
        return render_template('index.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Erro interno: {str(error)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

    return app


if __name__ == '__main__':
    try:
        logger.info("=== INICIANDO UNIBOT ===")
        app = create_app()
        logger.info("Aplicação criada com sucesso!")
        logger.info("Servidor iniciando em http://localhost:5000")
        logger.info("=== UNIBOT PRONTO PARA USO ===")
        app.run(debug=True, host='127.0.0.1', port=5000, threaded=True)
    except Exception as e:
        logger.error(f"Erro fatal na inicialização: {str(e)}")
        print(f"ERRO: {str(e)}")
