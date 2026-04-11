# Runbook Operacional — [Nome do Workflow]

> **Instância n8n:** https://n8n.eufacoseu.marketing/
> **Workflow ID:** `<id>`
> **Versão:** 1.0
> **Criado em:** YYYY-MM-DD
> **Atualizado em:** YYYY-MM-DD
> **Responsável:** [Nome / Equipe]

---

## 1. Propósito

<!-- O que este workflow faz e por que existe? -->
<!-- Ex: Toda segunda-feira às 9h, busca novos leads no Google Sheets, enriquece com HubSpot e envia email de boas-vindas. -->

**Objetivo de negócio:**

**Resultado esperado:**

---

## 2. Trigger

| Campo | Valor |
|-------|-------|
| Tipo | Cron / Webhook / Manual |
| Agendamento | Ex: `0 9 * * 1` (toda segunda às 9h) |
| Timezone | America/Sao_Paulo |
| Concorrência máxima | Ex: 1 (não executa em paralelo) |
| URL do Webhook (se aplicável) | `https://n8n.eufacoseu.marketing/webhook/<path>` |

---

## 3. Contrato de Dados

### Entrada

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `campo_1` | string | sim | Descrição |
| `campo_2` | number | não | Descrição |

**Fonte dos dados:**
<!-- Ex: Google Sheets "Leads EFSM" aba "Novos" -->

### Saída

| Destino | Tipo | Descrição |
|---------|------|-----------|
| Google Sheets | Append row | Registra status de cada lead processado |
| Email | Envio | Email de boas-vindas personalizado |

---

## 4. Idempotência

**Chave de dedup:** `<campo que identifica unicidade>`
<!-- Ex: email do lead, ID do registro, hash do payload -->

**Mecanismo de dedup:** 
<!-- Ex: Coluna "processado" no Google Sheets; se já existe, skip -->

**Comportamento seguro no re-run:**
<!-- Ex: Se registro já existe com status "enviado", ignora e não duplica email -->

---

## 5. Tratamento de Erro e Retry

**Política de retry:**
<!-- Ex: 3 tentativas com backoff: 1s → 2s → 4s -->

| Tentativa | Aguarda | Ação se falhar |
|-----------|---------|----------------|
| 1ª | 0s | Tenta novamente |
| 2ª | 1s | Tenta novamente |
| 3ª | 2s | Move para fila de revisão |

**Notificação de falha:**
<!-- Ex: Slack #automacoes-efsm com mensagem de erro e link para a execução -->

**Fila de revisão humana (HITL):**
<!-- Ex: Google Sheets "Fila de Revisão" aba "n8n-erros" -->

| Campo da fila | Descrição |
|---------------|-----------|
| `run_id` | ID único da execução |
| `timestamp` | Data/hora do erro |
| `workflow_id` | ID do workflow |
| `payload_original` | Dados que causaram o erro |
| `mensagem_erro` | Mensagem de erro do n8n |
| `status` | `pendente` / `aprovado` / `rejeitado` |

---

## 6. Observabilidade e Auditoria

**Run ID:** Gerado no início de cada execução via nó Code
```javascript
const run_id = Date.now() + '-' + Math.random().toString(36).slice(2, 8);
```

**O que é logado por execução:**

| Evento | Onde é armazenado | Campos |
|--------|-------------------|--------|
| Início | Planilha "Log Execuções" | run_id, timestamp, workflow_id |
| Fim com sucesso | Planilha "Log Execuções" | run_id, status, qtd_processados |
| Fim com erro | Planilha "Log Execuções" + Fila | run_id, status, erro, payload |

**Onde ver execuções:**
- n8n UI: https://n8n.eufacoseu.marketing/ → Workflow → Executions
- `python3 scripts/n8n_api.py list-executions --id <workflow-id> --limit 20 --pretty`

---

## 7. Credenciais Necessárias

<!-- Nunca inclua tokens/senhas aqui — apenas nomes das credenciais configuradas no n8n -->

| Credencial | Tipo | Nó(s) que usa | Configurado em |
|------------|------|----------------|----------------|
| `Google Sheets EFSM` | OAuth2 | Buscar Leads, Log Execuções | n8n UI → Credentials |
| `HubSpot EFSM` | API Key | HTTP - HubSpot Enrich | n8n UI → Credentials |
| `Email EFSM SMTP` | SMTP | Enviar Email | n8n UI → Credentials |

---

## 8. Verificações Operacionais

**Contagens e thresholds esperados:**

