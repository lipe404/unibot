from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import os
import logging
from werkzeug.utils import secure_filename
from config import Config
from models.ai_model import UnibotAI
from utils.database import Database
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar aplicação Flask
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Inicializar componentes
db = Database()

# Passar a instância da classe Config, não app.config
config_instance = Config()
unibot_ai = UnibotAI(config_instance)

# Criar diretórios necessários
os.makedirs(config_instance.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(config_instance.VECTORSTORE_PATH, exist_ok=True)


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

        # Registrar pergunta no banco
        db.log_question(user_message)

        # Gerar resposta
        response = unibot_ai.generate_response(user_message)

        # Registrar resposta no banco
        db.log_response(user_message, response)

        logger.info(f"Pergunta processada: {user_message[:50]}...")

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
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo enviado'
            })

        files = request.files.getlist('files')
        uploaded_files = []
        training_results = []

        for file in files:
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(
                    config_instance.UPLOAD_FOLDER, filename)

                # Salvar arquivo
                file.save(filepath)
                uploaded_files.append(filename)

                # Treinar IA com o PDF
                success = unibot_ai.pdf_processor.train_with_pdf(
                    filepath, filename)
                training_results.append({
                    'filename': filename,
                    'success': success
                })

                # Registrar no banco
                if success:
                    db.log_pdf_upload(filename, filepath)

                logger.info(
                    f"Arquivo processado: {filename} - Sucesso: {success}")

        return jsonify({
            'success': True,
            'uploaded_files': uploaded_files,
            'training_results': training_results
        })

    except Exception as e:
        logger.error(f"Erro no upload: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao processar arquivos'
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


if __name__ == '__main__':
    logger.info("Iniciando Unibot...")
    app.run(debug=True, host='0.0.0.0', port=5000)
