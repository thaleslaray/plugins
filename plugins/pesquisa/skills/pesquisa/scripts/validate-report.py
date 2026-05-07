#!/usr/bin/env python3
"""
PostToolUse hook validator para relatórios /pesquisa.

Roda após Write em ~/pesquisas/*.md. Valida que o relatório tem:
1. Todas as seções obrigatórias do formato declarado em SKILL.md
2. Cada fato-chave com ≥2 fontes independentes (domínios diferentes)
3. Confiança declarada bate com evidência real
4. CRAAP scores acompanhados de evidência por critério (não só total)

Exit codes:
- 0: válido, deixa passar
- 2: inválido, bloqueia (formato Claude Code hook)

JSON output em stderr com `permissionDecision: "deny"` + `permissionDecisionReason`.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


REQUIRED_SECTIONS = [
    "Resumo Executivo",
    "Comparativo Final",
    "Recomendação",
    "Contradições Identificadas",
    "Status dos Fatos-Chave",
    "Fontes Avaliadas",
]

# Confiança rules (declared vs derived)
CONFIANCA_RULES = {
    "ALTA": "todos fatos-chave com ≥2 fontes Tier A/B",
    "MÉDIA": "maioria dos fatos com ≥2 fontes, algumas Tier C",
    "BAIXA": "fatos com fonte única ou predominância Tier C/D",
}


def read_hook_input():
    """Lê JSON do stdin (formato PostToolUse hook)."""
    try:
        return json.load(sys.stdin)
    except Exception as e:
        # Hook input não disponível (rodando standalone) — pega de argv
        if len(sys.argv) > 1:
            return {"toolInput": {"file_path": sys.argv[1]}}
        sys.stderr.write(f"hook input parse fail: {e}\n")
        return None


def deny(reason, context="", event="PreToolUse"):
    """Emite JSON de bloqueio + exit 2 (Claude Code hook deny).

    PreToolUse: deny BLOQUEIA a execução do Write/Edit.
    PostToolUse: deny apenas envia feedback (file já foi escrito).
    """
    out = {
        "hookSpecificOutput": {
            "hookEventName": event,
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
            "additionalContext": context,
        }
    }
    print(json.dumps(out))
    sys.stderr.write(f"VALIDATION FAILED: {reason}\n")
    sys.exit(2)


def warn_only(reason):
    """Emite warning mas permite (apenas additionalContext, sem deny)."""
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": f"⚠️ /pesquisa validator: {reason}",
        }
    }
    print(json.dumps(out))
    sys.exit(0)


def extract_facts_table(content):
    """
    Extrai tabela 'Status dos Fatos-Chave' e retorna list of dicts.
    Esperado:
    | Fato | Fontes | Verificado? |
    """
    pattern = r"## Status dos Fatos-Chave\s*\n(.*?)(?=\n##|\Z)"
    m = re.search(pattern, content, re.DOTALL)
    if not m:
        return None
    section = m.group(1)
    rows = []
    for line in section.split("\n"):
        if re.match(r"^\|.*\|.*\|.*\|", line) and "---" not in line and "Fato" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 3:
                rows.append({
                    "fato": cells[0],
                    "fontes": cells[1],
                    "status": cells[2],
                })
    return rows


def count_independent_domains(fontes_str):
    """
    Conta domínios DISTINTOS em string de fontes.
    'Trilogyai + 2 LinkedIn + 1 video' → conta tokens, mas não temos URLs.
    Tentativa: cada nome diferente conta como 1 fonte. Domínios não-url contam mas com tag.
    """
    # Divide por '+', ',', 'e' (case insensitive)
    parts = re.split(r"\s*[\+,]\s*|\s+e\s+", fontes_str, flags=re.IGNORECASE)
    parts = [p.strip() for p in parts if p.strip()]

    # Para URLs reais, extrair domínio
    domains = set()
    non_url_sources = set()
    for p in parts:
        # Tem http(s)?
        urls = re.findall(r"https?://[^\s\)]+", p)
        if urls:
            for u in urls:
                try:
                    d = urlparse(u).netloc.replace("www.", "")
                    if d:
                        domains.add(d)
                except Exception:
                    pass
        else:
            # Sem URL — usa nome textual (rebaixado, conta como 0.5 cada)
            cleaned = re.sub(r"^\d+\s+", "", p).strip().lower()
            if cleaned:
                non_url_sources.add(cleaned)

    return {
        "url_domains": len(domains),
        "url_domain_list": sorted(domains),
        "non_url_sources": len(non_url_sources),
        "non_url_list": sorted(non_url_sources),
    }


def extract_confianca(content):
    """Extrai declaração de confiança do Resumo Executivo."""
    # Match "Confiança ALTA" ou "**Confiança ALTA**"
    m = re.search(
        r"\*?\*?[Cc]onfian[çc]a\s+(?:geral:?\s+)?(\*?\*?)(ALTA|MÉDIA|MEDIA|BAIXA|ALTO|MÉDIO|MEDIO|BAIXO)",
        content,
    )
    if m:
        return m.group(2).upper().replace("MEDIA", "MÉDIA").replace("MEDIO", "MÉDIO")
    return None


def extract_craap_scores(content):
    """Extrai scores CRAAP da seção Fontes Avaliadas."""
    # Pattern: "score N" ou "Tier X (N-Y)"
    scores = []
    pattern = r"score\s+(\d+)"
    for m in re.finditer(pattern, content):
        scores.append(int(m.group(1)))
    return scores


def validate(file_path, content=None):
    """Validação principal. Retorna (ok, reason, context).

    Se content é passado (PreToolUse: tool_input.content), valida-o direto.
    Senão lê do disco (PostToolUse / standalone).
    """
    p = Path(file_path).expanduser()

    if not str(p).startswith(str(Path.home() / "pesquisas")):
        return True, "fora de ~/pesquisas/", ""  # não é relatório /pesquisa

    if not p.suffix == ".md":
        return True, "não é .md", ""

    if content is None:
        if not p.exists():
            return True, "arquivo não existe", ""
        content = p.read_text()

    # Check 1: secões obrigatórias
    missing_sections = []
    for section in REQUIRED_SECTIONS:
        if not re.search(rf"##\s+{re.escape(section)}", content):
            missing_sections.append(section)

    if missing_sections:
        return False, (
            f"Relatório /pesquisa em {p.name} está faltando seção(ões) obrigatória(s) "
            f"declarada(s) no SKILL.md: {', '.join(missing_sections)}. "
            f"Adicione antes de finalizar."
        ), f"Seções esperadas: {REQUIRED_SECTIONS}"

    # Check 2: fatos-chave com ≥2 fontes independentes
    facts = extract_facts_table(content)
    if facts is None:
        return False, "Tabela 'Status dos Fatos-Chave' não encontrada ou mal formatada.", ""

    weak_facts = []
    for f in facts:
        sources_info = count_independent_domains(f["fontes"])
        # Total de fontes "fortes" = url_domains; non_url sources contam como 0.5
        effective_count = sources_info["url_domains"] + (sources_info["non_url_sources"] * 0.5)
        if effective_count < 2:
            weak_facts.append({
                "fato": f["fato"][:80],
                "url_domains": sources_info["url_domain_list"],
                "non_url": sources_info["non_url_list"],
                "effective": effective_count,
            })

    # Check 3: Confiança declarada coerente
    confianca = extract_confianca(content)
    n_facts_full = sum(1 for f in facts if "✅" in f["status"] or "confirmado" in f["status"].lower())
    n_facts_total = len(facts)
    pct_confirmed = (n_facts_full / n_facts_total) if n_facts_total else 0

    confianca_warning = None
    if confianca == "ALTA" and pct_confirmed < 0.9:
        confianca_warning = (
            f"Confiança declarada ALTA mas só {n_facts_full}/{n_facts_total} fatos "
            f"({pct_confirmed:.0%}) marcados como confirmados. Revisar."
        )

    # Compor resultado: bloqueia em sections missing OU >50% fatos fracos.
    # Outros casos: warn-only.
    if weak_facts and len(weak_facts) > len(facts) // 2:
        return False, (
            f"Mais da metade dos fatos-chave ({len(weak_facts)}/{len(facts)}) tem <2 fontes "
            f"independentes (domínios distintos). Skill /pesquisa exige ≥2 fontes Tier A/B "
            f"pra Confiança ALTA. Forneça URLs reais ou rebaixe Confiança."
        ), json.dumps(weak_facts, ensure_ascii=False, indent=2)

    # Avisos não-bloqueantes
    warnings = []
    if weak_facts:
        warnings.append(f"{len(weak_facts)} fato(s)-chave com <2 fontes (URLs distintas): "
                        + ", ".join(f["fato"][:40] for f in weak_facts[:3]))
    if confianca_warning:
        warnings.append(confianca_warning)

    scores = extract_craap_scores(content)
    if scores and (max(scores) - min(scores)) < 8:
        warnings.append(f"Distribuição de CRAAP scores muito apertada ({min(scores)}-{max(scores)}) "
                        f"— sugere auto-justificação. Revisar critérios individuais.")

    if warnings:
        return True, "warnings", " | ".join(warnings)

    return True, "ok", "Validação passou: todas seções presentes, fatos-chave com fontes adequadas."


def main():
    hook_input = read_hook_input()
    if not hook_input:
        sys.exit(0)  # nada pra validar

    # Hook fields: tool_input.file_path (Write/Edit) — Claude Code usa snake_case
    tool_input = hook_input.get("tool_input") or hook_input.get("toolInput") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path")

    if not file_path:
        sys.exit(0)

    # Claude Code usa snake_case "tool_name" OU camelCase "toolName"
    tool_name = hook_input.get("tool_name") or hook_input.get("toolName", "")
    content = None
    if tool_name == "Write":
        content = tool_input.get("content")
    elif tool_name == "Edit":
        # Edit muda parte do arquivo. Pra validar, leríamos o arquivo + simular edit.
        # Por ora: deixar Edit passar (raramente é usado pra criar relatório do zero).
        sys.exit(0)

    ok, reason, context = validate(file_path, content=content)

    if not ok:
        deny(reason, context)
    elif reason == "warnings":
        warn_only(context)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
