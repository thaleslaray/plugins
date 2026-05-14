# thales-plugins

Skills e MCPs do [Thales Laray](https://instagram.com/thaleslaray) pra Claude Code.

## Instalar

```
/plugin marketplace add thaleslaray/plugins
/plugin install <nome-do-plugin>
```

Pra MCPs, depois do install rode `/<nome>:configure` pra entrar com as credenciais.

## Plugins disponíveis

| Plugin | Tipo | Categoria | Versão | Descrição |
|---|---|---|---|---|
| [`hotmart`](./plugins/hotmart) | MCP | ecommerce | 0.2.2 | Hotmart API — vendas, assinaturas, área de membros, produtos, cupons, eventos, negociação. 28 tools auto-geradas da spec OpenAPI oficial. Source: [`hotmart-mcp`](https://github.com/thaleslaray/hotmart-mcp). |
| [`pesquisa`](./plugins/pesquisa) | Skill | produtividade | 0.1.0 | Pesquisa profunda multi-agent em funil com idoneidade-first — CRAAP cego, adversarial council com sequential blinding, counter-adversarial, forensic CrossRef/OpenAlex, atomic fact decomposition opt-in. |

### Instalar um plugin específico

```
/plugin install hotmart       # MCP da Hotmart
/plugin install pesquisa      # Skill /pesquisa-v6
```

### Atualizar

```
/plugin update <nome>
```

Pra MCPs, depois do update limpa o cache do uvx pra pegar o código novo:

```bash
rm -rf ~/.cache/uv/git-v0/checkouts/*<nome>*
```

E reinicia o Claude Code.

## Padrão técnico

- **Skills puras** ficam direto neste repo em `plugins/<nome>/skills/<nome>/`.
- **MCPs** moram em repos próprios (ex: [`hotmart-mcp`](https://github.com/thaleslaray/hotmart-mcp)) e são referenciados via `.mcp.json` com `uvx --from git+...`. Cada MCP tem seu próprio ciclo de release e gera `.mcpb` instalável no Claude Desktop.
- Mesmo padrão de [`anthropics/claude-plugins-official`](https://github.com/anthropics/claude-plugins-official) (marketplace agregador) + [`anthropics/mcp-server-*`](https://github.com/anthropics) (1 repo por MCP server).

## Licença

MIT
