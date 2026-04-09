# gabs-design

Skill de engenharia de prompt para direção de arte com IA generativa. Baseada no Manual Mestre de Gabryel Alves.

Gera Super Prompts profissionais em 6 camadas para Gemini/Imagen, Adobe Firefly, DALL-E 3 e Midjourney.

## Como usar

```
/gabs-design
```

## O que esta skill faz

| Workflow | Descrição |
|---------|-----------|
| Super Prompt (6 Camadas) | Sujeito, Meio, Técnica, Iluminação, Modificadores, Escudo |
| Engenharia Reversa | Analisa imagem de referência e gera prompt equivalente |
| Referência Dupla | Coloca sujeito real num estilo específico |
| Upscale Inteligente | Prompt para aumentar resolução sem deformar o sujeito |

## Ferramentas suportadas

- Gemini / Imagen 3
- Adobe Firefly
- DALL-E 3 (ChatGPT)
- Midjourney
- Stable Diffusion / Magnific AI / Krea (upscale)

## Instalação

```bash
cp SKILL.md ~/.claude/commands/gabs-design.md
```
