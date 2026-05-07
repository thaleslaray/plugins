---
name: pesquisa
description: "Pesquisa profunda em funil multi-nível com fontes verificadas. Use SEMPRE que o usuário disser 'pesquisa', 'pesquisar', 'investiga', 'me ajuda a entender X', 'quero saber sobre Y' ou invocar /pesquisa — esse é o gatilho principal e mais óbvio. Também use proativamente para: comparativos com dados reais (X vs Y, framework A vs B, produto/carro/plano), decisões com stakes (migração de stack, fornecedor, plataforma), validação contra fontes (estudos científicos, benchmarks, segunda opinião médica), análise de mercado/competitiva, deep dive em estado da arte, TCO, impacto de mudanças regulatórias, ou literatura médica/farmacológica (interações, efeitos, validação de diagnóstico) — mesmo quando o user já consultou profissional. NÃO use para perguntas factuais rápidas, debug de código, operações de arquivo, ou referência a invocação anterior. Flags: -f (auto), -a (anônimo)."
---

# Pesquisa em Funil v3

Evolução do `/pesquisa` (v2) com 3 técnicas roubadas de skills do marketplace:

| Técnica | Origem | O que muda |
|---------|--------|------------|
| CRAAP scoring | claim-investigation | Score 0-100 por critério, não só tier |
| Phase Gate por fatos-chave | claim-investigation | ≥2 fontes independentes por fato central |
| Domain filters | Tavily pattern | Queries restritas a domínios confiáveis |

## O Funil v3

```
Nível 1: Varredura (perplexity_search paralelo)
    │ Apresentar → usuário aprova direção (HITL)
    ▼
Nível 2: Análise (perplexity_reason) + identificar fatos-chave + sub-tópicos
    │ Apresentar + listar sub-tópicos + fatos-chave → usuário escolhe (HITL)
    ▼
Nível 3: Deep Dive PARALELO (N × perplexity_research + firecrawl)
    │ Phase Gate v3: sub-perguntas respondidas? + fatos-chave em ≥2 fontes? + CRAAP?
    │ Se não → gap filling focado
    ▼
Relatório final → salvo como ~/pesquisas/[tema]-[data].md
```

**Regra inviolável:** human-in-the-loop entre cada nível. Não pular sem aprovação.

## ★ v3.1 — defesa em profundidade pós-incidente 2026-04-29

Esta skill foi auditada após dogfood que revelou `/pesquisa` rodando "internamente" (modelo se autovigia), gerando relatórios com seções obrigatórias ausentes e CRAAP inflacionado. Mudanças:

- **Phase Gate via subagent independente** (Passo 5): não é mais `executar internamente`, é `Agent({subagent_type: Explore, ...})` produzindo `verification_report.json`
- **CRAAP rubric calibrada** com 3 exemplos por Tier (Passo 4) — sem isso, scores convergem pra 88-95
- **Definição programática de "fonte independente"**: domínios distintos + não-duplicação de paper primário
- **PostToolUse hook validador** em `~/.claude/skills/pesquisa/scripts/validate-report.py` — bloqueia Write em `~/pesquisas/*.md` se relatório não tiver todas seções obrigatórias OU se >50% fatos têm <2 fontes

### Bloco contrastive (good vs bad fluxo)

**❌ Execução RUIM (incidente 2026-04-29):**
```
1. Spawn 5 perplexity_search paralelos → ok
2. Apresentar Nível 1 + AskUserQuestion → ok
3. Receber resposta → ok
4. perplexity_reason no Nível 2 → ok
5. AskUserQuestion sub-tópicos → ok
6. perplexity_research × 4 paralelos → ok
7. Phase Gate: "executar internamente" → modelo PULA, marca 5/5 checks sem evidência
8. Escrever relatório → modelo PULA seção "Contradições Identificadas" silenciosamente
9. CRAAP scores: 95, 92, 90, 88 → distribuição irreal de auto-justificação
10. F4 com "1 substack + 2 LinkedIn + 1 video" → marcado como ALTO sem ≥2 Tier A/B
```

