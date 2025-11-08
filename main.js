// WhatsApp Bulk Contact Manager & Messenger
// Main JavaScript Module

// ** VARIÁVEL DE AMBIENTE DA API (ATUALIZE ESTE VALOR) **
// Configure com o URL principal do seu serviço Render (ex: https://seu-servico.onrender.com)
const API_BASE_URL = 'https://site-excel-escola-v1-1-0.onrender.com';

class WhatsAppBulkManager {
    constructor() {
        this.contacts = [];
        this.processedContacts = [];
        this.currentFile = null;
        this.columns = [];
        this.mode = 'vcf';
        this.chatHistory = []; // Novo: Histórico do Chatbot
        
        this.initializeElements();
        this.bindEvents();
        this.loadSavedState();
        this.initializeChat(); // Novo: Inicializa o Chatbot
    }

    initializeElements() {
        // File upload elements
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('fileInput');
        this.fileInfo = document.getElementById('fileInfo');
        this.fileName = document.getElementById('fileName');
        this.fileSize = document.getElementById('fileSize');
        this.removeFile = document.getElementById('removeFile');
        this.browseBtn = document.getElementById('browseBtn');

        // Column mapping elements
        this.mappingSection = document.getElementById('mappingSection');
        this.nameColumn = document.getElementById('nameColumn');
        this.phoneColumn = document.getElementById('phoneColumn');
        this.detectColumnsBtn = document.getElementById('detectColumnsBtn');
        this.aiStatus = document.getElementById('aiStatus');

        // Preview elements
        this.previewSection = document.getElementById('previewSection');
        this.totalContacts = document.getElementById('totalContacts');
        this.contactTable = document.getElementById('contactTable');

        // Message composer elements
        this.messageSection = document.getElementById('messageSection');
        this.messageTemplate = document.getElementById('messageTemplate');
        this.messagePreview = document.getElementById('messagePreview');
        this.charCount = document.getElementById('charCount');

        // API config elements
        this.apiConfigSection = document.getElementById('apiConfigSection');
        this.accessToken = document.getElementById('accessToken');
        this.phoneNumberId = document.getElementById('phoneNumberId');
        this.templateName = document.getElementById('templateName');
        this.languageCode = document.getElementById('languageCode');

        // Action elements
        this.actionSection = document.getElementById('actionSection');
        this.generateVcfBtn = document.getElementById('generateVcfBtn');
        this.sendMessagesBtn = document.getElementById('sendMessagesBtn');

        // Mode toggle
        this.modeToggle = document.getElementById('modeToggle');

        // Modal elements
        this.progressModal = document.getElementById('progressModal');
        this.helpModal = document.getElementById('helpModal');

        // Chatbot elements (NOVO)
        this.chatToggleBtn = document.getElementById('chatToggleBtn');
        this.chatContainer = document.getElementById('chatContainer');
        this.chatCloseBtn = document.getElementById('chatCloseBtn');
        this.chatMessages = document.getElementById('chatMessages');
        this.chatForm = document.getElementById('chatForm');
        this.chatInput = document.getElementById('chatInput');
        this.chatSendBtn = document.getElementById('chatSendBtn');
        this.chatStatus = document.getElementById('chatStatus');
    }

