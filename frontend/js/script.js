/**
 * UniBot - Script de Interação Front-End
 * Autor: Felipe Toledo
 * Descrição: Lida com mensagens do usuário, comunicação com a API Python
 * e envio de arquivos PDF/DOCX/TXT para análise.
 */
document.addEventListener('DOMContentLoaded', function () {
    // Elementos da interface
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const chatHistory = document.getElementById('chatHistory');
    const fileInput = document.getElementById('fileInput');
    // Estado de carregamento
    let isLoading = false;
    /**
     * Cria e adiciona uma mensagem ao histórico de chat
     * @param {string} text - Conteúdo da mensagem
     * @param {boolean} isUser - Define se é uma mensagem do usuário
     */
    function addMessage(text, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', isUser ? 'user-message' : 'bot-message');
        messageDiv.textContent = text;
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    /**
     * Cria e retorna um elemento de carregamento
     */
    function createLoadingElement() {
        const loading = document.createElement('div');
        loading.classList.add('message', 'bot-message', 'loading');
        loading.textContent = "Digitando...";
        return loading;
    }
    /**
     * Envia uma mensagem para o bot
     */
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message || isLoading) return;

        addMessage(message, true);
        userInput.value = '';
        isLoading = true;

        const loadingElem = createLoadingElement();
        chatHistory.appendChild(loadingElem);
        chatHistory.scrollTop = chatHistory.scrollHeight;

        fetchBotResponse(message)
            .then(response => {
                chatHistory.removeChild(loadingElem);
                addMessage(response, false);
            })
            .catch(error => {
                chatHistory.removeChild(loadingElem);
                console.error('Erro ao buscar resposta:', error);
                addMessage("Desculpe, estou com problemas técnicos. Tente novamente mais tarde.", false);
            })
            .finally(() => {
                isLoading = false;
            });
    }

    /**
     * Busca a resposta do backend Python
     * @param {string} message - Mensagem do usuário
     * @returns {Promise<string>} - Resposta do bot
     */
    async function fetchBotResponse(message) {
        const response = await fetch('http://localhost:5000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message }),
        });

        if (!response.ok) {
            throw new Error('Erro na resposta da API');
        }

        const data = await response.json();
        return data.response || "Nenhuma resposta recebida.";
    }
    /**
     * Trata o upload de arquivos
     * @param {Event} event
     */
    function handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        const validTypes = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ];

        if (!validTypes.includes(file.type)) {
            alert('Envie apenas arquivos PDF, DOCX ou TXT.');
            return;
        }

        addMessage(`Enviando arquivo: ${file.name}...`, true);
        uploadFile(file);
    }
    /**
     * Envia o arquivo para o backend
     * @param {File} file
     */
    async function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('http://localhost:5000/api/upload', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Erro no upload do arquivo');
            }

            const data = await response.json();
            addMessage(data.message || "Arquivo enviado com sucesso!", false);
        } catch (error) {
            console.error('Erro no upload:', error);
            addMessage("Erro ao processar o arquivo. Tente novamente.", false);
        }
    }
    // Listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendMessage();
    });
    fileInput.addEventListener('change', handleFileUpload);
});