**✅ Execução BOA:**
```
1-6. Mesmas etapas mecânicas
7. Phase Gate: spawn `Agent({subagent_type: Explore, prompt: "verifier independente..."})` → recebe JSON com `verdict`, `weak_facts[]`, `craap_inflation_warning`
8. Escrever relatório SEGUINDO o template literal — incluindo "Contradições Identificadas" mesmo quando vazia (escrever "Nenhuma contradição entre fontes — todas convergiram")
9. CRAAP scores com EVIDÊNCIA POR CRITÉRIO (1 frase pra C, R, A, A, P de cada fonte)
10. Confiança ALTA APENAS se ≥2 fontes Tier A/B independentes (definição programática) por fato-chave
11. Save em ~/pesquisas/ → PostToolUse hook valida formato + bloqueia se inválido
```

## Preparação — carregar `AskUserQuestion`

O skill usa `AskUserQuestion` nos HITLs dos Níveis 1 e 2. Essa tool é **deferred** na harness atual — o schema não é carregado por padrão. **Antes** de rodar qualquer query do Nível 1, executar:

```
ToolSearch({ query: "select:AskUserQuestion", max_results: 1 })
```

Sem esse passo a tool não é invocável e o HITL falha silenciosamente — o modelo acaba escrevendo o "call" como texto em vez de invocar de verdade, e o fluxo trava. Pode rodar em paralelo com as queries do Nível 1 (não bloqueia). Se o schema já aparecer nas tools do turno, pular.

## Flags

### `-f` (full) — funil automático

Se o usuário passar `-f`, rodar o funil completo (1→2→3) sem parar para perguntar entre os níveis. O único HITL mantido é a escolha de sub-tópicos antes do Nível 3 — porque errar os sub-tópicos desperdiça muitas chamadas Perplexity.

### `-a` (anonymous) — não salva em disco

Se o usuário passar `-a`, **pular o passo de salvar o relatório** em `~/pesquisas/`. O relatório é apresentado normalmente na conversa, mas não persiste como arquivo `.md`.

Ao detectar a flag, avisar logo no início (antes do Nível 1):

```
🕶️ Modo anônimo: relatório não será salvo em ~/pesquisas/.
   Nota: queries ainda aparecem no histórico da sua conta Perplexity.
```

### Combinações

```
/pesquisa regulamentação de IA         → funil normal com HITL entre cada nível, salva
/pesquisa -f regulamentação de IA      → 1→2 direto, HITL de sub-tópicos, depois 3, salva
/pesquisa -a regulamentação de IA      → funil normal com HITL, NÃO salva
/pesquisa -fa regulamentação de IA     → automático + anônimo (combinável em qualquer ordem: -af, -fa)
```

---

## Nível 1 — Varredura

**Ferramenta:** `perplexity_search`
**Velocidade:** ~5 segundos por query
**Objetivo:** Mapear o terreno com 3-5 ângulos paralelos.

### Como executar

1. Decompor o tema em 3-5 ângulos complementares
2. Rodar TODAS em paralelo no mesmo turno
3. Usar `sources` estrategicamente: `web`, `scholar`, `social`

### Entrega do Nível 1

**Regra de formatação:** cada ângulo = 1 frase curta com negrito no rótulo. Máximo ~15 palavras por ângulo. Detalhes ficam pro Nível 2. Separar seções com linha em branco.

```
📡 **Varredura: [tema]**

Pesquisei [N] ângulos:

1. **[Rótulo curto]** — [achado em 1 frase, ~15 palavras máx]
2. **[Rótulo curto]** — [achado em 1 frase]
3. **[Rótulo curto]** — [achado em 1 frase]

**Padrões:** [1-2 frases curtas]

**Gaps:** [o que ainda não sei]
```

