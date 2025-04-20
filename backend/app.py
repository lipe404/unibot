"""
UniBot - Backend API
Integração com modelo de IA para processamento de documentos e respostas
"""

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import logging
from document_processor import process_document, query_ai_model

# ----------------------------
# Configuração e Inicialização
# ----------------------------

app = Flask(__name__)

# Pastas e extensões permitidas
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
MAX_FILE_SIZE_MB = 16

# Configurações do Flask
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_MB * 1024 * 1024

# Criar pasta de uploads se necessário
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("UniBotAPI")

# ----------------------------
# Funções auxiliares
# ----------------------------

def allowed_file(filename):
    """Verifica se o arquivo tem uma extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------------------
# Endpoints da API
# ----------------------------

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """
    Endpoint para interação com o modelo de IA.
    Espera um JSON com campo 'message'.
    """
    try:
        data = request.get_json(force=True)
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'error': 'Mensagem vazia.'}), 400

        logger.info(f"Usuário: {user_message}")

        bot_response = query_ai_model(user_message)

        return jsonify({
            'response': bot_response,
            'status': 'success'
        }), 200

    except Exception as e:
        logger.exception("Erro no endpoint /api/chat")
        return jsonify({'error': 'Erro ao processar a requisição.', 'details': str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def api_upload():
    """
    Endpoint para upload de documentos (PDF, DOCX, TXT).
    Retorna informações sobre o processamento do documento.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado.'}), 400

        file = request.files['file']

        if not file or file.filename == '':
            return jsonify({'error': 'Nome do arquivo está vazio.'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de arquivo não permitido. Permitidos: PDF, DOCX, TXT'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        logger.info(f"Arquivo recebido: {filename}")

        result = process_document(filepath)

        return jsonify({
            'message': f"Documento '{filename}' processado com sucesso!",
            'details': result,
            'status': 'success'
        }), 200

    except Exception as e:
        logger.exception("Erro no endpoint /api/upload")
        return jsonify({'error': 'Erro ao processar o arquivo.', 'details': str(e)}), 500


# ----------------------------
# Execução do servidor
# ----------------------------

if __name__ == '__main__':
    logger.info("Iniciando servidor UniBot API...")
    app.run(host='0.0.0.0', port=5000, debug=True)
