# thales-plugins

Skills e MCPs do [Thales Laray](https://instagram.com/thaleslaray) pra Claude Code.

## Instalar

```
/plugin marketplace add thaleslaray/plugins
/plugin install <nome-do-plugin>
```

Pra MCPs, depois do install rode `/<nome>:configure` pra entrar com as credenciais.

## Plugins disponíveis

<!-- PLUGINS_TABLE_START -->

| Plugin | Tipo | Categoria | Versão | Descrição |
|---|---|---|---|---|
| [`clint`](./plugins/clint) | MCP | sales | 0.2.0 | MCP server for the Clint CRM API (Brazilian) — 46 endpoints, FastMCP + Code Mode Source: [`clint-mcp`](https://github.com/thaleslaray/clint-mcp). |
| [`hotmart`](./plugins/hotmart) | MCP | ecommerce | 0.2.3 | Hotmart API MCP server — sales, subscriptions, club, products, coupons, tickets, and negotiation, auto-generated from the official OpenAPI spec Source: [`hotmart-mcp`](https://github.com/thaleslaray/hotmart-mcp). |
| [`pesquisa`](./plugins/pesquisa) | Skill | produtividade | 0.1.0 | Pesquisa profunda em funil multi-nível com fontes verificadas |

<!-- PLUGINS_TABLE_END -->

### Instalar um plugin específico

```
/plugin install hotmart       # MCP da Hotmart
/plugin install pesquisa      # Skill /pesquisa
```

### Atualizar

No **terminal externo** (não dentro do Claude Code):

```bash
claude plugin marketplace update thales-plugins
claude plugin install <nome>@thales-plugins
```

Depois reinicia o Claude Code.

> ⚠️ Use `install` (não `update`) — `claude plugin update` tem [bug conhecido](https://github.com/anthropics/claude-code/issues/46594) e reporta "already at latest" falsamente sem fazer `git fetch`. `install` em cima de instalação existente reinstala preservando config (validado em [issue #54678](https://github.com/anthropics/claude-code/issues/54678)).

> 💡 **Opcional — auto-update:** dentro do Claude Code, `/plugin` → **Marketplaces** → `thales-plugins` → **Enable auto-update**. Configura 1×, esquece.

Os MCPs vêm com versão pinada no `.mcp.json` (ex: `@v0.2.3`), então o uvx invalida cache sozinho — sem precisar `rm -rf` manual.

## Padrão técnico

- **Skills puras** ficam direto neste repo em `plugins/<nome>/skills/<nome>/`.
- **MCPs** moram em repos próprios (ex: [`hotmart-mcp`](https://github.com/thaleslaray/hotmart-mcp)) e são referenciados via `.mcp.json` com `uvx --from git+...`. Cada MCP tem seu próprio ciclo de release e gera `.mcpb` instalável no Claude Desktop.
- Mesmo padrão de [`anthropics/claude-plugins-official`](https://github.com/anthropics/claude-plugins-official) (marketplace agregador) + [`anthropics/mcp-server-*`](https://github.com/anthropics) (1 repo por MCP server).
- A tabela acima é regenerada automaticamente pela skill `/publicar` a partir do `marketplace.json` + `plugin.json` de cada plugin.

## Licença

MIT
