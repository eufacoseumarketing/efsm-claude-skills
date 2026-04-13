---
name: efsm-crm
description: Processa o ZIP White Label do CRM fornecedor e gera a versão EFSM pronta para uso. Substitui nome, descrição, IDs e imagens de marca. Use quando receber um novo arquivo WaBaCRM_X.X.XX.zip do fornecedor e precisar gerar o CRMEFSM_X.X.XX.zip com a identidade visual da EFSM.
---

Você é o responsável por processar o pacote White Label do CRM da EFSM. Quando receber um arquivo ZIP do fornecedor, execute o processo completo de personalização e gere o pacote pronto para distribuição.

Esta skill já inclui as imagens oficiais da marca EFSM dentro da pasta `assets/`:
- `assets/icon.png` — asterisco roxo EFSM
- `assets/logo.png` — logo "eu faço seu marketing"
- `assets/plugin_login.png` — tela de login do CRM EFSM

Para localizar o caminho da skill em tempo de execução, use o diretório onde este SKILL.md está localizado como base.

---

## O QUE ESTA SKILL FAZ

Recebe o ZIP White Label do fornecedor (ex: `WaBaCRM_4.3.30.zip`) e produz o ZIP com a identidade EFSM (ex: `CRMEFSM_4.3.30.zip`), realizando:

1. Descompactar o ZIP original em uma pasta temporária
2. Editar `manifest.json` (nome e descrição)
3. Substituir `label/config/utils.json` com os dados da EFSM
4. Substituir as 3 imagens de marca em `label/icons/plugin/` pelas que estão nesta skill
5. Recompactar e renomear com o padrão `CRMEFSM_X.X.XX.zip`
6. Entregar o arquivo para download

---

## IDENTIDADE EFSM — DADOS FIXOS

| Campo | Valor |
|-------|-------|
| **name** | `CRM EFSM: Sua principal ferramenta para vendas!` |
| **description** | `CRM EFSM: Toda conversa é uma oportunidade. Use nosso CRM para transformar leads e vendas` |
| **chromeStoreID** | `crmefsm` |
| **nameID** | `crmefsm` |
| **sigeID** | `5` |
| **language** | `pt` |

---

## PROCESSO COMPLETO

### Passo 1 — Identificar o arquivo de entrada
O usuário fornecerá o caminho do ZIP do fornecedor. O nome segue o padrão `WaBaCRM_X.X.XX.zip`.
Extraia a versão do nome: ex. `WaBaCRM_4.3.30.zip` → versão `4.3.30`.

### Passo 2 — Extrair o ZIP em pasta temporária
```bash
unzip -o "<caminho do zip do fornecedor>" -d /tmp/crm-efsm-work/
```

### Passo 3 — Editar manifest.json
No arquivo `/tmp/crm-efsm-work/manifest.json`, alterar **somente**:
- `"name"` → `"CRM EFSM: Sua principal ferramenta para vendas!"`
- `"description"` → `"CRM EFSM: Toda conversa é uma oportunidade. Use nosso CRM para transformar leads e vendas"`

Todos os outros campos (`key`, `version`, `permissions`, `content_scripts`, etc.) devem permanecer intactos.

### Passo 4 — Substituir label/config/utils.json
Substituir **todo o conteúdo** do arquivo `/tmp/crm-efsm-work/label/config/utils.json` por:
```json
{
    "chromeStoreID": "crmefsm",
    "nameID": "crmefsm",
    "sigeID": "5",
    "language": "pt",
    "name": "CRM EFSM: Sua principal ferramenta para vendas!",
    "descricao": "CRM EFSM: Toda conversa é uma oportunidade. Use nosso CRM para transformar leads e vendas"
}
```

### Passo 5 — Substituir as imagens de marca
As imagens estão na mesma pasta desta skill. Localize o caminho da skill e copie:

```bash
SKILL_DIR="<diretório onde esta skill está instalada>"

cp "$SKILL_DIR/assets/icon.png"         /tmp/crm-efsm-work/label/icons/plugin/icon.png
cp "$SKILL_DIR/assets/logo.png"         /tmp/crm-efsm-work/label/icons/plugin/logo.png
cp "$SKILL_DIR/assets/plugin_login.png" /tmp/crm-efsm-work/label/icons/plugin/plugin_login.png
```

### Passo 6 — Gerar o ZIP final
```bash
cd /tmp/crm-efsm-work
zip -r "/tmp/CRMEFSM_<versão>.zip" . \
  --exclude "*.DS_Store" \
  --exclude "__MACOSX/*" \
  --exclude "*/__MACOSX/*"
```

### Passo 7 — Verificar e entregar
```bash
# Confirmar os textos nos JSONs
unzip -p /tmp/CRMEFSM_<versão>.zip manifest.json
unzip -p /tmp/CRMEFSM_<versão>.zip label/config/utils.json

# Confirmar tamanho
ls -lh /tmp/CRMEFSM_<versão>.zip
```

Após a verificação, informe ao usuário onde o arquivo foi gerado e disponibilize para download.

### Passo 8 — Limpeza
```bash
rm -rf /tmp/crm-efsm-work/
```

---

## CHECKLIST DE VALIDAÇÃO

Antes de entregar, confirme:

- [ ] `manifest.json` → `"name"` é `"CRM EFSM: Sua principal ferramenta para vendas!"`
- [ ] `manifest.json` → `"description"` contém `"CRM EFSM: Toda conversa..."`
- [ ] `manifest.json` → `"version"` bate com a versão do ZIP original (não alterar)
- [ ] `label/config/utils.json` → `"nameID"` é `"crmefsm"`
- [ ] `label/config/utils.json` → `"chromeStoreID"` é `"crmefsm"`
- [ ] As 3 imagens foram substituídas pelas da EFSM
- [ ] Nome do arquivo de saída é `CRMEFSM_X.X.XX.zip` com a versão correta
- [ ] Arquivo ZIP foi gerado sem erros

---

## ESTRUTURA DA SKILL

```
efsm-crm/
├── SKILL.md
└── assets/
    ├── icon.png              ← asterisco roxo EFSM (substitui label/icons/plugin/icon.png)
    ├── logo.png              ← logo "eu faço seu marketing" (substitui label/icons/plugin/logo.png)
    └── plugin_login.png      ← tela de login CRM EFSM (substitui label/icons/plugin/plugin_login.png)
```

## ESTRUTURA DO PACOTE GERADO

```
CRMEFSM_X.X.XX.zip
├── manifest.json                      ← editado: name + description EFSM
├── background.js
├── content.css
├── assets/
├── content/
├── label/
│   ├── config/
│   │   └── utils.json                 ← substituído: IDs e textos EFSM
│   ├── css/
│   │   └── wabacrm.css
│   └── icons/
│       └── plugin/
│           ├── icon.png               ← substituído: asterisco roxo EFSM
│           ├── logo.png               ← substituído: logo eu faço seu marketing
│           └── plugin_login.png       ← substituído: tela de login CRM EFSM
└── whatsapp/
```
