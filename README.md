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
| [`hotmart`](./plugins/hotmart) | MCP | ecommerce | 0.2.3 | Hotmart API MCP server — sales, subscriptions, club, products, coupons, tickets, and negotiation, auto-generated from the official OpenAPI spec Source: [`hotmart-mcp`](https://github.com/thaleslaray/hotmart-mcp). |
| [`pesquisa`](./plugins/pesquisa) | Skill | produtividade | 0.1.0 | Pesquisa profunda em funil multi-nível com fontes verificadas |

<!-- PLUGINS_TABLE_END -->

### Instalar um plugin específico

```
/plugin install hotmart       # MCP da Hotmart
/plugin install pesquisa      # Skill /pesquisa
```

### Atualizar

```
/plugin marketplace update thales-plugins        # 1. atualiza catálogo
/plugin update <nome>@thales-plugins             # 2. atualiza plugin instalado
/reload-plugins                                  # 3. recarrega
```

E reinicia o Claude Code.

⚠️ A ordem importa:
1. **`marketplace update`** faz o Claude "enxergar" versões novas no catálogo
2. **`plugin update <nome>@thales-plugins`** baixa a nova versão do plugin (note o sufixo `@thales-plugins`, é a sintaxe oficial)

Os MCPs vêm com versão pinada no `.mcp.json` (ex: `@v0.2.3`), então o uvx invalida cache sozinho — sem precisar `rm -rf` manual.

## Padrão técnico

- **Skills puras** ficam direto neste repo em `plugins/<nome>/skills/<nome>/`.
- **MCPs** moram em repos próprios (ex: [`hotmart-mcp`](https://github.com/thaleslaray/hotmart-mcp)) e são referenciados via `.mcp.json` com `uvx --from git+...`. Cada MCP tem seu próprio ciclo de release e gera `.mcpb` instalável no Claude Desktop.
- Mesmo padrão de [`anthropics/claude-plugins-official`](https://github.com/anthropics/claude-plugins-official) (marketplace agregador) + [`anthropics/mcp-server-*`](https://github.com/anthropics) (1 repo por MCP server).
- A tabela acima é regenerada automaticamente pela skill `/publicar` a partir do `marketplace.json` + `plugin.json` de cada plugin.

## Licença

MIT
