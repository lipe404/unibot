class UnibotAdmin {
  constructor() {
    this.initializeEventListeners();
    this.loadStats();
    this.loadTrainedDocs();
  }

  initializeEventListeners() {
    // File selection
    const selectFiles = document.getElementById("selectFiles");
    const fileInput = document.getElementById("fileInput");
    const uploadArea = document.getElementById("uploadArea");

    selectFiles.addEventListener("click", () => {
      fileInput.click();
    });

    fileInput.addEventListener("change", (e) => {
      this.handleFileSelection(e.target.files);
    });

    // Drag and drop
    uploadArea.addEventListener("dragover", (e) => {
      e.preventDefault();
      uploadArea.style.borderColor = "#667eea";
      uploadArea.style.backgroundColor = "rgba(102, 126, 234, 0.1)";
    });

    uploadArea.addEventListener("dragleave", (e) => {
      e.preventDefault();
      uploadArea.style.borderColor = "#cbd5e0";
      uploadArea.style.backgroundColor = "transparent";
    });

    uploadArea.addEventListener("drop", (e) => {
      e.preventDefault();
      uploadArea.style.borderColor = "#cbd5e0";
      uploadArea.style.backgroundColor = "transparent";

      const files = Array.from(e.dataTransfer.files).filter(
        (file) => file.type === "application/pdf"
      );

      if (files.length > 0) {
        this.handleFileSelection(files);
      } else {
        this.showAlert("Apenas arquivos PDF são aceitos.", "warning");
      }
    });

    // Upload button
    const uploadFiles = document.getElementById("uploadFiles");
    uploadFiles.addEventListener("click", () => {
      this.uploadFiles();
    });

    // Clear history button
    const clearHistory = document.getElementById("clearHistory");
    clearHistory.addEventListener("click", () => {
      this.clearHistory();
    });
  }

  handleFileSelection(files) {
    const fileList = document.getElementById("fileList");
    const selectedFiles = document.getElementById("selectedFiles");

    if (files.length === 0) {
      fileList.style.display = "none";
      return;
    }

    // Clear previous selection
    selectedFiles.innerHTML = "";

    // Add files to list
    Array.from(files).forEach((file) => {
      if (file.type === "application/pdf") {
        const li = document.createElement("li");
        li.innerHTML = `
                    <i class="fas fa-file-pdf"></i>
                    <span>${file.name}</span>
                    <small>(${this.formatFileSize(file.size)})</small>
                `;
        selectedFiles.appendChild(li);
      }
    });

    fileList.style.display = "block";
  }

  async uploadFiles() {
    const fileInput = document.getElementById("fileInput");
    const uploadButton = document.getElementById("uploadFiles");

    if (!fileInput.files.length) {
      this.showAlert("Selecione pelo menos um arquivo PDF.", "warning");
      return;
    }

    // Disable button and show loading
    uploadButton.disabled = true;
    uploadButton.innerHTML =
      '<i class="fas fa-spinner fa-spin"></i> Processando...';

    try {
      const formData = new FormData();
      Array.from(fileInput.files).forEach((file) => {
        formData.append("files", file);
      });

      const response = await fetch("/upload", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        this.showAlert(
          `${result.uploaded_files.length} arquivo(s) processado(s) com sucesso!`,
          "success"
        );

        // Reset form
        fileInput.value = "";
        document.getElementById("fileList").style.display = "none";

        // Reload data
        this.loadStats();
        this.loadTrainedDocs();
      } else {
        this.showAlert(result.error || "Erro ao processar arquivos.", "error");
      }
    } catch (error) {
      console.error("Erro no upload:", error);
      this.showAlert("Erro de conexão. Tente novamente.", "error");
    }

    // Re-enable button
    uploadButton.disabled = false;
    uploadButton.innerHTML =
      '<i class="fas fa-upload"></i> Fazer Upload e Treinar IA';
  }

  async loadStats() {
    try {
      const response = await fetch("/stats");
      const result = await response.json();

      if (result.success) {
        document.getElementById("totalDocs").textContent =
          result.stats.total_pdfs;
        document.getElementById("totalQuestions").textContent =
          result.stats.total_questions;
        document.getElementById("totalChunks").textContent =
          result.stats.total_chunks;
      }
    } catch (error) {
      console.error("Erro ao carregar estatísticas:", error);
    }
  }

  async loadTrainedDocs() {
    const trainedDocs = document.getElementById("trainedDocs");

    try {
      const response = await fetch("/trained-docs");
      const result = await response.json();

      if (result.success && result.documents.length > 0) {
        trainedDocs.innerHTML = `
                    <div class="docs-list">
                        ${result.documents
                          .map(
                            (doc) => `
                            <div class="doc-item">
                                <div class="doc-info">
                                    <i class="fas fa-file-pdf"></i>
                                    <div>
                                        <strong>${doc.filename}</strong>
                                        <small>Carregado em: ${this.formatDate(
                                          doc.upload_date
                                        )}</small>
                                    </div>
                                </div>
                                <span class="doc-status ${doc.status}">${
                              doc.status
                            }</span>
                            </div>
                        `
                          )
                          .join("")}
                    </div>
                `;
      } else {
        trainedDocs.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-file-pdf"></i>
                        <p>Nenhum documento treinado ainda.</p>
                        <small>Faça upload de PDFs para começar a treinar a IA.</small>
                    </div>
                `;
      }
    } catch (error) {
      console.error("Erro ao carregar documentos:", error);
      trainedDocs.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Erro ao carregar documentos.</p>
                </div>
            `;
    }
  }

  async clearHistory() {
    if (!confirm("Tem certeza que deseja limpar o histórico de conversas?")) {
      return;
    }

    try {
      const response = await fetch("/clear-history", {
        method: "POST",
      });

      const result = await response.json();

      if (result.success) {
        this.showAlert("Histórico limpo com sucesso!", "success");
        this.loadStats();
      } else {
        this.showAlert(result.error || "Erro ao limpar histórico.", "error");
      }
    } catch (error) {
      console.error("Erro ao limpar histórico:", error);
      this.showAlert("Erro de conexão. Tente novamente.", "error");
    }
  }

  formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  formatDate(dateString) {
    return new Date(dateString).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  showAlert(message, type = "info") {
    // Create alert element
    const alert = document.createElement("div");
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
            <i class="fas fa-${this.getAlertIcon(type)}"></i>
            <span>${message}</span>
            <button class="alert-close">&times;</button>
        `;

    // Add styles
    alert.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${this.getAlertColor(type)};
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            gap: 10px;
            z-index: 1000;
            animation: slideInRight 0.3s ease;
        `;

    // Add close functionality
    const closeBtn = alert.querySelector(".alert-close");
    closeBtn.style.cssText = `
            background: none;
            border: none;
            color: white;
            font-size: 1.2em;
            cursor: pointer;
            margin-left: 10px;
        `;

    closeBtn.addEventListener("click", () => {
      alert.remove();
    });

    // Add to page
    document.body.appendChild(alert);

    // Auto remove after 5 seconds
    setTimeout(() => {
      if (alert.parentNode) {
        alert.remove();
      }
    }, 5000);
  }

  getAlertIcon(type) {
    const icons = {
      success: "check-circle",
      error: "exclamation-circle",
      warning: "exclamation-triangle",
      info: "info-circle",
    };
    return icons[type] || "info-circle";
  }

  getAlertColor(type) {
    const colors = {
      success: "#48bb78",
      error: "#e53e3e",
      warning: "#ed8936",
      info: "#667eea",
    };
    return colors[type] || "#667eea";
  }
}

// Add CSS for animations
const style = document.createElement("style");
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    .docs-list {
        display: flex;
        flex-direction: column;
        gap: 15px;
    }

    .doc-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px;
        background: rgba(102, 126, 234, 0.05);
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }

    .doc-info {
        display: flex;
        align-items: center;
        gap: 15px;
    }

    .doc-info i {
        font-size: 1.5em;
        color: #e53e3e;
    }

    .doc-info strong {
        display: block;
        color: #4a5568;
    }

    .doc-info small {
        color: #718096;
    }

    .doc-status {
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8em;
        font-weight: bold;
        text-transform: uppercase;
    }

    .doc-status.active {
        background: #c6f6d5;
        color: #22543d;
    }

    .empty-state, .error-state {
        text-align: center;
        padding: 40px;
        color: #718096;
    }

    .empty-state i, .error-state i {
        font-size: 3em;
        margin-bottom: 15px;
        display: block;
    }

    .error-state i {
        color: #e53e3e;
    }
`;
document.head.appendChild(style);

// Initialize admin when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  new UnibotAdmin();
});