    bindEvents() {
        // File upload events
        this.dropZone.addEventListener('dragover', this.handleDragOver.bind(this));
        this.dropZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.dropZone.addEventListener('drop', this.handleDrop.bind(this));
        this.dropZone.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        this.removeFile.addEventListener('click', this.clearFile.bind(this));

        // Column mapping events
        this.detectColumnsBtn.addEventListener('click', this.detectColumns.bind(this));
        this.nameColumn.addEventListener('change', this.updatePreview.bind(this));
        this.phoneColumn.addEventListener('change', this.updatePreview.bind(this));

        // Message composer events
        this.messageTemplate.addEventListener('input', this.updateMessagePreview.bind(this));

        // Mode toggle
        this.modeToggle.addEventListener('change', this.toggleMode.bind(this));

        // Action buttons
        this.generateVcfBtn.addEventListener('click', this.generateVCF.bind(this));
        this.sendMessagesBtn.addEventListener('click', this.sendMessages.bind(this));

        // Modal events
        document.getElementById('helpBtn').addEventListener('click', () => this.showModal('helpModal'));
        document.getElementById('closeHelp').addEventListener('click', () => this.hideModal('helpModal'));
        document.getElementById('closeProgress').addEventListener('click', () => this.hideModal('progressModal'));

        // API config events
        this.accessToken.addEventListener('input', this.saveApiConfig.bind(this));
        this.phoneNumberId.addEventListener('input', this.saveApiConfig.bind(this));
        this.templateName.addEventListener('input', this.saveApiConfig.bind(this));
        this.languageCode.addEventListener('change', this.saveApiConfig.bind(this));

        // Chatbot events (NOVO)
        this.chatToggleBtn.addEventListener('click', this.toggleChat.bind(this));
        this.chatCloseBtn.addEventListener('click', this.toggleChat.bind(this));
        this.chatForm.addEventListener('submit', this.handleChatSubmit.bind(this));
        this.chatInput.addEventListener('input', () => {
            this.chatSendBtn.disabled = this.chatInput.value.trim() === '';
        });
    }

    // NOVO: Lógica do Chatbot
    initializeChat() {
        // Inicializa o histórico do chat com a saudação da AI
        this.addMessage("Olá! Sou o **Ajudante General a AI que pensa por você**. Estou aqui para te ajudar a entender a estrutura do seu arquivo de contatos e como usar todas as funcionalidades do site para envio em massa. O que você gostaria de saber sobre o seu arquivo ou sobre o site?", 'ai', true);
    }
    
    toggleChat() {
        this.chatContainer.classList.toggle('hidden');
        if (!this.chatContainer.classList.contains('hidden')) {
            this.scrollToBottom();
            this.chatInput.focus();
        }
    }
    
    handleChatSubmit(e) {
        e.preventDefault();
        const userMessage = this.chatInput.value.trim();
        if (!userMessage) return;

        this.addMessage(userMessage, 'user');
        this.chatInput.value = '';
        this.chatSendBtn.disabled = true;

        this.callChatAPI(userMessage);
    }