Depois chamar:
```
AskUserQuestion({
  questions: [{
    question: "Como quer prosseguir?",
    header: "Próximo passo",
    multiSelect: false,
    options: [
      { label: "Nível 2 (Recommended)", description: "Analisar e comparar os achados em profundidade" },
      { label: "Ajustar foco", description: "Mudar direção antes de aprofundar" },
      { label: "Nível 1 basta", description: "Resumo atual é suficiente, encerrar aqui" }
    ]
  }]
})
```

**Não prosseguir sem resposta do usuário.**

---

## Nível 2 — Análise + Fatos-Chave ★ NOVO

**Ferramenta:** `perplexity_reason`
**Velocidade:** ~15 segundos

**Diferença v3:** Além de comparar e identificar sub-tópicos, identificar explicitamente **3-5 fatos-chave** — afirmações factuais centrais para a conclusão que precisarão ser verificadas por ≥2 fontes independentes no Phase Gate.

### Como executar

1. Construir query analítica com achados do Nível 1 + contexto do usuário
2. Pedir comparação direta e tabela de trade-offs
3. Identificar 2-4 sub-tópicos independentes para o Nível 3
4. **Novo:** Listar 3-5 fatos-chave verificáveis (números, datas, causalidades, claims técnicos)

**Exemplos de fatos-chave:**
- "X custa R$Y" → precisa de ≥2 fontes confirmando o preço
- "Framework A é 3x mais rápido que B" → benchmark de ≥2 fontes independentes
- "Empresa X foi fundada em YYYY" → ≥2 fontes com a data

### Entrega do Nível 2

```
🔍 Análise: [tema]

Comparativo:
| Critério | Opção A | Opção B | Opção C |
|----------|---------|---------|---------|
...

Recomendação preliminar: [opção] porque [razão]

Fatos-chave a verificar no Nível 3:
- [ ] [Fato 1] — precisa de ≥2 fontes independentes
- [ ] [Fato 2] — precisa de ≥2 fontes independentes
- [ ] [Fato 3] — precisa de ≥2 fontes independentes
```

Depois chamar (com os sub-tópicos reais identificados):
```
AskUserQuestion({
  questions: [{
    question: "Quais sub-tópicos quer no deep dive paralelo?",
    header: "Deep dive",
    multiSelect: true,
    options: [
      { label: "Todos (Recommended)", description: "Investigar todos os sub-tópicos em paralelo" },
      { label: "[sub-tópico A]", description: "[por que vale investigar]" },
      { label: "[sub-tópico B]", description: "[por que vale investigar]" },
      { label: "[sub-tópico C]", description: "[por que vale investigar]" }
    ]
  }]
})
```

**Regra: sempre "Todos" como primeira opção + até 3 sub-tópicos específicos. Limite da ferramenta: máx 4 opções. Usar multiSelect: true. Não prosseguir sem resposta.**

---

## Nível 3 — Deep Dive Paralelo com Domain Filters

**Ferramentas:** N × `perplexity_research` em paralelo + `firecrawl_scrape`
**Velocidade:** ~60-90s (paralelo, não sequencial)

### Passo 1 — Inferir domain filters (opcional)

Antes de disparar as queries, avaliar se o tema tem domínios de alta confiabilidade óbvios. Se sim, incluir nas queries para priorizar resultados:

| Tipo de tema | Domain hints para queries |
|--------------|--------------------------|
| Tecnologia/frameworks | `site:github.com OR site:arxiv.org OR site:docs.[framework].com` |
| Mercado/business | `site:statista.com OR site:reports.[org].com` |
| Saúde/medicina | `site:pubmed.ncbi.nlm.nih.gov OR site:who.int` |
| Regulação/legal | `site:gov.br OR site:legisweb.com.br` |
| Geral | Não filtrar — deixar o Perplexity decidir |

Incorporar domain hints nas queries do `perplexity_research` quando relevante.