| Métrica | Esperado | Ação se fora do padrão |
|---------|----------|------------------------|
| Leads processados / execução | 10-500 | Alertar se 0 ou >1000 |
| Taxa de sucesso de emails | >95% | Alertar se <90% |
| Duração da execução | <5 min | Alertar se >10 min |

**Condições de "parar a linha":**
<!-- Ex: Se 0 registros encontrados no Sheets → alertar e não prosseguir -->
<!-- Ex: Se API do HubSpot retornar 429 → parar, aguardar 1h, notificar Slack -->

---

## 9. Arquitetura do Workflow

```
[Trigger] → [Configuração] → [Buscar Dados] → [Validar] → [Processar] → [Saída] → [Log Sucesso]
                                                    ↓ (inválido)          ↓ (erro)
                                             [Log Inválido]        [Retry + Backoff]
                                                                          ↓ (esgotou tentativas)
                                                                  [Fila de Revisão] → [Slack Alerta]
```

**Nós principais:**

| Nó | Tipo | Responsabilidade |
|----|------|-----------------|
| Schedule Mon 9h | scheduleTrigger | Dispara toda segunda às 9h BRT |
| Gerar run_id | code | Gera ID único e timestamp de início |
| Buscar Leads | googleSheets | Lê novos leads da planilha |
| Verificar Dedup | if | Filtra leads já processados |
| HTTP HubSpot | httpRequest | Enriquece dados do lead |
| Gerar Email | code | Personaliza conteúdo do email |
| Enviar Email | emailSend | Envia email de boas-vindas |
| Log Sucesso | googleSheets | Registra resultado na auditoria |
| [ERRO] Retry | wait | Aguarda antes de tentar novamente |
| [ERRO] Fila | googleSheets | Escreve na fila de revisão humana |
| [ERRO] Slack | slack | Notifica equipe no Slack |

---

## 10. Runbook de Operação

### Verificação de saúde
```bash
# Listar execuções recentes
python3 scripts/n8n_api.py list-executions --id <workflow-id> --limit 10 --pretty

# Estatísticas dos últimos 7 dias
python3 scripts/n8n_api.py stats --id <workflow-id> --days 7 --pretty

# Relatório de otimização
python3 scripts/n8n_optimizer.py report --id <workflow-id>
```

### Resposta a falhas

**Falha isolada (1 execução):**
1. Verificar detalhes: `python3 scripts/n8n_api.py get-execution --id <execution-id> --pretty`
2. Identificar nó com falha nos logs
3. Verificar dados na Fila de Revisão
4. Corrigir dados manualmente se necessário
5. Re-executar: `python3 scripts/n8n_api.py execute --id <workflow-id> --data '<payload>'`

**Falhas recorrentes:**
1. Desativar workflow: `python3 scripts/n8n_api.py deactivate --id <workflow-id>`
2. Investigar padrão: `python3 scripts/n8n_optimizer.py analyze --id <workflow-id> --days 7 --pretty`
3. Validar estrutura: `python3 scripts/n8n_tester.py validate --id <workflow-id>`
4. Corrigir e testar: `python3 scripts/n8n_tester.py dry-run --id <workflow-id> --data-file test.json --report`
5. Reativar: `python3 scripts/n8n_api.py activate --id <workflow-id>`

### Atualização do workflow
1. Desativar: `python3 scripts/n8n_api.py deactivate --id <workflow-id>`
2. Modificar e salvar novo `workflow.json`
3. Validar: `python3 scripts/n8n_tester.py validate --file workflow.json --pretty`
4. Atualizar: `python3 scripts/n8n_api.py update --id <workflow-id> --from-file workflow.json`
5. Testar dry-run: `python3 scripts/n8n_tester.py dry-run --id <workflow-id> --data-file test.json --report`
6. Reativar: `python3 scripts/n8n_api.py activate --id <workflow-id>`
7. Atualizar este runbook com as mudanças

---

## 11. Dependências Externas

| Sistema | URL / Referência | Tipo de uso | Contato em caso de problema |
|---------|-----------------|-------------|----------------------------|
| Google Sheets | [Link da planilha] | Leitura/escrita de dados | time@efsm.com.br |
| HubSpot | api.hubapi.com | Enriquecimento de leads | time@efsm.com.br |
| Servidor de Email | SMTP config | Envio de emails | time@efsm.com.br |

---

## 12. Changelog

| Data | Versão | Autor | Mudança |
|------|--------|-------|---------|
| YYYY-MM-DD | 1.0 | [Nome] | Criação inicial |
