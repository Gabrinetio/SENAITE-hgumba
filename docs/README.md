# DocumentaÃ§Ã£o do Projeto SENAITE â€” HGUMBA

Ãndice centralizado da documentaÃ§Ã£o. Os arquivos originais permanecem intactos em suas respectivas pastas.

---

## NavegaÃ§Ã£o RÃ¡pida

| # | Documento | PÃºblico-alvo | ConteÃºdo |
|---|-----------|-------------|----------|
| 00 | [00-specification.md](./00-specification.md) | Infraestrutura | Stack, acesso, credenciais, arquitetura ZODB |
| 01 | [01-summary.md](./01-summary.md) | Equipe tÃ©cnica | Progresso, liÃ§Ãµes aprendidas, critical context |
| 02 | [02-customizations.md](./02-customizations.md) | Desenvolvedores | Add-on senaite.hgumba: CDM, CoPhysicians, report PDF, create-ar, set-remark |
| 03 | [03-middleware.md](./03-middleware.md) | Desenvolvedores | Spec-first do middleware: rotas, contratos Pydantic, camadas |
| 04 | [04-middleware-readme.md](./04-middleware-readme.md) | OperaÃ§Ã£o | README do middleware: instalaÃ§Ã£o, execuÃ§Ã£o, testes, endpoints |
| 05 | [05-integracao.md](./05-integracao.md) | Lab + Eng. ClÃ­nica | Manual de integraÃ§Ã£o: CATSERV, ASTM, portas, troubleshooting |
| 06 | [06-deploy.md](./06-deploy.md) | Infraestrutura | Deploy Swarm: volumes NFS, redes overlay, constraints, rollback |
| 07 | [07-auditoria.md](./07-auditoria.md) | Auditoria/Qualidade | POP RDC 978: rastreabilidade, logs JSON, mapa de auditoria |
| 08 | [08-manual-operador.md](./08-manual-operador.md) | **Operadores do LAC** | POP diÃ¡rio: cadastro, CDM, flags, publish, troubleshooting |
| 09 | [09-drp.md](./09-drp.md) | GTI e SysAdmins | Disaster Recovery expandido: restore ZODB, pg_dump, migraÃ§Ã£o NFS, SLA 98% |
| â€” | [drp.md](./drp.md) | GTI e SysAdmins | **DRP oficial do edital** â€” versÃ£o concisa com repozo, pg_dump e contingÃªncia Swarm |
| â€” | [requisitos_ti.md](./requisitos_ti.md) | TI do ExÃ©rcito | Requisitos de integraÃ§Ã£o pÃ³s-sigilo: endpoints CADBEN/SIRE/SANDRA, seguranÃ§a, homologaÃ§Ã£o |

---

## Matriz por Tarefa

| Se vocÃª precisa | Leia |
|-----------------|------|
| Subir o ambiente local | `04-middleware-readme.md` (instalaÃ§Ã£o + compose) |
| Configurar um analisador | `05-integracao.md` (seÃ§Ã£o 3: portas e handshake) |
| Mapear exame CATSERV â†’ SENAITE | `05-integracao.md` (seÃ§Ã£o 1: dicionÃ¡rio) |
| Fazer deploy no Swarm | `06-deploy.md` |
| Criar um endpoint Zope novo | `02-customizations.md` (seÃ§Ãµes 1, 5, 6) |
| Troubleshooting de resultado rejeitado | `05-integracao.md` (seÃ§Ã£o 7: audit logger) |
| Auditoria RDC 978 | `07-auditoria.md` |
| OperaÃ§Ã£o diÃ¡ria do LAC | `08-manual-operador.md` |
| Disaster Recovery e Continuidade | `09-drp.md` |
| Consultar credenciais de acesso | `00-specification.md` |
| Ver o que jÃ¡ foi feito e prÃ³ximos passos | `01-summary.md` |

---

## Origem dos Arquivos

| Documento Centralizado | Original em |
|-----------------------|------------|
| `00-specification.md` | `SENAITE/specification.md` |
| `01-summary.md` | `SENAITE/summary.md` |
| `02-customizations.md` | `SENAITE/customizations/spec-customizations.md` |
| `03-middleware.md` | `SENAITE/hgumba-middleware/spec-middleware.md` |
| `04-middleware-readme.md` | `SENAITE/hgumba-middleware/README.md` |
| `05-integracao.md` | `SENAITE/hgumba-middleware/docs/integracao.md` |
| `06-deploy.md` | *(documento original desta pasta)* |
| `07-auditoria.md` | `SENAITE/hgumba-middleware/docs/auditoria_rdc978.md` |
| `08-manual-operador.md` | *(documento original desta pasta)* |
| `09-drp.md` | *(documento original desta pasta)* |

---

## ConvenÃ§Ãµes

- **Nomes**: Prefixo numÃ©rico de dois dÃ­gitos para ordenaÃ§Ã£o lÃ³gica
- **Header**: Cada documento inicia com `> **Origem:** <caminho original>`
- **AtualizaÃ§Ã£o**: Prefira editar o original e recopiar para `docs/`. Ou edite direto aqui e sincronize de volta.