### Passo 2 — Disparar em paralelo

Para cada sub-tópico aprovado, criar uma query específica. Disparar TODAS no mesmo turno:

```
perplexity_research("[sub-tópico A] análise completa 2025 dados concretos [domain hints]")
perplexity_research("[sub-tópico B] análise completa 2025 dados concretos [domain hints]")
perplexity_research("[sub-tópico C] análise completa 2025 dados concretos [domain hints]")
```

### Passo 3 — Scraping de URLs identificadas

Após receber resultados, identificar 2-3 URLs de maior valor e raspar. Ordem de fallback:

1. `firecrawl_scrape(url)` — primeira opção: melhor metadata, cache, lida com JS pesado (MCP pago)
2. Bash: `npx -y @teng-lin/agent-fetch "<url>" --json` — fallback local, ~400ms, verbatim, grátis. Parsear o campo `markdown` do JSON.
3. Bash: `curl -s "https://r.jina.ai/<url>"` — segundo fallback, grátis sem conta, markdown limpo, ~10s
4. `WebFetch(url)` — último recurso: **resume/parafraseeia**, não extrai. Usar só pra confirmar existência, nunca pra extração fiel
5. Pular a URL, anotar como indisponível

URLs que valem o scraping:
- Reviews com dados concretos / benchmarks
- Páginas de especificações técnicas
- Threads de fóruns com casos reais

### Passo 4 — CRAAP Scoring ★ MELHORADO v3.1

Para cada fonte relevante encontrada, avaliar nos 5 critérios — cada um de 0 a 20, total de 0 a 100. **Cada score precisa de evidência por critério** (1 frase justificando), não só o total. Sem evidência por critério, score é descartado como performance theatre.

| Critério | O que avaliar | Score |
|----------|--------------|-------|
| **C**urrency | Data de publicação/atualização. Conteúdo recente para o tema? | 0-20 |
| **R**elevance | Fit direto com a pergunta? Ou apenas tangencial? | 0-20 |
| **A**uthority | Quem publicou? Tem credenciais no domínio? Cite o autor/org | 0-20 |
| **A**ccuracy | Corroborada por outras fontes? Tem referências rastreáveis? | 0-20 |
| **P**urpose | Intenção: informar, vender, persuadir, entreter? | 0-20 |

**Bandas de confiança:**
- 80-100: Tier A — usar como fonte primária, citar diretamente
- 60-79: Tier B — usar com ressalva de autoridade
- 40-59: Tier C — mencionar apenas para contexto, não para fatos
- <40: Tier D — descartar ou citar explicitamente como não confiável

**Atenção ao Purpose:** Fonte com score alto em C/R/A/A mas Purpose = "vender" → rebaixar para Tier C independentemente do total.

#### Exemplos calibrados (uso obrigatório de referência)

Use estes 3 exemplos como ancoragem antes de pontuar suas próprias fontes. Sem rubric externa, scores convergem pra inflação (todos 88-95). Compare contra:

**Tier A (92) — peer-reviewed conference paper:**
- Fonte: arXiv 2410.09102 "Instructional Segment Embedding" (ICLR 2025)
- C=20: publicado out/2024, ainda referencial
- R=20: trata exatamente do tema
- A=18: autores Wallace et al. + ICLR é Tier A venue
- A=18: 40+ refs rastreáveis, código replicável
- P=16: pesquisa acadêmica (não 20 porque ainda assim posição própria)
- **Total: 92 → Tier A. Citação direta justificada.**

**Tier B (72) — community blog post de autor identificado:**
- Fonte: dev.to/kanta13jp1 "LangGraph State Machine Patterns"
- C=18, R=20, A=12, A=14, P=8
- A=12 porque autor dev individual sem credencial acadêmica formal
- P=8 porque blog tem viés de "tutorial otimizado"
- **Total: 72 → Tier B. Use com ressalva.**

