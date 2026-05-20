# Documentação do Projeto SENAITE ” HGUMBA

Índice centralizado da documentação. Os arquivos originais permanecem intactos em suas respectivas pastas.

---

## Navegação Rápida

| # | Documento | Público-alvo | Conteúdo |
|---|-----------|-------------|----------|
| 00 | [00-specification.md](./00-specification.md) | Infraestrutura | Stack, acesso, credenciais, arquitetura ZODB |
| 01 | [01-summary.md](./01-summary.md) | Equipe técnica | Progresso, lições aprendidas, critical context |
| 02 | [02-customizations.md](./02-customizations.md) | Desenvolvedores | Add-on senaite.hgumba: CDM, CoPhysicians, report PDF, create-ar, set-remark |
| 03 | [03-middleware.md](./03-middleware.md) | Desenvolvedores | Spec-first do middleware: rotas, contratos Pydantic, camadas |
| 04 | [04-middleware-readme.md](./04-middleware-readme.md) | Operação | README do middleware: instalação, execução, testes, endpoints |
| 05 | [05-integracao.md](./05-integracao.md) | Lab + Eng. Clínica | Manual de integração: CATSERV, ASTM, portas, troubleshooting |
| 06 | [06-deploy.md](./06-deploy.md) | Infraestrutura | Deploy Swarm: volumes NFS, redes overlay, constraints, rollback |
| 07 | [07-auditoria.md](./07-auditoria.md) | Auditoria/Qualidade | POP RDC 978: rastreabilidade, logs JSON, mapa de auditoria |
| 08 | [08-manual-operador.md](./08-manual-operador.md) | **Operadores do LAC** | POP diário: cadastro, CDM, flags, publish, troubleshooting |
| 09 | [09-drp.md](./09-drp.md) | GTI e SysAdmins | Disaster Recovery expandido: restore ZODB, pg_dump, migração NFS, SLA 98% |
| ” | [drp.md](./drp.md) | GTI e SysAdmins | **DRP oficial do edital** ” versão concisa com repozo, pg_dump e contingência Swarm |
| ” | [requisitos_ti.md](./requisitos_ti.md) | TI do Exército | Requisitos de integração pós-sigilo: endpoints CADBEN/SIRE/SANDRA, segurança, homologação |

---

## Matriz por Tarefa

| Se você precisa | Leia |
|-----------------|------|
| Subir o ambiente local | `04-middleware-readme.md` (instalação + compose) |
| Configurar um analisador | `05-integracao.md` (seção 3: portas e handshake) |
| Mapear exame CATSERV â†’ SENAITE | `05-integracao.md` (seção 1: dicionário) |
| Fazer deploy no Swarm | `06-deploy.md` |
| Criar um endpoint Zope novo | `02-customizations.md` (seções 1, 5, 6) |
| Troubleshooting de resultado rejeitado | `05-integracao.md` (seção 7: audit logger) |
| Auditoria RDC 978 | `07-auditoria.md` |
| Operação diária do LAC | `08-manual-operador.md` |
| Disaster Recovery e Continuidade | `09-drp.md` |
| Consultar credenciais de acesso | `00-specification.md` |
| Ver o que já foi feito e próximos passos | `01-summary.md` |

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

## Convenções

- **Nomes**: Prefixo numérico de dois dígitos para ordenação lógica
- **Header**: Cada documento inicia com `> **Origem:** <caminho original>`
- **Atualização**: Prefira editar o original e recopiar para `docs/`. Ou edite direto aqui e sincronize de volta.
