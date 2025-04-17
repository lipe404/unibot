/**
 * UniBot
 */
document.addEventListener('DOMContentLoaded', function() {
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const chatHistory = document.getElementById('chatHistory');
    const fileInput = document.getElementById('fileInput');
    // Função para adicionar mensagem ao chat
    function addMessage(text, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
        messageDiv.textContent = text;
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    // Enviar mensagem quando clicar no botão ou pressionar Enter
    function sendMessage() {
        const message = userInput.value.trim();
        if (message) {
            addMessage(message, true);
            userInput.value = '';
            // Simular resposta do bot (será substituído pela API real)
            setTimeout(() => {
                addMessage("Estou processando sua pergunta... Em breve terei uma resposta para você!", false);
                // Aqui você fará a chamada para a API Python
                fetchBotResponse(message);
            }, 500);
        }
    }
    // Função para buscar resposta da API Python
    async function fetchBotResponse(message) {
        try {
            const response = await fetch('http://localhost:5000/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    // Adicionar outros parâmetros aqui
                }),
            });
            if (!response.ok) {
                throw new Error('Erro na resposta da API');
            }
            const data = await response.json();
            addMessage(data.response, false);
        } catch (error) {
            console.error('Erro ao buscar resposta:', error);
            addMessage("Desculpe, estou tendo problemas para processar sua solicitação. Por favor, tente novamente mais tarde.", false);
        }
    }
    // Função para enviar arquivo
    function handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        // Verificar tipo de arquivo
        const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
        if (!validTypes.includes(file.type)) {
            alert('Por favor, envie apenas arquivos PDF, DOCX ou TXT.');
            return;
        }
        // Mostrar mensagem de upload
        addMessage(`Enviando arquivo: ${file.name}...`, true);
        // Aqui você enviaria o arquivo para o backend Python
        uploadFile(file);
    }
    // Função para enviar arquivo para o backend
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
            addMessage(data.message, false);
        } catch (error) {
            console.error('Erro no upload:', error);
            addMessage("Desculpe, houve um problema ao processar seu arquivo. Por favor, tente novamente.", false);
        }
    }
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    fileInput.addEventListener('change', handleFileUpload);
});