**Tier C (52) — LinkedIn pulse post:**
- Fonte: LinkedIn pulse "LLMs struggle with negative prompts"
- C=14, R=18, A=4, A=8, P=8
- A=4 porque LinkedIn pulse não tem revisão
- A=8 porque claims sem dados, sem links pra estudos
- **Total: 52 → Tier C. Mencionar apenas para contexto.**

#### Definição programática de "fonte independente"

Duas fontes são **independentes** quando:
1. **Domínios diferentes** (URLs com hostnames distintos após remover `www.`), E
2. **NÃO são duas resenhas/citações do mesmo paper primário** (ex: 2 blogs falando do mesmo arXiv = 1 fonte efetiva, não 2)

Exemplos:
- ✅ INDEPENDENTES: arxiv.org + aclanthology.org (papers diferentes)
- ✅ INDEPENDENTES: code.claude.com docs + github.com/anthropics issue (oficial + community evidence)
- ❌ DEPENDENTES: 3 blogs em domínios diferentes citando o mesmo arXiv (vale como 1)
- ❌ DEPENDENTES: substack.com + linkedin.com mesmo autor mesma claim
- ⚠️ FRACAS: 1 paper primário + 2 mídias sociais sem dados próprios (~1.5 efetivas)

**Regra prática:** se você não consegue dizer "estas 2 fontes seriam acreditadas mesmo sem a outra", não são independentes. Anote no relatório.

### Passo 5 — Phase Gate v3.1 ★ EXTERNAL VERIFIER (mudou)

**MUDANÇA crítica v3.1:** Phase Gate NÃO é mais executado "internamente" pelo modelo. É delegado a um **subagent verifier independente** (read-only, fresh context). Razão: dogfood 2026-04-29 provou que self-verification rubber-stamps; auditor independente não tem incentivo pra rebaixar.

#### Como invocar o verifier

Antes de escrever o relatório final no Nível 3:

```
Agent({
  description: "Phase Gate verifier",
  subagent_type: "Explore",
  prompt: "Você é Phase Gate verifier INDEPENDENTE pra um relatório /pesquisa. Read-only.

  Você recebe: caminho do draft markdown + lista de URLs encontradas.

  Auditar e produzir verification_report.json com:

  {
    \"verifier_model\": \"...\",
    \"draft_path\": \"...\",
    \"timestamp\": \"...\",
    \"checklist\": [
      {\"id\": \"C1\", \"check\": \"Sub-perguntas do Nível 2 respondidas?\", \"status\": \"pass|fail\", \"evidence\": \"linhas X-Y citam ...\"},
      {\"id\": \"C2\", \"check\": \"Dados concretos (números, datas, casos) além de generalidades?\", \"status\": ...},
      {\"id\": \"C3\", \"check\": \"Fatos-chave têm ≥2 fontes INDEPENDENTES (domínios distintos, não-duplicado)?\", \"status\": ..., \"evidence\": \"para fato F1: ... | para F2: ...\"},
      {\"id\": \"C4\", \"check\": \"Fontes Tier A/B (CRAAP ≥60) com EVIDÊNCIA POR CRITÉRIO confirmam conclusões?\", \"status\": ..., \"evidence\": \"...\"},
      {\"id\": \"C5\", \"check\": \"Contradições entre fontes identificadas e endereçadas?\", \"status\": ..., \"evidence\": \"...\"}
    ],
    \"weak_facts\": [\"F1 só tem 1 fonte real\", ...],
    \"craap_inflation_warning\": \"scores 88-95 sem evidência por critério: ...\",
    \"verdict\": \"pass|fail\",
    \"required_fixes\": [\"...\"]
  }

  Output: APENAS o JSON. Não escreva nada além."
})
```

- Se **verdict: pass**: prosseguir pra escrever relatório final
- Se **verdict: fail**: aplicar fixes listados e re-rodar gate
- Se infraestrutura de subagent indisponível: usar checklist abaixo manualmente, MAS rebaixar Confiança final 1 nível (ALTA → MÉDIA)

