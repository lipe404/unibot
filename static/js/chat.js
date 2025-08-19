class UnibotChat {
  constructor() {
    this.messageInput = document.getElementById("messageInput");
    this.sendButton = document.getElementById("sendButton");
    this.chatMessages = document.getElementById("chatMessages");
    this.typingIndicator = document.getElementById("typingIndicator");
    this.charCount = document.getElementById("charCount");

    this.initializeEventListeners();
    this.updateTimestamp();
  }

  initializeEventListeners() {
    // Send button click
    this.sendButton.addEventListener("click", () => this.sendMessage());

    // Enter key press
    this.messageInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Character count
    this.messageInput.addEventListener("input", () => {
      const length = this.messageInput.value.length;
      this.charCount.textContent = `${length}/500`;

      if (length > 450) {
        this.charCount.style.color = "#e53e3e";
      } else {
        this.charCount.style.color = "#718096";
      }
    });

    // Auto-resize textarea
    this.messageInput.addEventListener("input", () => {
      this.messageInput.style.height = "auto";
      this.messageInput.style.height = this.messageInput.scrollHeight + "px";
    });
  }

  async sendMessage() {
    const message = this.messageInput.value.trim();

    if (!message) return;

    // Disable input
    this.setInputState(false);

    // Add user message
    this.addMessage(message, "user");

    // Clear input
    this.messageInput.value = "";
    this.charCount.textContent = "0/500";

    // Show typing indicator
    this.showTypingIndicator();

    try {
      // Send to backend
      const response = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: message }),
      });

      const data = await response.json();

      // Hide typing indicator
      this.hideTypingIndicator();

      if (data.success) {
        this.addMessage(data.response, "bot");
      } else {
        this.addMessage("Desculpe, ocorreu um erro. Tente novamente.", "bot");
      }
    } catch (error) {
      console.error("Erro ao enviar mensagem:", error);
      this.hideTypingIndicator();
      this.addMessage(
        "Erro de conexão. Verifique sua internet e tente novamente.",
        "bot"
      );
    }

    // Re-enable input
    this.setInputState(true);
  }

  addMessage(text, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${sender}-message`;

    const icon = sender === "bot" ? "fas fa-robot" : "fas fa-user";
    const timestamp = this.getCurrentTimestamp();

    messageDiv.innerHTML = `
            <div class="message-content">
                <i class="${icon}"></i>
                <div class="text">${this.formatMessage(text)}</div>
            </div>
            <div class="timestamp">${timestamp}</div>
        `;

    this.chatMessages.appendChild(messageDiv);
    this.scrollToBottom();
  }

  formatMessage(text) {
    // Convert line breaks to <br>
    text = text.replace(/\n/g, "<br>");

    // Convert URLs to links
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    text = text.replace(urlRegex, '<a href="$1" target="_blank">$1</a>');

    return text;
  }

  showTypingIndicator() {
    this.typingIndicator.style.display = "flex";
    this.scrollToBottom();
  }

  hideTypingIndicator() {
    this.typingIndicator.style.display = "none";
  }

  setInputState(enabled) {
    this.messageInput.disabled = !enabled;
    this.sendButton.disabled = !enabled;

    if (enabled) {
      this.messageInput.focus();
    }
  }

  scrollToBottom() {
    setTimeout(() => {
      this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }, 100);
  }

  getCurrentTimestamp() {
    return new Date().toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  updateTimestamp() {
    const initialTimestamp = document.getElementById("initialTimestamp");
    if (initialTimestamp) {
      initialTimestamp.textContent = this.getCurrentTimestamp();
    }
  }
}

// Initialize chat when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  new UnibotChat();
});
