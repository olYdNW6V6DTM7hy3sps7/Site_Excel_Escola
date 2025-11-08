WhatsApp Bulk Contact Manager & Messenger

Um aplicativo web focado em privacidade para importação em massa de contatos de arquivos Excel/CSV e envio de mensagens personalizadas do WhatsApp através de dois caminhos distintos: geração de arquivo VCF e mensagens diretas via Cloud API. O site também inclui um Chatbot de AI para assistência em tempo real.

Funcionalidades

🎯 Funcionalidade Central

Carregamento de Arquivos: Suporte para arquivos Excel (.xlsx, .xls) e CSV

Detecção de Colunas com AI: Mapeamento automático (ou manual) das colunas de nome e telefone, utilizando a AI DeepSeek R1T2 via OpenRouter.

Limpeza de Número de Telefone: Validação do formato E.164 com suporte a formato brasileiro.

Geração VCF: Criação de arquivos de contato para importação em telefone.

WhatsApp Cloud API: Envio direto de mensagens via Business API, com processamento em lote no backend.

Chatbot de AI Integrado: Um assistente, o "Ajudante Geral a AI que pensa por você", para ajudar a entender a estrutura dos dados carregados e as funcionalidades do site.

Privacidade em Primeiro Lugar: Todo o processamento de dados confidenciais ocorre no lado do cliente (navegador), sem armazenamento de dados de contato nos nossos servidores.

🔧 Dois Modos de Operação

Modo Geração VCF:

Gera arquivos vCard para importação de contatos em massa.

Baixe e importe para o aplicativo de contatos do telefone.

Modo Cloud API:

Envia mensagens diretamente via WhatsApp Business API (requer credenciais).

Rastreamento de progresso em tempo real (requer Redis configurado no backend).

Configuração Rápida

1. Usando a Aplicação Web

Carregue Seu Arquivo: Arraste e solte o arquivo Excel ou CSV.

Mapeie as Colunas: Use a detecção por AI ou mapeamento manual.

Consulte a AI: Use o Chatbot integrado (ícone de robô roxo no canto inferior direito) para tirar dúvidas sobre seus dados ou o site.

Configure a Mensagem: Crie um modelo de mensagem com placeholders.

Escolha o Modo: VCF (download) ou API (envio).

Processe Contatos: Baixe o VCF ou envie as mensagens.

2. Configurando as Variáveis de Ambiente do Servidor (Proxy Backend)

O servidor proxy (FastAPI) usa variáveis de ambiente cruciais, especialmente para a funcionalidade de AI.

Variável

Descrição

Obrigatório para...

OPENROUTER_API_KEY

Sua chave de API do OpenRouter para acessar o modelo DeepSeek R1T2.

Chatbot AI e Detecção de Colunas AI.

RATE_LIMIT_REDIS_URL

URL de conexão Redis (Ex: redis://localhost:6379).

Rastreamento de Status do Job e Limitação de Taxa (Muito recomendado).

CORS_ALLOWED_ORIGINS

Lista separada por vírgulas dos domínios que podem acessar a API (Ex: *, https://seu-app-render.onrender.com).

Acesso do Frontend.

3. Configurando o Deploy no Render

Para configurar o Render com sucesso, assumindo que todos os arquivos (index.html, main.js, proxy_server.py, requirements.txt etc.) estão soltos na raiz do seu repositório GitHub, siga estes passos:

A. Criação do Serviço Web

Tipo de Serviço: Escolha "Web Service" (Serviço Web).

Repositório: Conecte-se ao seu repositório GitHub.

Ambiente: Selecione Python 3.

Região: Escolha a região mais próxima de você ou do seu público.

B. Comandos de Build e Início

Comando de Build (Build Command): Instala as dependências listadas no requirements.txt.

pip install -r requirements.txt



Comando de Início (Start Command): Inicia o servidor FastAPI usando Uvicorn, vinculando-o ao host e porta exigidos pelo Render.

uvicorn proxy_server:app --host 0.0.0.0 --port $PORT



C. Variáveis de Ambiente (Configuração Essencial)

Você deve adicionar suas variáveis de ambiente na seção "Environment Variables" do Render.

Chave

Valor

Tipo

OPENROUTER_API_KEY

Sua chave de API do OpenRouter (Valor Secreto)

Secreto

CORS_ALLOWED_ORIGINS

O URL final do seu aplicativo Render (Ex: https://nome-do-seu-app.onrender.com)

Padrão

PYTHONUNBUFFERED

1 (Opcional, mas recomendado para logs)

Padrão

Observação sobre o Redis: Se você configurar o RATE_LIMIT_REDIS_URL no Render, precisará criar um serviço Redis separado para apontar para ele, o que é altamente recomendado para a estabilidade e rastreamento do job em lote.

Desenvolvimento

Arquitetura Frontend

Framework: JavaScript Puro (ES2020+)

Estilização: Tailwind CSS

Chatbot: Chamadas ao endpoint /api/chat no backend.

Arquitetura Backend

Framework: FastAPI (Python)

AI Integration: DeepSeek R1T2 (via OpenRouter e httpx para /api/chat e /api/detect-columns).

Rastreamento de Job: Redis (opcional, para /api/job-status).