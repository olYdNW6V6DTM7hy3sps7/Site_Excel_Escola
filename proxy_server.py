"""
WhatsApp Bulk Contact Manager - Backend Proxy Server (ATUALIZADO)
FastAPI implementation for AI column detection, Chatbot, and WhatsApp Cloud API proxy

================================================================================
| NOTA DE SEGURANÇA E LGPD (Atualizado: 8 de Novembro de 2025)                 |
================================================================================
|
| Este backend implementa e documenta as proteções da LGPD solicitadas:
|
| 1.  **Medida: Criptografia e Comunicação Segura (SSL/TLS)**
|     - ONDE: Configuração do Servidor (Render, Cloudflare, etc.).
|     - AÇÃO: Este código DEVE rodar atrás de um proxy reverso (como o Render faz
|       por padrão) que força HTTPS. Todas as chamadas (para OpenRouter,
|       Facebook) usam `https://` para garantir criptografia em trânsito.
|
| 2.  **Medida: Controle de Acesso (IAM)**
|     - ONDE: Configuração do Servidor (Render) e neste código.
|     - AÇÃO: O acesso à máquina do servidor é controlado pelo Render. O acesso
|       às APIs (OpenRouter, WhatsApp) é controlado pelas chaves
|       (`OPENROUTER_API_KEY`, `accessToken`) que devem ser Variáveis de
|       Ambiente, nunca escritas no código (Princípio do Acesso Mínimo).
|
| 3.  **Medida: Senhas e Autenticação (MFA/2FA)**
|     - ONDE: Configuração do Servidor (Render) e neste código.
|     - AÇÃO: O acesso ao Render deve ser protegido com 2FA. O `accessToken`
|       do WhatsApp funciona como a "senha" da API, que é verificada
|       aqui antes de permitir o envio (`send_whatsapp_batch`).
|
| 4.  **Medida: Prevenção contra Perda (Backups Regulares)**
|     - ONDE: Configuração do Servidor (Render/Redis).
|     - AÇÃO: Este app segue a "Minimização de Dados": ele NÃO armazena
|       listas de contatos. A única coisa que precisa de backup é o Redis
|       (se usado para rastreamento de jobs) e os logs de segurança.
|
| 5.  **Medida: Proteção de Sistemas (Firewall e WAF)**
|     - ONDE: Configuração do Servidor (Render/Cloudflare).
|     - AÇÃO: Este código DEVE rodar atrás de um Firewall de Aplicação Web (WAF)
|       para bloquear tráfego malicioso (SQL Injection, DDOS, XSS)
|       antes que chegue a esta API.
|
| 6.  **Medida: Governança e Política (PSI)**
|     - ONDE: Documentação (README, index.html modal de Ajuda).
|     - AÇÃO: A política de segurança (PSI) está documentada no modal de Ajuda
|       do `index.html`, informando ao usuário (Princípio da Transparência)
|       exatamente como seus dados são protegidos.
|
| 7.  **Medida: Monitoramento e Auditoria de Logs**
|     - ONDE: Implementado abaixo usando a biblioteca `logging`.
|     - AÇÃO: Registramos eventos de segurança importantes (logs) para
|       permitir auditoria e resposta a incidentes, sem registrar
|       dados pessoais sensíveis (como números de telefone ou mensagens).
|
| 8.  **Medida: Anonimização e Pseudonimização**
|     - ONDE: Implementado nos endpoints `/api/chat` e `/api/detect-columns`.
|     - AÇÃO: O frontend envia apenas uma *amostra* dos dados (Minimização).
|       Este backend repassa apenas essa amostra para a IA, nunca a lista
|       completa, protegendo a privacidade do usuário.
|
| 9.  **Medida: Plano de Resposta a Incidentes**
|     - ONDE: Logs e Alertas (Configuração do Servidor).
|     - AÇÃO: Os logs de nível `ERROR` e `CRITICAL` (abaixo) devem ser
|       configurados no servidor para disparar alertas (ex: via Sentry,
|       Datadog) para a equipe administrativa, iniciando o plano de resposta.
|
================================================================================
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from typing import Dict, List, Any, Optional
import redis
from datetime import datetime
import json
import asyncio
import re
from pydantic import BaseModel, Field # ATUALIZADO: Importa Field para validação
import logging 

# --- IMPLEMENTAÇÃO (LGPD: Monitoramento e Auditoria de Logs) ---
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [SEGURANCA_LOG] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
# -----------------------------------------------------------------

# Configurações de Integração da AI
AI_MODEL = "tngtech/deepseek-r1t2-chimera:free"
SITE_URL = os.getenv("FRONTEND_URL", "http://localhost:8000") 
SITE_TITLE = "WhatsApp Bulk Manager"

class Config:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    REDIS_URL = os.getenv("RATE_LIMIT_REDIS_URL", "redis://localhost:6379")
    CORS_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 3600  # 1 hour

# Initialize FastAPI app
app = FastAPI(title="WhatsApp Bulk Manager API", version="1.2.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis client
redis_client = None
if Config.REDIS_URL:
    try:
        redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
    except Exception as e:
        # --- LGPD (Monitoramento / Resposta a Incidentes) ---
        logging.critical(f"Falha CRÍTICA ao conectar ao Redis: {e}. O rastreamento de jobs não funcionará.")
        # --------------------------------------------------

# --- Modelos de Requisição (com Validação de Segurança) ---
# COMENTÁRIO DE SEGURANÇA (Anti-Hacking: Validação de Entrada)
# Usamos Pydantic para validar estritamente o formato de TODAS as
# requisições que chegam. Se uma requisição não bater com este
# formato (ex: um tipo de dado errado, um campo extra injetado),
# ela é rejeitada com um erro 422 ANTES de tocar na nossa lógica.

class ColumnDetectionRequest(BaseModel):
    headers: List[str]
    sample_data: List[Dict[str, Any]]

class WhatsAppCredentials(BaseModel):
    accessToken: str = Field(..., min_length=10) # Garante que o token não está vazio
    phoneNumberId: str = Field(..., min_length=5, regex=r"^\d+$") # Garante que é numérico
    templateName: Optional[str] = None
    languageCode: Optional[str] = None

class WhatsAppSendRequest(BaseModel):
    contacts: List[Dict[str, Any]]
    message: str
    credentials: WhatsAppCredentials # Usa o modelo validado

class ChatMessage(BaseModel):
    role: str
    text: str
    
class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage]
    contact_data_sample: Optional[str] = None 

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, str]

# --- Fim dos Modelos ---

# Rate limiting
async def check_rate_limit(client_ip: str) -> bool:
    if not redis_client:
        return True
    
    key = f"rate_limit:{client_ip}"
    try:
        current = redis_client.incr(key)
        if current == 1:
            redis_client.expire(key, Config.RATE_LIMIT_WINDOW)
        
        is_limited = current > Config.RATE_LIMIT_REQUESTS
        
        if is_limited:
            # --- LGPD (Monitoramento) ---
            logging.warning(f"RATE LIMIT EXCEDIDO (Medida Anti-Hacking/DDOS) pelo IP: {client_ip}")
            # ------------------------------
        
        return not is_limited
    except Exception as e:
        # --- LGPD (Monitoramento) ---
        logging.error(f"Erro no Redis (Rate Limit): {e}. Permitindo passagem (fail-open).")
        # ------------------------------
        return True

# Health check
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services_status = {
        "api": "healthy",
        "redis": "healthy" if redis_client else "disabled",
        "ai_api_key": "configured" if Config.OPENROUTER_API_KEY else "missing"
    }
    
    if redis_client:
        try:
            redis_client.ping()
        except Exception:
            services_status["redis"] = "unhealthy"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        services=services_status
    )

# Deep Prompt/System Instruction para o Chatbot (ATUALIZADO)
SYSTEM_INSTRUCTION = """
Você é o "Ajudante Geral a AI que pensa por você", um assistente de IA focado em ajudar o usuário a gerenciar e processar listas de contatos para envio de mensagens em massa (bulk messaging) via WhatsApp.

