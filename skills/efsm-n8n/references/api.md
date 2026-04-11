# Referência da API REST do n8n — EFSM

**Instância:** `https://n8n.eufacoseu.marketing/`
**Base da API:** `https://n8n.eufacoseu.marketing/api/v1/`

---

## Autenticação

Todas as requisições exigem o header:
```
X-N8N-API-KEY: <seu-token>
```

Ou equivalentemente via Bearer:
```
Authorization: Bearer <seu-token>
```

**Como obter o token:** n8n UI → Settings → API → Create API Key

**Regra de segurança:** Nunca exiba o token em outputs, logs ou JSONs de workflow. Use sempre via variável de ambiente `N8N_API_KEY`.

---

## Workflows

### Listar Workflows
```
GET /workflows
```
Query params opcionais:
- `?active=true` — apenas ativos
- `?active=false` — apenas inativos

Resposta:
```json
{
  "data": [
    {
      "id": "abc123",
      "name": "Nutrição de Leads",
      "active": true,
      "createdAt": "2026-01-14T10:00:00.000Z",
      "updatedAt": "2026-04-01T08:00:00.000Z",
      "tags": []
    }
  ]
}
```

### Obter Workflow
```
GET /workflows/{id}
```
Retorna o workflow completo com `nodes`, `connections` e `settings`.

### Criar Workflow
```
POST /workflows
Content-Type: application/json

{
  "name": "Nome do Workflow",
  "nodes": [...],
  "connections": {...},
  "settings": {},
  "active": false
}
```
> Sempre crie com `"active": false`. Ative manualmente após validação.

### Atualizar Workflow
```
PATCH /workflows/{id}
Content-Type: application/json

{ "nodes": [...], "connections": {...} }
```

### Ativar / Desativar
```
PATCH /workflows/{id}
Content-Type: application/json

{ "active": true }   // ativar
{ "active": false }  // desativar
```

### Deletar Workflow
```
DELETE /workflows/{id}
```
> Irreversível. Confirme antes de executar.

---

## Execuções

### Listar Execuções
```
GET /executions
```
Query params opcionais:
- `?workflowId={id}` — filtrar por workflow
- `?limit=20` — quantidade (padrão 20, máx 100)
- `?status=success|error|waiting` — filtrar por status

Resposta:
```json
{
  "data": [
    {
      "id": "exec-456",
      "finished": true,
      "mode": "trigger",
      "status": "success",
      "startedAt": "2026-04-01T09:00:00.000Z",
      "stoppedAt": "2026-04-01T09:00:05.000Z",
      "workflowId": "abc123"
    }
  ]
}
```

### Obter Execução
```
GET /executions/{id}
```
Retorna detalhes completos incluindo dados de cada nó e erros.

### Deletar Execução
```
DELETE /executions/{id}
```

### Executar Workflow Manualmente
```
POST /workflows/{id}/execute
Content-Type: application/json

{ "data": { "chave": "valor" } }
```
Retorna:
```json
{
  "data": { "executionId": "exec-789" }
}
```

---

## Códigos de Status HTTP

| Código | Significado |
|--------|------------|
| 200 | Sucesso |
| 201 | Criado com sucesso |
| 400 | Requisição inválida (verifique o JSON) |
| 401 | Não autorizado — token inválido ou ausente |
| 404 | Recurso não encontrado |
| 409 | Conflito (ex: workflow já ativo) |
| 429 | Rate limit excedido — aguarde antes de tentar |
| 500 | Erro interno do servidor |

---

## Exemplos de uso com curl

### Listar workflows ativos
```bash
curl -s \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "https://n8n.eufacoseu.marketing/api/v1/workflows?active=true" \
  | python3 -m json.tool
```

### Ativar workflow
```bash
curl -s -X PATCH \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"active": true}' \
  "https://n8n.eufacoseu.marketing/api/v1/workflows/abc123"
```

### Executar workflow com dados
```bash
curl -s -X POST \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"data": {"email": "lead@empresa.com", "nome": "João"}}' \
  "https://n8n.eufacoseu.marketing/api/v1/workflows/abc123/execute"
```

### Ver execuções recentes com falha
```bash
curl -s \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "https://n8n.eufacoseu.marketing/api/v1/executions?status=error&limit=10" \
  | python3 -m json.tool
```

---

## Exemplos com scripts Python (recomendado)

```bash
# Listar todos os workflows (formatado)
python3 scripts/n8n_api.py list-workflows --pretty

# Ver detalhes de um workflow
python3 scripts/n8n_api.py get-workflow --id abc123 --pretty

# Criar workflow a partir de arquivo
python3 scripts/n8n_api.py create --from-file meu-workflow.json

# Ativar workflow
python3 scripts/n8n_api.py activate --id abc123

# Executar com dados
python3 scripts/n8n_api.py execute --id abc123 --data '{"email": "teste@efsm.com.br"}'

# Ver estatísticas dos últimos 30 dias
python3 scripts/n8n_api.py stats --id abc123 --days 30 --pretty

# Validar workflow localmente
python3 scripts/n8n_tester.py validate --file workflow.json --pretty

# Dry-run com dados e relatório
python3 scripts/n8n_tester.py dry-run --id abc123 --data-file test-data.json --report

# Relatório de otimização
python3 scripts/n8n_optimizer.py report --id abc123
```

---

## Variáveis de Ambiente

| Variável | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `N8N_API_KEY` | Sim | — | Token de autenticação da API |
| `N8N_BASE_URL` | Não | `https://n8n.eufacoseu.marketing` | URL base da instância |

---

## Referências Externas

- n8n API Docs: https://docs.n8n.io/api/
- n8n Node Types: https://docs.n8n.io/integrations/builtin/
- n8n Community Forum: https://community.n8n.io
- EFSM n8n UI: https://n8n.eufacoseu.marketing/