#### Checklist de suficiência (fallback se verifier não disponível)

```
□ As sub-perguntas definidas no Nível 2 foram respondidas?
□ Há dados concretos (números, datas, casos) além de generalidades?
□ Fatos-chave identificados no Nível 2 têm ≥2 fontes INDEPENDENTES (definição acima)?
□ Fontes Tier A ou B (CRAAP ≥60) confirmam as principais conclusões?
□ Contradições entre fontes foram identificadas e endereçadas?
```

- Se **≥ 4 checks**: prosseguir
- Se **< 4 checks**: para cada gap:
  - Gap **factual pontual** (fato-chave sem 2ª fonte, número específico) → `perplexity_ask`
  - Gap **analítico/comparativo** (sub-pergunta não respondida, trade-off indefinido) → `perplexity_search`

**Regra de ouro do `ask`:** só usar se a pergunta tem UMA resposta correta e factual. Se começa com "depende", usar `reason`.

**Fatos-chave sem 2ª fonte:** Se um fato central do relatório tem apenas 1 fonte, verificar ativamente com `perplexity_ask` antes de reportar como confirmado. Se não encontrar 2ª fonte, reportar como "fonte única — não confirmado independentemente".

---

## Entrega do Nível 3

```
📋 Relatório: [tema]
Gerado em: [data] | Sub-tópicos: [N] | Fontes avaliadas: [N] | Fatos-chave verificados: [N/total]

## Resumo Executivo
[2-3 frases com conclusão principal e nível de confiança explícito]

## [Sub-tópico A]
[Achados com dados concretos]
Fatos verificados: [lista com status ≥2 fontes ou "fonte única"]
Fontes principais: [CRAAP score ≥60 com URLs]

## [Sub-tópico B]
[Achados com dados concretos]
Fatos verificados: [lista com status]
Fontes principais: [CRAAP score ≥60 com URLs]

## Comparativo Final
| Critério | Opção A | Opção B |
|----------|---------|---------|
| [dado concreto] | ... | ... |

## Recomendação
[Opção recomendada + justificativa + nível de confiança: ALTO/MÉDIO/BAIXO]

Confiança ALTO: todos fatos-chave com ≥2 fontes Tier A/B
Confiança MÉDIO: maioria dos fatos com ≥2 fontes, algumas Tier C
Confiança BAIXO: fatos com fonte única ou predominância Tier C/D

## Contradições Identificadas
[Pontos onde fontes divergem — mencionar os dois lados com scores CRAAP]

## Status dos Fatos-Chave
| Fato | Fontes | Verificado? |
|------|--------|-------------|
| [fato 1] | [fonte A] + [fonte B] | ✅ confirmado |
| [fato 2] | [fonte A] apenas | ⚠️ fonte única |
| [fato 3] | [fonte A] contradiz [fonte B] | ❌ conflito |

## Fontes Avaliadas (CRAAP)
**Tier A (80-100):**
- [fonte — score — URL — data]

**Tier B (60-79):**
- [fonte — score — URL]

**Tier C/D (<60 — com ressalva):**
- [fonte — score — URL — motivo do rebaixamento]
```

---

## Salvar como arquivo

**Se a flag `-a` foi passada:** pular este passo inteiro. Avisar ao final:

```
🕶️ Modo anônimo: relatório não salvo em disco.
```

**Caso contrário (default):** após apresentar o relatório, salvar automaticamente:

```bash
mkdir -p ~/pesquisas
# Nome: pesquisa-[tema-slug]-[YYYY-MM-DD].md
```

Usar a ferramenta `Write` para criar o arquivo em `~/pesquisas/pesquisa-[tema]-[data].md`.

Informar o usuário: `Relatório salvo em: ~/pesquisas/pesquisa-[tema]-[data].md`

---

## Adaptação por contexto

