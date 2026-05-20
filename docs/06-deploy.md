> **Origem:** `SENAITE/docs/deploy.md`

# Guia de Deploy e Orquestração — Swarm

> Estratégico para Infraestrutura: transformar `compose.local.yaml` na Stack definitiva do Swarm.

---

## Sumário

1. [Visão Geral da Stack](#1-visao-geral-da-stack)
2. [Compose Local → Swarm Stack](#2-compose-local--swarm-stack)
3. [Volumes e Constraints (192.168.4.23)](#3-volumes-e-constraints-192168423)
4. [Redes Overlay](#4-redes-overlay)
5. [Deploy via MCP-GTI](#5-deploy-via-mcp-gti)
6. [Verificação Pós-Deploy](#6-verificacao-pos-deploy)
7. [Rollback e Manutenção](#7-rollback-e-manutencao)

---

## 1. Visão Geral da Stack

### Stack: `senaite`

| Serviço | Imagem | Portas | Réplicas | Depende de |
|---------|--------|--------|----------|------------|
| `app` | `192.168.4.23:5000/senaite:2.x` | 8083 → 8080 | 1 (ZODB) | — |
| `db` | `postgres:13-alpine` | 5433 → 5432 | 1 | — |
| `middleware_gateway` | `192.168.4.23:5000/hgumba-middleware:latest` | 8000 | 1 (escalável) | app, db |
| `middleware_instruments` | `192.168.4.23:5000/hgumba-middleware:latest` | 5001–5005 | 1 | app |

### Arquitetura Final

```
Internet/NPM
    │
    ▼
proxy_network (overlay externa)
    │
    ├── app:8080  ← SENAITE LIS (Zope/Plone)
    │
senaite_net (overlay interna)
    │
    ├── db:5432   ← PostgreSQL CATSERV
    ├── middleware_gateway:8000 ← FastAPI (REST)
    └── middleware_instruments:5001-5005 ← Daemon TCP ASTM

192.168.4.23 (NFS Storage)
    ├── /data/senaite/var       → /opt/senaite/var  (ZODB Data.fs)
    └── /data/senaite/postgres  → /var/lib/postgresql/data
```

---

## 2. Compose Local → Swarm Stack

### Diagnóstico: o que muda

| Aspecto | `compose.local.yaml` (DEV) | Stack Swarm (PROD) |
|---------|---------------------------|-------------------|
| **Build** | `build:` local (senaite-hgumba:local) | Push para registry + `image:` |
| **Volumes DEV** | Bind mount `./src` (hot-reload) | Volume config `:ro` ou removido |
| **Entrypoint** | Entrypoint original | `startup.sh` wrapper com pip deps |
| **DB init** | `./db/init.sql:ro` | SQL inline ou ConfigMap |
| **Rede** | `bridge` | `overlay` |
| **Swarm** | `docker compose up` | `docker stack deploy` |

### Passo a Passo

#### 2.1. Build e Push das Imagens

```bash
# Imagem SENAITE (Dockerfile local)
docker build -t senaite-hgumba:local .
docker tag senaite-hgumba:local 192.168.4.23:5000/senaite:2.x
docker push 192.168.4.23:5000/senaite:2.x

# Imagem Middleware
cd hgumba-middleware
docker build -t hgumba-middleware:local .
docker tag hgumba-middleware:local 192.168.4.23:5000/hgumba-middleware:latest
docker push 192.168.4.23:5000/hgumba-middleware:latest
```

#### 2.2. Startup Wrapper (SENAITE app)

O container SENAITE precisa instalar deps Python antes de iniciar. No Swarm, isso é feito via `startup.sh`:

```bash
# Contedo de /opt/senaite/addons/startup.sh
#!/bin/bash
set -e
echo "=== Instalando senaite.hgumba dependencies ==="
pip install --no-deps matplotlib==2.2.5 reportlab Pillow numpy==1.16.6 \
  pyparsing==2.4.7 cycler kiwisolver python-dateutil six pytz \
  backports.functools-lru-cache subprocess32 archetypes.schemaextender
echo "=== Chaining to original entrypoint ==="
exec /docker-entrypoint.sh "$@"
```

Montado como bind volume `:ro` em todos os nós.

#### 2.3. Database Init

O SQL de criação da tabela CATSERV deve estar no nfs storage ou ser executado manualmente no primeiro deploy:

```bash
# Aplicar init.sql no PostgreSQL CATSERV
docker exec $(docker ps -f name=senaite_db -q) psql -U catserv -d financeiro -f /docker-entrypoint-initdb.d/01-init.sql
```

---

## 3. Volumes e Constraints (192.168.4.23)

### Princípio

O Storage primário `192.168.4.23` exporta NFS para todos os nós do Swarm. Volumes críticos (ZODB + PostgreSQL) **devem** residir neste storage, com constraints de placement para garantir que apenas nós com acesso NFS rodem os serviços de dados.

### 3.1. Criar os Volumes NFS

```bash
# No nó manager (docker-01), criar volumes que apontam para o NFS 192.168.4.23
docker volume create \
  --driver local \
  --opt type=nfs \
  --opt o=addr=192.168.4.23,rw,nfsvers=4,hard \
  --opt device=:/data/senaite/var \
  senaite_data

docker volume create \
  --driver local \
  --opt type=nfs \
  --opt o=addr=192.168.4.23,rw,nfsvers=4,hard \
  --opt device=:/data/senaite/postgres \
  pg_data
```

> **ATENÇÃO:** Volumes NFS precisam ser criados em **cada nó** que pode rodar o serviço. Para evitar esse trabalho manual, constraint `node.hostname == docker-01` é a abordagem mais segura.

### 3.2. Constraints de Placement

| Serviço | Constraint | Motivo |
|---------|-----------|--------|
| `app` (SENAITE) | `node.role == manager` | ZODB = escrita única; NFS montado no manager |
| `db` (PostgreSQL) | `node.hostname == docker-01` | PG data no NFS; evitar split-brain |
| `middleware_gateway` | _(nenhuma)_ | Pode rodar em qualquer nó |
| `middleware_instruments` | _(nenhuma)_ | Pode rodar em qualquer nó |

```yaml
# Exemplo no compose
app:
  deploy:
    placement:
      constraints:
        - node.role == manager
db:
  deploy:
    placement:
      constraints:
        - node.hostname == docker-01
```

### 3.3. Volumes no Stack Compose

```yaml
volumes:
  senaite_data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=192.168.4.23,rw,nfsvers=4,hard
      device: :/data/senaite/var
  pg_data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=192.168.4.23,rw,nfsvers=4,hard
      device: :/data/senaite/postgres
```

### 3.4. Estrutura de Diretórios no NFS

```
/data/senaite/
  var/                # ZODB — bind mount em /opt/senaite/var
    Data.fs           # Banco principal
    Data.fs.lock
    Data.fs.tmp
  postgres/           # PostgreSQL — bind mount em /var/lib/postgresql/data
    base/
    pg_wal/
    postgresql.conf
  init/               # Scripts de inicialização
    01-init.sql       # CREATE TABLE catserv
  addons/             # Add-on e startup.sh
    startup.sh
    src/              # Contedo de customizations/src/senaite.hgumba/src
    050-senaite-hgumba-configure.zcml
```

---

## 4. Redes Overlay

### 4.1. Criar as Redes

O Swarm requer redes `overlay` para comunicação entre nós. Duas redes são necessárias:

```bash
# Rede interna (servios se comunicam entre si)
docker network create \
  --driver overlay \
  --attachable \
  senaite_net

# Rede externa (proxy — j existente, verificar)
# Se for usar Nginx Proxy Manager, conectar tambm:
docker network create \
  --driver overlay \
  --attachable \
  proxy_network
```

### 4.2. Topologia de Rede

```
proxy_network (overlay)
  ├── app          ← porta 8080 exposta via NPM
  └── (nginx-proxy-manager)

senaite_net (overlay, attachable)
  ├── app          ← SENAITE LIS
  ├── db           ← PostgreSQL CATSERV
  ├── gateway      ← FastAPI
  └── instruments  ← Daemon ASTM
```

### 4.3. Atribuição de Redes por Serviço

| Serviço | `senaite_net` | `proxy_network` | Motivo |
|---------|:---:|:---:|--------|
| `app` | ✅ | ✅ | Acesso interno (gateway/db) + externo (NPM) |
| `db` | ✅ | ❌ | Só o gateway e o app precisam |
| `gateway` | ✅ | ❌ | Só precisa falar com app e db |
| `instruments` | ✅ | ❌ | Só precisa falar com app |

---

## 5. Deploy via MCP-GTI

### 5.1. Stack Compose Final

```yaml
# compose.stack.yaml — usar com docker stack deploy
version: "3.9"

services:
  app:
    image: 192.168.4.23:5000/senaite:2.x
    entrypoint: ["/bin/bash", "/opt/senaite/addons/startup.sh"]
    ports:
      - "8083:8080"
    volumes:
      - senaite_data:/opt/senaite/var
      - /opt/senaite/addons/src:/opt/senaite/addons/src:ro
      - /opt/senaite/addons/senaite-hgumba.pth:/usr/local/lib/python2.7/site-packages/senaite-hgumba.pth:ro
      - /opt/senaite/addons/package-includes:/home/senaite/senaitelims/parts/instance/etc/package-includes
      - /opt/senaite/addons/startup.sh:/opt/senaite/addons/startup.sh:ro
    environment:
      DB_HOST: db
      DB_PORT: "5432"
      DB_NAME: financeiro
      DB_USER: catserv
      DB_PASSWORD: /run/secrets/db_password
    secrets:
      - db_password
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.role == manager
      resources:
        limits:
          cpus: "1.5"
          memory: 2G
        reservations:
          cpus: "0.5"
          memory: 1G
    networks:
      - senaite_net
      - proxy_network

  db:
    image: postgres:13-alpine
    environment:
      POSTGRES_DB: financeiro
      POSTGRES_USER: catserv
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - pg_data:/var/lib/postgresql/data
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.hostname == docker-01
      resources:
        limits:
          cpus: "0.5"
          memory: 1G
        reservations:
          cpus: "0.25"
          memory: 512M
    networks:
      - senaite_net

  gateway:
    image: 192.168.4.23:5000/hgumba-middleware:latest
    command: uv run uvicorn main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      SENAITE_URL: "http://app:8080/senaite"
      SENAITE_USER: admin
      SENAITE_PASSWORD: admin
      DB_HOST: db
      DB_PORT: "5432"
      DB_NAME: financeiro
      DB_USER: catserv
      DB_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    deploy:
      mode: replicated
      replicas: 1
      resources:
        limits:
          cpus: "0.5"
          memory: 512M
        reservations:
          cpus: "0.25"
          memory: 256M
    networks:
      - senaite_net

  instruments:
    image: 192.168.4.23:5000/hgumba-middleware:latest
    command: uv run instrumentos --portas=5001,5002,5003,5004,5005
    ports:
      - "5001-5005:5001-5005"
    environment:
      SENAITE_URL: "http://app:8080/senaite"
      SENAITE_USER: admin
      SENAITE_PASSWORD: admin
    deploy:
      mode: replicated
      replicas: 1
      resources:
        limits:
          cpus: "0.5"
          memory: 512M
        reservations:
          cpus: "0.25"
          memory: 256M
    networks:
      - senaite_net

volumes:
  senaite_data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=192.168.4.23,rw,nfsvers=4,hard
      device: :/data/senaite/var
  pg_data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=192.168.4.23,rw,nfsvers=4,hard
      device: :/data/senaite/postgres

secrets:
  db_password:
    external: true

networks:
  senaite_net:
    external: true
  proxy_network:
    external: true
```

### 5.2. Comando de Deploy

```bash
# Via MCP-GTI (recomendado)
mcp-gti deploy_swarm_stack stack_name="senaite" compose_content="$(cat compose.stack.yaml)"

# Ou manualmente no manager
docker stack deploy -c compose.stack.yaml senaite
```

### 5.3. Antes do Primeiro Deploy

```bash
# 1. Criar redes
docker network create --driver overlay --attachable senaite_net
docker network create --driver overlay --attachable proxy_network

# 2. Criar secret da senha do banco
echo "catserv_secret" | docker secret create db_password -

# 3. Garantir que os diretórios NFS existem
# No 192.168.4.23:
mkdir -p /data/senaite/var /data/senaite/postgres /data/senaite/init /data/senaite/addons

# 4. Copiar startup.sh e add-on para o NFS
scp customizations/update_wrapper3.sh 192.168.4.23:/data/senaite/addons/
ssh 192.168.4.23 /data/senaite/addons/update_wrapper3.sh
```

---

## 6. Verificação Pós-Deploy

```bash
# Status da stack
docker stack ps senaite

# Logs do SENAITE
docker service logs senaite_app --tail 50

# Verificar se o site SENAITE foi criado
curl -s -o /dev/null -w "%{http_code}" http://localhost:8083/senaite/login

# Testar health do middleware
curl http://localhost:8000/health

# Testar criacao de AR via bypass
curl -X POST http://localhost:8000/@@hgumba-create-ar \
  -u admin:admin \
  -H "Content-Type: application/json" \
  -d '{"services":["GLI001"],"patient_name":"Deploy Test"}'

# Verificar trilha de auditoria
docker service logs senaite_gateway 2>&1 | grep "HGUMBA-Audit"
```

---

## 7. Rollback e Manutenção

### Rollback de Imagem

```bash
# Rollback para verso anterior
docker service update --rollback senaite_app

# Ou especificar imagem
docker service update --image 192.168.4.23:5000/senaite:2.x senaite_app
```

### Backup do ZODB Antes de Mudanças

```bash
# Parar o servio
docker service scale senaite_app=0

# Copiar Data.fs do volume NFS
cp /data/senaite/var/Data.fs /data/senaite/var/Data.fs.bkp.$(date +%Y%m%d_%H%M%S)

# Subir novamente
docker service scale senaite_app=1
```

### Atualização do Add-on

```bash
# 1. Copiar novo cdigo para o NFS
scp -r customizations/src/senaite.hgumba/src/* 192.168.4.23:/data/senaite/addons/src/

# 2. Restartar o servio
docker service update --force senaite_app
```

### Drenagem e Remocao da Stack

```bash
# Remover stack (dados persistem nos volumes)
docker stack rm senaite

# Remover volumes (cuidado — destri dados)
docker volume rm senaite_data pg_data

# Remover redes (se criadas para esta stack)
docker network rm senaite_net
```

---

## Checklist de Implantação

- [ ] Diretrios NFS criados em `192.168.4.23:/data/senaite/`
- [ ] `startup.sh` copiado e com permissão de execução
- [ ] Add-on source copiado para `/data/senaite/addons/src`
- [ ] `050-senaite-hgumba-configure.zcml` em `/data/senaite/addons/package-includes/`
- [ ] Imagens buildadas e pushed para `192.168.4.23:5000/`
- [ ] Redes overlay `senaite_net` e `proxy_network` criadas
- [ ] Secret `db_password` criada (`echo "senha" | docker secret create db_password -`)
- [ ] Primeiro acesso ao SENAITE e criação do site via `@@senaite-addsite`
- [ ] Seed executado via browser (`/senaite/@@hgumba-seed`)
- [ ] Middleware gateway responde em `:8000/health`
- [ ] Portas ASTM 5001–5005 acessíveis do switch do laboratório
- [ ] Audit trail verificável via `docker service logs senaite_gateway | grep HGUMBA`

---

*Documento gerado em 2026-05-19 | v1.0.0*