    addMessage(text, role, isSilent = false) {
        // Limita o histórico a 20 mensagens (10 pares) para evitar sobrecarga no payload
        if (!isSilent && this.chatHistory.length >= 20) {
            this.chatHistory.shift(); // Remove o mais antigo
        }
        
        const messageObject = { role: role, text: text };
        if (!isSilent) {
            this.chatHistory.push(messageObject);
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'}`;

        const bubble = document.createElement('div');
        bubble.className = `message-bubble ${role === 'user' ? 'user-message' : 'ai-message'}`;

        // Usa Markdown para formatar a saída da AI
        bubble.innerHTML = marked.parse(text);

        messageDiv.appendChild(bubble);
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    getContactDataSample() {
        if (this.contacts.length === 0) return null;
        
        // Envia apenas as 5 primeiras linhas de dados completos
        const sample = this.contacts.slice(0, 5);
        
        // Retorna como JSON stringificado para o backend
        return JSON.stringify(sample, null, 2);
    }
    
    async callChatAPI(userMessage, isInitial = false) {
        this.chatStatus.classList.remove('hidden');
        
        const dataSample = this.getContactDataSample();
        
        // O histórico inclui a mensagem atual do usuário (já adicionada via addMessage)
        const historyPayload = this.chatHistory;
        
        const payload = {
            message: userMessage,
            history: historyPayload,
            contact_data_sample: dataSample
        };

        try {
            // Usa o URL base configurado
            const response = await fetch(`${API_BASE_URL}/api/chat`, { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.status === 429) {
                this.addMessage('Desculpe, o limite de taxa para o chatbot foi excedido. Tente novamente em 1 hora.', 'ai');
                return;
            }
            
            if (!response.ok) {
                 const errorData = await response.json();
                 this.addMessage(`Erro da API Chatbot: ${errorData.detail || 'Erro desconhecido.'}`, 'ai');
                 // Remove a última mensagem do histórico para que o usuário possa tentar novamente sem poluir
                 this.chatHistory.pop();
                 return;
            }

            const data = await response.json();
            
            // Adiciona a resposta da AI. A função addMessage cuidará de atualizar o histórico.
            this.addMessage(data.response, 'ai');

        } catch (error) {
            console.error('Chat API Error:', error);
            this.addMessage('Desculpe, não foi possível conectar ao assistente de AI. Verifique se o backend do Render está ativo.', 'ai');
            // Remove a última mensagem do histórico em caso de falha de conexão
            this.chatHistory.pop();
        } finally {
            this.chatStatus.classList.add('hidden');
        }
    }
    
    // FIM NOVO: Lógica do Chatbot

    // File Upload Handling
    handleDragOver(e) {
        e.preventDefault();
        this.dropZone.classList.add('drag-over');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.dropZone.classList.remove('drag-over');
    }

    handleDrop(e) {
        e.preventDefault();
        this.dropZone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.processFile(file);
        }
    }

    async processFile(file) {
        if (!file.name.match(/\.(xlsx|xls|csv)$/i)) {
            this.showError('Por favor, carregue um arquivo Excel ou CSV válido');
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            this.showError('O tamanho do arquivo deve ser inferior a 10MB');
            return;
        }

        this.currentFile = file;
        this.showFileInfo(file);
        
        try {
            this.showProgress('Processando Arquivo', 'Lendo dados da planilha. Por favor, aguarde...');
            const contacts = await ExcelParser.parse(file);
            this.contacts = contacts;
            this.hideProgress();
            this.showMappingSection();
        } catch (error) {
            this.hideProgress();
            this.showError('Erro ao analisar o arquivo: ' + error.message);
        }
    }

    showFileInfo(file) {
        this.fileName.textContent = file.name;
        this.fileSize.textContent = this.formatFileSize(file.size);
        this.fileInfo.classList.remove('hidden');
    }

    clearFile() {
        this.currentFile = null;
        this.contacts = [];
        this.processedContacts = [];
        this.fileInfo.classList.add('hidden');
        this.mappingSection.classList.add('hidden');
        this.previewSection.classList.add('hidden');
        this.messageSection.classList.add('hidden');
        this.apiConfigSection.classList.add('hidden');
        this.actionSection.classList.add('hidden');
        this.fileInput.value = '';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Column Mapping
    showMappingSection() {
        this.populateColumnSelectors();
        this.mappingSection.classList.remove('hidden');
        this.mappingSection.classList.add('fade-in');
    }

    populateColumnSelectors() {
        if (this.contacts.length === 0) return;

        const headers = Object.keys(this.contacts[0]);
        this.columns = headers;

        // Clear existing options
        this.nameColumn.innerHTML = '<option value="">Selecione a coluna...</option>';
        this.phoneColumn.innerHTML = '<option value="">Selecione a coluna...</option>';

        headers.forEach(header => {
            const option1 = new Option(header, header);
            const option2 = new Option(header, header);
            this.nameColumn.add(option1);
            this.phoneColumn.add(option2);
        });
    }

    async detectColumns() {
        if (this.columns.length === 0) return;

        this.detectColumnsBtn.disabled = true;
        this.detectColumnsBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Detectando...';

        try {
            // Adapta a chamada para o novo endpoint de detecção
            const payload = {
                headers: this.columns,
                sample_data: this.contacts.slice(0, 5) // Envia uma amostra
            };
            
            // Usa o URL base configurado
            const response = await fetch(`${API_BASE_URL}/api/detect-columns`, { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                 const errorData = await response.json();
                 this.showError(`Erro na Detecção AI: ${errorData.detail || 'Erro desconhecido.'}`);
                 throw new Error('AI detection failed');
            }
            
            const result = await response.json();
            
            if (result.name_key && this.columns.includes(result.name_key)) {
                this.nameColumn.value = result.name_key;
            }
            if (result.number_key && this.columns.includes(result.number_key)) {
                this.phoneColumn.value = result.number_key;
            }

            this.aiStatus.classList.remove('hidden');
            this.updatePreview();

        } catch (error) {
            console.error('AI detection failed:', error);
            this.showError('A detecção por AI falhou. Mapeie as colunas manualmente.');
        } finally {
            this.detectColumnsBtn.disabled = false;
            this.detectColumnsBtn.innerHTML = '<i class="fas fa-magic mr-2"></i>Detecção de Colunas com AI';
        }
    }

    // Contact Preview
    updatePreview() {
        const nameKey = this.nameColumn.value;
        const phoneKey = this.phoneColumn.value;

        if (!nameKey || !phoneKey) return;

        this.processContacts(nameKey, phoneKey);
        this.showPreview();
        this.showMessageSection();
        this.showActionSection();
    }

    processContacts(nameKey, phoneKey) {
        this.processedContacts = this.contacts.map((contact, index) => {
            const name = contact[nameKey] || '';
            const phone = contact[phoneKey] || '';
            
            // País padrão Brasil (55)
            const cleanedPhone = NumberCleaner.clean(phone, '55'); 
            const status = this.getPhoneStatus(phone, cleanedPhone);

            return {
                id: index + 1,
                name: name.toString().trim(),
                originalPhone: phone.toString().trim(),
                cleanedPhone: cleanedPhone,
                status: status,
                originalData: contact
            };
        });
    }

    getPhoneStatus(original, cleaned) {
        if (!cleaned) return 'invalid';
        // Remove todos os caracteres não-dígitos para comparação
        const originalDigits = original.toString().replace(/\D/g, ''); 
        const cleanedDigits = cleaned.toString().replace(/\D/g, '');

        if (originalDigits === cleanedDigits) return 'valid';
        // Se a limpeza resulta em um número E.164 válido, mas diferente, foi corrigido
        if (cleaned.startsWith('+')) return 'corrected'; 
        return 'invalid';
    }

    showPreview() {
        this.totalContacts.textContent = this.processedContacts.length;
        this.renderContactTable();
        this.previewSection.classList.remove('hidden');
        this.previewSection.classList.add('fade-in');
    }

    renderContactTable() {
        const tbody = this.contactTable;
        tbody.innerHTML = '';

        // Exibe mais contatos (primeiros 200) para remover a limitação anterior
        const displayContacts = this.processedContacts.slice(0, 200); 

        displayContacts.forEach(contact => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-50';

            const statusIcon = this.getStatusIcon(contact.status);
            const statusClass = `status-${contact.status}`;

            row.innerHTML = `
                <td class="px-4 py-2 text-gray-600">${contact.id}</td>
                <td class="px-4 py-2">
                    <input type="text" value="${this.escapeHtml(contact.name)}" 
                           class="border-0 bg-transparent w-full focus:outline-none focus:bg-white focus:border focus:border-gray-300 rounded px-1"
                           onchange="app.updateContactName(${contact.id - 1}, this.value)">
                </td>
                <td class="px-4 py-2">
                    <input type="text" value="${this.escapeHtml(contact.cleanedPhone)}" 
                           class="border-0 bg-transparent w-full focus:outline-none focus:bg-white focus:border focus:border-gray-300 rounded px-1"
                           onchange="app.updateContactPhone(${contact.id - 1}, this.value)">
                </td>
                <td class="px-4 py-2 ${statusClass}">${statusIcon}</td>
                <td class="px-4 py-2">
                    <button onclick="app.downloadSingleVCF(${contact.id - 1})" 
                            class="text-blue-600 hover:text-blue-800 text-xs">
                        <i class="fas fa-download mr-1"></i>VCF
                    </button>
                </td>
            `;

            tbody.appendChild(row);
        });
    }

    getStatusIcon(status) {
        switch (status) {
            case 'valid': return '🟢 Válido';
            case 'corrected': return '🟡 Corrigido';
            case 'invalid': return '🔴 Inválido';
            default: return '⚪ Desconhecido';
        }
    }

    updateContactName(index, value) {
        if (this.processedContacts[index]) {
            this.processedContacts[index].name = value;
            this.updateMessagePreview();
        }
    }

    updateContactPhone(index, value) {
        if (this.processedContacts[index]) {
            const cleaned = NumberCleaner.clean(value, '55');
            this.processedContacts[index].cleanedPhone = cleaned;
            this.processedContacts[index].status = this.getPhoneStatus(value, cleaned);
            this.renderContactTable(); // Renderiza novamente para atualizar o status/ícone
        }
    }

    // Message Composer
    showMessageSection() {
        this.messageSection.classList.remove('hidden');
        this.messageSection.classList.add('fade-in');
        this.updateMessagePreview();
    }

    updateMessagePreview() {
        const template = this.messageTemplate.value;
        this.charCount.textContent = template.length;

        if (this.processedContacts.length > 0) {
            const firstContact = this.processedContacts[0];
            const preview = this.replacePlaceholders(template, firstContact);
            this.messagePreview.textContent = preview;
        }

        // Update character count color
        if (template.length > 4096) {
            this.charCount.className = 'text-xs text-red-500 font-medium';
        } else if (template.length > 3500) {
            this.charCount.className = 'text-xs text-yellow-500 font-medium';
        } else {
            this.charCount.className = 'text-xs text-gray-500';
        }
    }

    replacePlaceholders(template, contact) {
        let result = template;
        result = result.replace(/{name}/g, contact.name || '');
        
        // Replace other custom fields
        Object.keys(contact.originalData).forEach(key => {
            const placeholder = `{${key}}`;
            result = result.replace(new RegExp(placeholder, 'g'), contact.originalData[key] || '');
        });

        return result;
    }

    // Mode Toggle
    toggleMode() {
        this.mode = this.modeToggle.value;
        
        if (this.mode === 'api') {
            this.apiConfigSection.classList.remove('hidden');
            this.generateVcfBtn.style.display = 'none';
            this.sendMessagesBtn.style.display = 'inline-flex';
        } else {
            this.apiConfigSection.classList.add('hidden');
            this.generateVcfBtn.style.display = 'inline-flex';
            this.sendMessagesBtn.style.display = 'none';
        }
    }

    // Action Section
    showActionSection() {
        this.actionSection.classList.remove('hidden');
        this.actionSection.classList.add('fade-in');
        this.toggleMode(); // Update button visibility
    }

    // VCF Generation
    async generateVCF() {
        const validContacts = this.processedContacts.filter(c => c.status !== 'invalid');
        
        if (validContacts.length === 0) {
            this.showError('Nenhum contato válido para gerar arquivo VCF');
            return;
        }

        this.showProgress('Gerando Arquivo VCF', `Processando ${validContacts.length} contatos...`);

        try {
            const vcfContent = VCFGenerator.generate(validContacts);
            const blob = new Blob([vcfContent], { type: 'text/vcard' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `contacts_${new Date().getTime()}.vcf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.hideProgress();
            this.showSuccess(`Arquivo VCF gerado com ${validContacts.length} contatos`);

        } catch (error) {
            this.hideProgress();
            this.showError('Erro ao gerar arquivo VCF: ' + error.message);
        }
    }

    downloadSingleVCF(index) {
        const contact = this.processedContacts[index];
        if (!contact || contact.status === 'invalid') return;

        const vcfContent = VCFGenerator.generateSingle(contact);
        const blob = new Blob([vcfContent], { type: 'text/vcard' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `${contact.name.replace(/[^a-zA-Z0-9]/g, '_')}.vcf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // WhatsApp Cloud API
    async sendMessages() {
        const credentials = this.getApiCredentials();
        if (!this.validateCredentials(credentials)) {
            return;
        }

        const validContacts = this.processedContacts.filter(c => c.status !== 'invalid');
        if (validContacts.length === 0) {
            this.showError('Nenhum contato válido para enviar mensagens');
            return;
        }

        const messageTemplate = this.messageTemplate.value;
        if (!messageTemplate.trim() && !credentials.templateName) {
            this.showError('Por favor, insira um modelo de mensagem ou um nome de template aprovado.');
            return;
        }

        this.showProgress('Enviando Mensagens', `Iniciando envio para ${validContacts.length} contatos...`);

        try {
            const results = await WhatsAppAPI.sendBatch({
                contacts: validContacts,
                message: messageTemplate,
                credentials: credentials,
                onProgress: (progress) => {
                    this.updateProgress(progress.current, progress.total, progress.message);
                }
            });

            this.hideProgress();
            
            const successCount = results.success;
            const failedCount = results.failed;

            this.showSuccess(`Envio concluído. Sucesso: ${successCount}, Falha: ${failedCount}`);

        } catch (error) {
            this.hideProgress();
            this.showError('Erro ao enviar mensagens: ' + error.message);
        }
    }

    getApiCredentials() {
        return {
            accessToken: this.accessToken.value,
            phoneNumberId: this.phoneNumberId.value,
            templateName: this.templateName.value || '',
            languageCode: this.languageCode.value || 'pt_BR'
        };
    }

    validateCredentials(credentials) {
        if (!credentials.accessToken) {
            this.showError('Por favor, insira seu token de acesso da API do WhatsApp Business');
            return false;
        }
        if (!credentials.phoneNumberId) {
            this.showError('Por favor, insira o ID do seu número de telefone');
            return false;
        }
        return true;
    }

    // State Management
    saveApiConfig() {
        const config = this.getApiCredentials();
        sessionStorage.setItem('whatsapp_api_config', JSON.stringify(config));
    }

    loadSavedState() {
        // Load API config from sessionStorage
        const savedConfig = sessionStorage.getItem('whatsapp_api_config');
        if (savedConfig) {
            try {
                const config = JSON.parse(savedConfig);
                this.accessToken.value = config.accessToken || '';
                this.phoneNumberId.value = config.phoneNumberId || '';
                this.templateName.value = config.templateName || '';
                this.languageCode.value = config.languageCode || 'pt_BR';
            } catch (error) {
                console.error('Erro ao carregar configuração salva:', error);
            }
        }

        // Load mode from localStorage
        const savedMode = localStorage.getItem('whatsapp_mode');
        if (savedMode) {
            this.modeToggle.value = savedMode;
            this.mode = savedMode;
        }
    }

    // Modal Management
    showModal(modalId) {
        document.getElementById(modalId).classList.remove('hidden');
    }

    hideModal(modalId) {
        document.getElementById(modalId).classList.add('hidden');
    }

    // Progress Management
    showProgress(title, message) {
        document.getElementById('progressTitle').textContent = title;
        document.getElementById('progressText').textContent = message;
        document.getElementById('progressCount').textContent = `0/${this.processedContacts.length}`;
        document.getElementById('progressBar').style.width = `0%`;
        this.showModal('progressModal');
    }

    updateProgress(current, total, message) {
        const percentage = Math.round((current / total) * 100);
        document.getElementById('progressCount').textContent = `${current}/${total}`;
        document.getElementById('progressBar').style.width = `${percentage}%`;
        if (message) {
            document.getElementById('progressText').textContent = message;
        }
    }

    hideProgress() {
        this.hideModal('progressModal');
    }

    // Utility Methods
    showError(message) {
        this.showToast(message, 'error');
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            type === 'error' ? 'bg-red-600 text-white' : 'bg-green-600 text-white'
        }`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 5000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Excel Parser Module
class ExcelParser {
    static async parse(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                try {
                    const data = new Uint8Array(e.target.result);
                    // Força a leitura de datas como texto
                    const workbook = XLSX.read(data, { type: 'array', cellDates: false }); 
                    const sheetName = workbook.SheetNames[0];
                    // Mantém os tipos de dados originais (raw) para evitar corrompimento
                    const worksheet = workbook.Sheets[sheetName]; 
                    // Transforma para JSON, usando a primeira linha como cabeçalho
                    const json = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
                    
                    if (json.length < 2) {
                        reject(new Error('O arquivo deve conter pelo menos uma linha de cabeçalho e uma linha de dados'));
                        return;
                    }
                    
                    const headers = json[0].map(h => h ? h.toString().trim() : 'Coluna_Vazia');
                    const contacts = json.slice(1).map(row => {
                        const contact = {};
                        headers.forEach((header, index) => {
                            // Converte todo o conteúdo da célula para string para consistência
                            contact[header] = row[index] !== undefined && row[index] !== null ? row[index].toString().trim() : '';
                        });
                        return contact;
                    });
                    
                    resolve(contacts);
                } catch (error) {
                    reject(error);
                }
            };
            
            reader.onerror = () => reject(new Error('Falha ao ler o arquivo'));
            reader.readAsArrayBuffer(file);
        });
    }
}

// Number Cleaner Module
class NumberCleaner {
    // Tenta limpar e formatar para E.164, assumindo +55 para o Brasil por padrão
    static clean(number, defaultCountryCode = '55') {
        if (!number) return '';
        
        // 1. Remove tudo que não for dígito, incluindo espaços e pontuações
        const digits = number.toString().replace(/\D/g, '');
        
        // Se o número começar com 0, removê-lo (comum em DDD/DDI)
        let processedDigits = digits.startsWith('0') ? digits.substring(1) : digits;
        
        const countryCode = defaultCountryCode;

        // 2. Verifica se o número JÁ está no formato internacional (começa com DDI)
        if (processedDigits.length >= 10 && processedDigits.length <= 15 && processedDigits.startsWith(countryCode)) {
             // Já tem DDI, apenas garante o prefixo '+'
             return `+${processedDigits}`;
        }
        
        // 3. Formato Brasileiro (10 ou 11 dígitos sem DDI)
        if (countryCode === '55') {
            
            // 11 dígitos: (DDD) 9XXXX-XXXX (comum em SP, RJ)
            if (processedDigits.length === 11 && (processedDigits.startsWith('11') || processedDigits.startsWith('21'))) {
                return `+${countryCode}${processedDigits}`;
            }
            
            // 10 dígitos: (DDD) XXXX-XXXX (fixo, ou móvel mais antigo sem o 9)
            if (processedDigits.length === 10) {
                 // Adiciona 9 após o DDD se for um número móvel. Essa é uma heurística arriscada,
                 // mas comum em listas antigas no Brasil. 
                 // Melhor adicionar DDI + 9, assumindo que é móvel.
                 const ddd = processedDigits.substring(0, 2);
                 const numberPart = processedDigits.substring(2);
                 return `+${countryCode}${ddd}9${numberPart}`;
            }

            // 11 dígitos: (DDI) DDI+DDD+NUMERO (já formatado com 55)
            if (processedDigits.length === 13 && processedDigits.startsWith('55')) {
                return `+${processedDigits}`;
            }

        } else if (processedDigits.length >= 10 && processedDigits.length <= 15) {
            // Outros países: Se o comprimento for razoável, adiciona o DDI padrão
            return `+${countryCode}${processedDigits}`;
        }
        
        return ''; // Número inválido ou não detectável
    }
}

// VCF Generator Module
class VCFGenerator {
    static generate(contacts) {
        // Filtra contatos com telefone limpo
        const vcards = contacts
            .filter(c => c.cleanedPhone && c.cleanedPhone.startsWith('+'))
            .map(contact => this.generateSingle(contact));
            
        // Adiciona cabeçalho e rodapé VCF. Note que 'BEGIN' e 'END' já estão em generateSingle.
        // Apenas junta as vcards.
        return vcards.join('\n');
    }

    static generateSingle(contact) {
        const name = contact.name || 'Unknown';
        const phone = contact.cleanedPhone || '';
        
        // O vCard requer N e FN
        return `BEGIN:VCARD
VERSION:3.0
FN:${name}
N:${name};;;;
TEL;TYPE=CELL:${phone}
END:VCARD`;
    }
}

// WhatsApp API Module
class WhatsAppAPI {
    // Implementação de alto nível para enviar lotes, usando o backend Render para processamento
    static async sendBatch({ contacts, message, credentials, onProgress }) {
        // Envia todos os dados para o backend para que ele inicie o trabalho assíncrono
        const payload = {
            contacts: contacts,
            message: message,
            credentials: credentials
        };

        try {
            // 1. Inicia o Job de envio
            const response = await fetch(`${API_BASE_URL}/api/send-whatsapp-batch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.status === 429) {
                throw new Error('Limite de taxa excedido. Tente novamente mais tarde.');
            }
            if (!response.ok) {
                 const errorData = await response.json();
                 throw new Error(`Falha ao iniciar o trabalho de envio: ${errorData.detail || 'Erro desconhecido.'}`);
            }
            
            const jobData = await response.json();
            const jobId = jobData.jobId;
            const totalContacts = jobData.totalContacts;
            
            // 2. Inicia o Polling para o status do job
            let status = 'processing';
            let totalSent = 0;
            let totalFailed = 0;
            let results = [];

            while (status === 'processing') {
                // Espera 3 segundos antes do próximo poll (reduz o load no Redis e no servidor)
                await new Promise(resolve => setTimeout(resolve, 3000));
                
                const statusResponse = await fetch(`${API_BASE_URL}/api/job-status/${jobId}`);
                
                // Trata erro 503 (Serviço indisponível, ex: Redis não configurado)
                if (statusResponse.status === 503) {
                     throw new Error('Job tracking (rastreamento de trabalho) indisponível. Verifique a configuração do Redis no backend.');
                }

                if (!statusResponse.ok) {
                     // Tenta mais uma vez antes de falhar
                     await new Promise(resolve => setTimeout(resolve, 1000));
                     const statusResponseRetry = await fetch(`${API_BASE_URL}/api/job-status/${jobId}`);
                     if (!statusResponseRetry.ok) {
                         const errorDetail = await statusResponseRetry.json().catch(() => ({ detail: 'Erro de rede desconhecido' }));
                         throw new Error(`Falha ao obter o status do trabalho: ${errorDetail.detail}`);
                     }
                     
                     // Atualiza os dados do status se o retry funcionar
                     const statusData = await statusResponseRetry.json();
                     status = statusData.status;
                     totalSent = statusData.completed || 0;
                     totalFailed = statusData.failed || 0;
                     results = statusData.results || [];
                } else {
                    const statusData = await statusResponse.json();
                    status = statusData.status;
                    totalSent = statusData.completed || 0;
                    totalFailed = statusData.failed || 0;
                    results = statusData.results || [];
                }
                
                if (onProgress) {
                    onProgress({
                        current: totalSent + totalFailed,
                        total: totalContacts,
                        message: `Processados: ${totalSent} com sucesso, ${totalFailed} com falha.`
                    });
                }
            }
            
            // 3. Retorna o resultado final
            return {
                total: totalContacts,
                success: totalSent,
                failed: totalFailed,
                results: results
            };

        } catch (error) {
            console.error('API Error during batch send:', error);
            throw error;
        }
    }
}

// Adiciona a biblioteca marked para renderização de markdown no chat
document.write('<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/4.0.12/marked.min.js"></script>');

// Initialize Application
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new WhatsAppBulkManager();
});
