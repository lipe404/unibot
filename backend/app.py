"""
UniBot - Backend API
Integração com modelo de IA para processamento de documentos e respostas
"""

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from document_processor import process_document, query_ai_model
import logging

#Configurações básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

#Configurações
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16 MB para upload de arquivos

#Verificar se a pasta de uploads existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

#Função para verificar se a extensão do arquivo é permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/upload', methods=['POST'])
def chat():
    """Endpoint para processar mensagens do usuário e retornar respostas"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({'error': 'Mensagem vazia'}), 400

        logger.info(f"Processando mensagem: {user_message}")

        #Processar a mensagem com o modelo de IA
        #Implementar a integração com a API do modelo de IA

        bot_response = query_ai_model(user_message)

        return jsonify({
            'response': bot_response,
            'status': 'success'
        })

    except Exception as e:
        logger.error(f"Erro no endpoint /api/chat: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
        """Endpoint para upload e processamento de documentos"""
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'Nenhum arquivo enviado'}), 400

            file = request.files['file']

            if file.filename == '':
                return jsonify({'error': 'Nome de arquivo vazio'}), 400

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                logger.info(f"Arquivo {filename} salvo em {filepath}")

                # Processar o documento (extrair texto, enviar para IA, etc.)
                process_result = process_document(filepath)

                return jsonify({
                    'message': f"Documento '{filename}' processado com sucesso! Agora posso responder perguntas sobre ele.",
                    'details': process_result,
                    'status': 'success'
                })
            else:
                return jsonify({'error': 'Tipo de arquivo não permitido'}), 400

        except Exception as e:
            logger.error(f"Erro no endpoint /api/upload: {str(e)}")
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

