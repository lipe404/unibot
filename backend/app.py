"""
UniBot - Backend API
Integração com modelo de IA para processamento de documentos e respostas
"""

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import logging
from document_processor import process_document, query_ai_model

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar o app Flask
app = Flask(__name__)

# Configurações
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite: 16MB

# Criar a pasta de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Função utilitária para verificar se o arquivo é permitido
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------------------
# Endpoint de chat com IA
# ----------------------------
@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Recebe mensagem do usuário e retorna resposta do modelo de IA"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'error': 'Mensagem vazia'}), 400

        logger.info(f"Mensagem recebida: {user_message}")

        # Obter resposta da IA
        bot_response = query_ai_model(user_message)

        return jsonify({
            'response': bot_response,
            'status': 'success'
        })

    except Exception as e:
        logger.error(f"Erro no endpoint /api/chat: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ----------------------------
# Endpoint para upload de arquivos
# ----------------------------
@app.route('/api/upload', methods=['POST'])
def api_upload():
    """Recebe e processa arquivos PDF, DOCX ou TXT"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400

        file = request.files['file']

        if not file.filename:
            return jsonify({'error': 'Nome do arquivo está vazio'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de arquivo não permitido'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        logger.info(f"Arquivo recebido: {filename} (salvo em {filepath})")

        # Processar o conteúdo do documento
        process_result = process_document(filepath)

        return jsonify({
            'message': f"Documento '{filename}' processado com sucesso! Agora posso responder perguntas sobre ele.",
            'details': process_result,
            'status': 'success'
        })

    except Exception as e:
        logger.error(f"Erro no endpoint /api/upload: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ----------------------------
# Inicialização do servidor
# ----------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
