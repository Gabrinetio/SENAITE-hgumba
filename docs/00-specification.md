> **Origem:** `SENAITE/specification.md`

# SENAITE LIMS — Especificação Arquitetural

## Stack
- **Nome**: `senaite`
- **Imagem**: `192.168.4.23:5000/senaite:2.x`
- **Nó**: docker-01 (manager) — fixado via `node.role == manager`

## Acesso
| URL | Porta | Descrição |
|-----|-------|-----------|
| `http://192.168.4.16:8083/` | 8083 | Direto ao SENAITE (Zope/Plone) |
| `http://senaite.gti.local/` | 80/443 | Via Nginx Proxy Manager (configurar NPM) |

## Credenciais (ZMI/Zope)
- **Usuário**: `admin`
- **Senha**: `admin`
- **ZMI**: `http://192.168.4.16:8083/manage`

> O site SENAITE ainda não foi criado. Acessar a URL e clicar em **"Create a new SENAITE site"**.

## Arquitetura
```
Nginx Proxy Manager (80/443) → senaite_app:8083 (proxy_network)
```

### ZODB / Single Replica
`replicas: 1` — ZODB não suporta escrita concorrente sem ZEO.

### Recursos
- **Limits**: 1.5 CPU / 2 GB RAM
- **Reservations**: 0.5 CPU / 1 GB RAM

### Rede
- `proxy_network` (overlay externa)

### Volumes
- Bind mount `/opt/senaite/var` — persistência ZODB Data.fs