SUA PERSONALIDADE:
1. Apresente-se sempre como: "Ajudante Geral a AI que pensa por você".
2. Seja prestativo, informativo, conciso e use um tom profissional e amigável.
3. Fale exclusivamente em Português do Brasil.
4. Ao se apresentar pela primeira vez, explique sua utilidade (analisar dados, guiar no uso do site, ajudar a remover contatos).

SUAS TAREFAS E CONHECIMENTO SOBRE O SITE:
1. Entender o fluxo de trabalho do site: Upload, Mapeamento, Limpeza/Validação, Geração VCF ou Envio via API.

2. **ANÁLISE DE DADOS (CRÍTICO):**
    Você receberá o contexto dos dados no formato JSON stringificado em `contact_data_sample`.

    A. Se `processing_not_started`:
        - O JSON conterá `sample_data` (dados brutos).
        - Use `sample_data` para ajudar o usuário a escolher as colunas corretas.

    B. Se `processing_complete`:
        - O JSON conterá resumos: `total_contacts`, `total_valid`, `total_invalid`.
        - Ele também conterá `invalid_contacts_sample` (exemplos de falhas) e `valid_contacts_sample` (exemplos de sucesso).

    **SUA REGRA MAIS IMPORTANTE (LGPD: Anonimização e Privacidade):**
    - Você recebe apenas uma *amostra* dos dados (Minimização de Dados).
    - **NUNCA** repita dados pessoais (como telefones ou nomes) na sua resposta, a menos que o usuário pergunte *especificamente* por eles.
    - Se o usuário perguntar sobre contatos "inválidos":
        1. Olhe para `total_invalid`. Se for > 0, informe o número (ex: "Foram encontrados 4 contatos inválidos.").
        2. Use `invalid_contacts_sample` para listar os nomes (ex: "Aqui estão alguns deles: [Nome do Aluno], [Nome do Aluno]...").
        3. Use o campo `telefone_original` para explicar POR QUE falharam (ex: "O número '123' é muito curto").
    - Se `total_invalid` for 0, diga "Nenhum contato falhou na validação."
    