| Tipo | Nível 1 | Nível 2 | Nível 3 | Domain hints |
|------|---------|---------|---------|--------------|
| **Compra** | Opções, preços, reviews | Comparativo + trade-offs | Produto A / Produto B / Problemas reais | Reclame Aqui, Procon, reviews especializados |
| **Tecnologia** | Frameworks, benchmarks | Comparativo técnico | Docs oficiais / Issues / Comunidade | github.com, arxiv.org, docs.[framework] |
| **Mercado** | Tamanho, players | Análise competitiva | Player A / Player B / Regulação | statista.com, ibge.gov.br |
| **Aprendizado** | Conceitos, fontes | Síntese + gaps | Paper / Implementações / Casos reais | arxiv.org, scholar |
| **Decisão** | Opções, critérios, riscos | Matriz de decisão | Risco A / Risco B / Validação | Depende do domínio |

## Comportamento padrão e flags

- `/pesquisa [tema]` (padrão): Funil completo 1→2→3 com HITL entre cada nível. Salva relatório em `~/pesquisas/`.
- `/pesquisa -f [tema]`: Roda 1→2 direto sem perguntar, para só no HITL de sub-tópicos antes do Nível 3, depois completa. Salva.
- `/pesquisa -a [tema]`: Funil normal com HITL, mas **não salva** o relatório em disco (modo anônimo).
- `/pesquisa -fa [tema]` (ou `-af`): Combinação — funil automático + sem salvar.

Se o usuário já está satisfeito no Nível 1 ou 2, não forçar o funil. Perguntar.

---

## Ferramentas

| Ferramenta | Quando usar | Sources |
|-----------|-------------|---------|
| `perplexity_search` | Nível 1, gap filling analítico | web, scholar, social |
| `perplexity_ask` | Phase Gate: gaps factuais pontuais com resposta única | web, scholar, social |
| `perplexity_reason` | Nível 2, análise/comparação/trade-offs | web, scholar, social |
| `perplexity_research` | Nível 3, por sub-tópico (paralelo) | web, scholar, social |
| `firecrawl_scrape` | Nível 3, URLs específicas — 1ª opção (MCP pago) | qualquer URL |
| `npx -y @teng-lin/agent-fetch "<url>" --json` | 2º fallback — local, ~400ms, verbatim, grátis | qualquer URL |
| `curl -s "https://r.jina.ai/<url>"` | 3º fallback — grátis, markdown limpo, ~10s | qualquer URL |
| `WebFetch` | Último recurso — **resume, não extrai** | qualquer URL |
| `firecrawl_map` | Descobrir URLs de um site | qualquer URL |
| `Write` | Salvar relatório final como .md | — |

**Quando NÃO usar `ask`:** comparativos, trade-offs, análises qualitativas, qualquer pergunta cuja resposta comece com "depende". Nesses casos sempre `reason`.

---

## Fallback: tokens expirados

Se `perplexity_search` falhar com erro de autenticação ou o MCP desconectar:

```
⚠️ Tokens do Perplexity expiraram. Para renovar:

1. Abrir perplexity.ai no browser (logado)
2. Usar a extensão Perplexity Keys (Chrome) para copiar os 2 tokens
   - Se não tiver a extensão: DevTools (F12) → Application → Cookies → https://www.perplexity.ai
   - Copiar: __Secure-next-auth.session-token e next-auth.csrf-token
3. Atualizar os tokens no arquivo onde o MCP foi instalado:
   - Se instalou via `claude mcp add --scope user`: ~/.claude/.mcp.json
   - Se instalou via plugin marketplace: ~/.claude/plugins/marketplaces/[autor]/.mcp.json
   - Se não sabe onde está: rodar `grep -r "perplexity" ~/.claude/ --include="*.json" -l`
4. Sair e entrar de novo no Claude Code
```

Firecrawl e as demais ferramentas de scraping continuam funcionando sem o Perplexity.