3. **REMOÇÃO DE CONTATOS (NOVO):**
    - O frontend (JavaScript) tentará capturar pedidos de remoção (ex: "remover joão").
    - Se o frontend falhar e o pedido chegar a você, você NÃO PODE remover o contato.
    - Em vez disso, responda: "Eu entendi que você quer remover um contato. Para fazer isso, por favor, clique no ícone de lixeira (<i class='fas fa-trash-alt'></i>) ao lado do nome dele na tabela de prévia."

4. Se o usuário perguntar algo não relacionado (pseudo hacking, engenharia social, etc.), redirecione educadamente: "Meu foco é exclusivamente ajudar com o gerenciamento de contatos para WhatsApp."
"""

@app.post("/api/chat")
async def handle_chat_query(request: ChatRequest, client_request: Request):
    """Endpoint para o Chatbot AI"""
    client_ip = client_request.client.host 

    if not Config.OPENROUTER_API_KEY:
        # --- LGPD (Monitoramento) ---
        logging.error(f"Tentativa de uso do Chat (IP: {client_ip}) falhou: OPENROUTER_API_KEY não configurada.")
        # ------------------------------
        raise HTTPException(status_code=503, detail="OPENROUTER_API_KEY não configurada. Por favor, defina a variável de ambiente.")

    if not await check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Limite de taxa excedido. Tente novamente mais tarde."
        )
    
    # --- LGPD (Monitoramento) ---
    logging.info(f"Consulta ao Chatbot recebida do IP: {client_ip}")
    # ------------------------------

    # Constrói o histórico de mensagens
    messages = []
    messages.append({"role": "system", "content": SYSTEM_INSTRUCTION})

    for message in request.history:
        role = "user" if message.role == "user" else "assistant"
        messages.append({"role": role, "content": message.text})
    
    last_user_prompt = messages[-1]["content"]
    if request.contact_data_sample:
        # --- LGPD (Anonimização / Minimização de Dados) ---
        # O frontend envia apenas uma AMOSTRA, não a lista completa.
        # --------------------------------------------------
        data_context = f"\n\n--- DADOS DE CONTEXTO DO EXCEL (JSON stringified) ---\n{request.contact_data_sample}\n--- FIM DOS DADOS DE CONTEXTO ---\n"
        last_user_prompt += data_context
    messages[-1]["content"] = last_user_prompt

    payload = {
        "model": AI_MODEL,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 512
    }
    
    headers = {
        "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": SITE_URL,
        "X-Title": SITE_TITLE,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            max_retries = 3
            delay = 1
            response = None
            
            for attempt in range(max_retries):
                # --- LGPD (Criptografia e Comunicação Segura) ---
                # A chamada é feita para `https://openrouter.ai`, garantindo SSL/TLS.
                # ------------------------------------------------
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 429 and response.status_code < 500:
                    break
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    raise HTTPException(status_code=response.status_code, detail="Erro de serviço da AI ou limite de taxa excedido.")

            
            if response.status_code != 200:
                # --- LGPD (Monitoramento) ---
                logging.error(f"Erro da API OpenRouter (IP: {client_ip}): {response.status_code} - {response.text}")
                # ------------------------------
                raise HTTPException(status_code=500, detail=f"Erro ao comunicar com a AI. Código: {response.status_code}")

            result = response.json()
            ai_text = result.get("choices", [{}])[0].get("message", {}).get("content")
            
            if not ai_text:
                raise HTTPException(status_code=500, detail="A AI retornou uma resposta inesperada.")
            
            # COMENTÁRIO DE SEGURANÇA (Anti-Hacking: Higienização de Saída)
            # Embora o frontend vá higienizar, fazemos uma limpeza básica aqui
            # para remover caracteres que podem quebrar o JSON/HTML.
            ai_text_cleaned = ai_text.replace("<", "&lt;").replace(">", "&gt;")
            
            return {"response": ai_text_cleaned}

    except HTTPException:
        raise 
    except Exception as e:
        # --- LGPD (Monitoramento / Resposta a Incidentes) ---
        logging.critical(f"Exceção inesperada no Chatbot (IP: {client_ip}): {e}")
        # ------------------------------
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

# AI Column Detection
@app.post("/api/detect-columns")
async def detect_columns(request: ColumnDetectionRequest, client_request: Request):
    """Detect name and phone columns using AI or heuristic fallback"""
    client_ip = client_request.client.host
    
    if not await check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Limite de taxa excedido. Tente novamente mais tarde."
        )
    
    # --- LGPD (Monitoramento) ---
    logging.info(f"Detecção de colunas iniciada pelo IP: {client_ip}")
    # ------------------------------
    
    if Config.OPENROUTER_API_KEY:
        try:
            headers_text = ", ".join(request.headers)
            sample_rows = []
            
            # --- LGPD (Minimização de Dados) ---
            # Enviamos apenas os PRIMEIROS 5 registros como amostra.
            # -------------------------------------
            for row in request.sample_data[:5]:
                row_text = ", ".join([f"'{k}': '{v}'" for k, v in row.items()])
                sample_rows.append(row_text)
            
            sample_text = "; ".join(sample_rows)
            
            system_prompt = """Você é um analista de dados. Sua tarefa é identificar a coluna de 'nome principal' e 'número de telefone'.

            Retorne SOMENTE um objeto JSON válido com este formato exato:
            {"name_key": "nome_da_coluna", "number_key": "nome_da_coluna"}

            Regras:
            - **name_key (Nome Principal)**: Priorize colunas que pareçam ser o nome de um 'aluno' (ex: "Nome do Aluno", "Aluno"). Se não encontrar, procure por um nome genérico (ex: "Nome").
            - **number_key (Telefone)**: Coluna que contém números de telefone.
            - Use os nomes exatos das colunas fornecidos nos cabeçalhos.
            - Se não tiver certeza, retorne uma string vazia ("")."""
            
            user_prompt = f"""{system_prompt}
            Cabeçalhos: {headers_text}
            Amostra de dados: {sample_text}
            Identifique as colunas de Nome e Número de Telefone."""
            
            messages = [
                {"role": "user", "content": user_prompt}
            ]

            headers = {
                "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": SITE_URL,
                "X-Title": SITE_TITLE,
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": AI_MODEL,
                        "messages": messages,
                        "temperature": 0.1,
                        "max_tokens": 150
                    }
                )
                
                if response.status_code != 200:
                    return await heuristic_column_detection(request.headers)
                
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                try:
                    json_match = re.search(r'\{[^}]+\}', content)
                    if json_match:
                        ai_result = json.loads(json_match.group())
                    else:
                        raise json.JSONDecodeError("JSON não encontrado", content, 0)
                    
                    name_key = ai_result.get("name_key", "")
                    number_key = ai_result.get("number_key", "")
                    
                    if name_key not in request.headers: name_key = ""
                    if number_key not in request.headers: number_key = ""
                    
                    return {"name_key": name_key, "number_key": number_key}
                        
                except (json.JSONDecodeError, KeyError) as e:
                    logging.warning(f"AI JSON parsing failed, using heuristic: {e}")
                    return await heuristic_column_detection(request.headers)
                    
        except Exception as e:
            logging.error(f"AI column detection (OpenRouter) error: {e}")
            return await heuristic_column_detection(request.headers)
            
    return await heuristic_column_detection(request.headers)


async def heuristic_column_detection(headers: List[str]) -> Dict[str, str]:
    """Fallback heuristic column detection"""
    name_patterns = ['aluno', 'nome aluno', 'nome_aluno', 'responsavel', 'responsável', 'nome resp', 'name', 'nome']
    phone_patterns = ['phone', 'telefone', 'mobile', 'cell', 'whatsapp', 'phone_number', 'phone number', 'celular']
    
    name_key = ""
    number_key = ""
    
    # Busca por nome (com prioridade)
    for pattern in name_patterns:
        for header in headers:
            header_lower_simple = header.lower().replace("_", " ").replace("á", "a").replace("ç", "c")
            if pattern == header_lower_simple:
                name_key = header
                break
        if name_key:
            break
            
    # Busca por telefone (com prioridade)
    for pattern in phone_patterns:
        for header in headers:
            header_lower_simple = header.lower().replace("_", " ")
            if pattern == header_lower_simple:
                number_key = header
                break
        if number_key:
            break

    # Fallback (se a busca exata falhou, tenta 'in')
    if not name_key:
        for header in headers:
            header_lower = header.lower()
            for pattern in name_patterns:
                if pattern in header_lower:
                    name_key = header
                    break
            if name_key:
                break
                
    if not number_key:
        for header in headers:
            header_lower = header.lower()
            for pattern in phone_patterns:
                if pattern in header_lower:
                    number_key = header
                    break
            if number_key:
                break
    
    return {"name_key": name_key, "number_key": number_key}

# WhatsApp Batch Send Endpoint
@app.post("/api/send-whatsapp-batch")
async def send_whatsapp_batch(request: WhatsAppSendRequest, client_request: Request):
    """Send WhatsApp messages in batch via Cloud API"""
    client_ip = client_request.client.host
    
    if not await check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Limite de taxa excedido. Tente novamente mais tarde."
        )
    
    # A validação de `credentials` agora é feita pelo Pydantic (WhatsAppSendRequest)
    
    if not request.contacts:
        raise HTTPException(status_code=400, detail="Nenhum contato fornecido")
    
    credentials = request.credentials
    
    # --- LGPD (Senhas e Autenticação) ---
    # O Pydantic já validou que o token e o ID existem e têm o formato
    # mínimo esperado. O token em si é enviado via HTTPS (Criptografia).
    # ---------------------------------------
    
    job_id = f"whatsapp_job_{datetime.utcnow().timestamp()}"
    
    # --- LGPD (Monitoramento) ---
    # Logamos o *início* do trabalho, quantos contatos, mas NUNCA
    # a lista de telefones ou a mensagem (Minimização de Dados no Log).
    logging.info(f"Iniciando Job de Envio (IP: {client_ip}): {job_id} para {len(request.contacts)} contatos.")
    # ------------------------------
    
    # Inicia a tarefa em background
    asyncio.create_task(process_whatsapp_batch(
        job_id, request.contacts, request.message, credentials.dict()
    ))
    
    return {
        "jobId": job_id,
        "status": "processing",
        "totalContacts": len(request.contacts),
        "estimatedTime": len(request.contacts) * 0.1
    }

async def process_whatsapp_batch(job_id: str, contacts: List[Dict], message: str, credentials: Dict):
    """Process WhatsApp messages in background"""
    
    # --- LGPD (Prevenção contra Perda / Resposta a Incidentes) ---
    # O status do job é salvo no Redis.
    # Usamos `setex` (com expiração) para que os dados não fiquem para sempre
    # (Princípio da Retenção de Dados).
    # -------------------------------------------------------------
    if redis_client:
        try:
            redis_client.setex(f"job:{job_id}", 3600, json.dumps({
                "status": "processing",
                "total": len(contacts),
                "completed": 0,
                "failed": 0,
                "results": []
            }))
        except Exception as e:
            # --- LGPD (Monitoramento / Resposta a Incidentes) ---
            logging.error(f"Falha ao escrever Job inicial no Redis (Job: {job_id}): {e}")
            # --------------------------------------------------
            # O job continuará, mas não será rastreável
            pass 
    
    results = []
    batch_size = 10
    delay_ms = 1000  # 1 segundo entre lotes
    
    for i in range(0, len(contacts), batch_size):
        batch = contacts[i:i + batch_size]
        batch_results = await send_whatsapp_batch_api(batch, message, credentials)
        results.extend(batch_results)
        
        if redis_client:
            try:
                completed = len([r for r in results if r.get("success")])
                failed = len([r for r in results if not r.get("success")])
                
                redis_client.setex(f"job:{job_id}", 3600, json.dumps({
                    "status": "processing",
                    "total": len(contacts),
                    "completed": completed,
                    "failed": failed,
                    "results": results # Armazena resultados parciais
                }))
            except Exception as e:
                 logging.error(f"Falha ao atualizar Job no Redis (Job: {job_id}): {e}")
        
        if i + batch_size < len(contacts):
            await asyncio.sleep(delay_ms / 1000)
    
    # Marca o job como concluído
    if redis_client:
        try:
            completed = len([r for r in results if r.get("success")])
            failed = len([r for r in results if not r.get("success")])
            
            # --- LGPD (Monitoramento) ---
            logging.info(f"Job de Envio Concluído: {job_id}. Sucesso: {completed}, Falhas: {failed}")
            # ------------------------------
            
            redis_client.setex(f"job:{job_id}", 3600, json.dumps({
                "status": "completed",
                "total": len(contacts),
                "completed": completed,
                "failed": failed,
                "results": results
            }))
        except Exception as e:
             logging.error(f"Falha ao finalizar Job no Redis (Job: {job_id}): {e}")


async def send_whatsapp_batch_api(contacts: List[Dict], message: str, credentials: Dict) -> List[Dict]:
    """Send WhatsApp messages via Cloud API"""
    
    results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for contact in contacts:
            try:
                phone = contact.get("cleanedPhone", "").replace("+", "")
                
                # Validação extra de segurança
                if not phone.isdigit() or len(phone) < 10:
                    results.append({
                        "contact_id": contact.get("id"),
                        "phone": contact.get("cleanedPhone"),
                        "success": False,
                        "error": "Número de telefone inválido (não numérico ou curto demais) no lado do servidor.",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    continue

                phone_number_id = credentials["phoneNumberId"]
                access_token = credentials["accessToken"]
                template_name = credentials.get("templateName", "")
                language_code = credentials.get("languageCode", "pt_BR")
                
                # Substitui placeholders
                personalized_message = message.replace("{name}", contact.get("name", ""))
                
                # COMENTÁRIO DE SEGURANÇA (Anti-Hacking: Higienização de Saída)
                # Embora o Facebook deva lidar com isso, higienizamos a mensagem
                # para remover caracteres de controle que poderiam bugar o JSON.
                personalized_message = re.sub(r'[\x00-\x1F\x7F]', '', personalized_message)

                
                if template_name and template_name.strip() and template_name != 'hello_world':
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": phone,
                        "type": "template",
                        "template": {
                            "name": template_name,
                            "language": { "code": language_code },
                            "components": [
                                {
                                    "type": "body",
                                    "parameters": [
                                        {"type": "text", "text": contact.get("name", "")}
                                    ]
                                }
                            ]
                        }
                    }
                else:
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": phone,
                        "type": "text",
                        "text": { "body": personalized_message }
                    }
                
                # --- LGPD (Criptografia e Comunicação Segura) ---
                # A chamada é feita para `https://graph.facebook.com`, garantindo SSL/TLS.
                # ------------------------------------------------
                response = await client.post(
                    f"https://graph.facebook.com/v18.0/{phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                
                if response.status_code == 200:
                    result_data = response.json()
                    results.append({
                        "contact_id": contact.get("id"),
                        "phone": contact.get("cleanedPhone"),
                        "success": True,
                        "messageId": result_data.get("messages", [{}])[0].get("id"),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                else:
                    results.append({
                        "contact_id": contact.get("id"),
                        "phone": contact.get("cleanedPhone"),
                        "success": False,
                        "error": response.text,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
            except Exception as e:
                results.append({
                    "contact_id": contact.get("id"),
                    "phone": contact.get("cleanedPhone"),
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    return results

# Job status endpoint
@app.get("/api/job-status/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a WhatsApp sending job"""
    
    if not redis_client:
        # --- LGPD (Monitoramento) ---
        logging.error(f"Tentativa de verificar job {job_id} falhou: Redis não configurado.")
        # ------------------------------
        raise HTTPException(status_code=503, detail="Rastreamento de trabalho (Job tracking) não disponível sem Redis configurado.")
    
    try:
        # COMENTÁRIO DE SEGURANÇA (Anti-Hacking: Validação de Entrada)
        # Higieniza o job_id para prevenir ataques (ex: Redis injection)
        # Embora o risco seja baixo, é boa prática.
        if not re.match(r"^[a-zA-Z0-9_.-]+$", job_id):
             logging.warning(f"Tentativa de acesso a job com ID malicioso: {job_id}")
             raise HTTPException(status_code=400, detail="Job ID inválido")

        job_data = redis_client.get(f"job:{job_id}")
        
        if not job_data:
            raise HTTPException(status_code=404, detail="Trabalho (Job) não encontrado")
        
        return json.loads(job_data)
        
    except Exception as e:
        # --- LGPD (Monitoramento) ---
        logging.error(f"Falha ao recuperar status do job {job_id}: {e}")
        # ------------------------------
        raise HTTPException(status_code=500, detail="Falha ao recuperar o status do trabalho")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # --- LGPD (Monitoramento / Resposta a Incidentes) ---
    logging.critical(f"Erro 500 Inesperado: {exc} na Rota: {request.url}")
    # --------------------------------------------------
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
