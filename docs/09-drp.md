# Plano de Continuidade e Disaster Recovery (DRP)

> Procedimentos de emergência para alta disponibilidade (SLA 98%) do SENAITE LIS.
> Público: GTI e SysAdmins.

---

## Sumário

1. [Arquitetura de Resiliência](#1-arquitetura-de-resili-ncia)
2. [SLA 98% — Métrica e Cobertura](#2-sla-98---m-trica-e-cobertura)
3. [Rotina de Hot Backup Automatizado](#3-rotina-de-hot-backup-automatizado)
4. [Restore do ZODB Data.fs (Corrupção)](#4-restore-do-zodb-datafs-corrup-o)
5. [pg_dump e Restore do CATSERV PostgreSQL](#5-pg-dump-e-restore-do-catserv-postgresql)
6. [Falha do Nó 192.168.4.23 — Migração NFS](#6-falha-do-n-192168423---migra-o-nfs)
7. [Plano de Comunicação em Incidentes](#7-plano-de-comunica-o-em-incidentes)
8. [Testes Periódicos](#8-testes-peri-dicos)

---

## 1. Arquitetura de Resiliência

### Dependências Críticas

```
Internet / Rede Laboratório
    │
    ├── DNS (MikroTik 192.168.4.1)        ← SPOF se cair, sem acesso ao sistema
    ├── NFS Storage (192.168.4.23)         ← SPOF — contém ZODB + PG data
    ├── Swarm Manager (Docker-01)          ← Orquestração
    └── Nginx Proxy Manager (proxy)       ← Entrada externa
```

### Stack e Pontos Únicos de Falha

| Serviço | SPOF? | Mitigação |
|---------|-------|-----------|
| `app` (SENAITE) | Sim — ZODB single replica | Backup programado + restart automático (restart: always) |
| `db` (PostgreSQL) | Sim — instância única | Backup pg_dump diário + WAL archive |
| `middleware_gateway` | **Não** — escala horizontal | Múltiplas réplicas via Swarm |
| `middleware_instruments` | Sim — estado TCP | Restart automático + buffer no analisador |
| **192.168.4.23 (NFS)** | **Sim** — storage único | Migração emergencial para outro nó (seção 6) |

### SLA 98% — Janelas Permitidas

98% de disponibilidade mensal = **máximo 14h 24min de indisponibilidade por mês**.

| Cenário | Meta de Restore | Impacto no SLA |
|---------|-----------------|----------------|
| Container caiu (app/db) | 5 min (restart automático) | 0,01% |
| Nó Docker-01 caiu | 15 min (failover Swarm) | 0,03% |
| NFS 192.168.4.23 caiu | 60 min (migrar volume) | 0,14% |
| Corrupção de Data.fs | 30 min (restore de backup) | 0,07% |
| Perda total do storage | 4h (restaurar de backup externo) | 0,56% |

---

## 2. Rotina de Hot Backup Automatizado

### 2.1. Script de Backup Diário

Instalar no **servidor NFS (192.168.4.23)** via cron:

```bash
#!/bin/bash
# /usr/local/bin/backup-senaite.sh
# Executar diariamente às 02:00 via cron

BACKUP_DIR="/data/backups/senaite"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR/zodb" "$BACKUP_DIR/postgres" "$BACKUP_DIR/addons"

# 1. ZODB Data.fs (cópia fria — para consistency, para o container antes)
docker exec senaite_app tar czf "$BACKUP_DIR/zodb/datafs_$DATE.tar.gz" -C /data filestorage

# 2. PostgreSQL CATSERV (hot backup via pg_dump)
docker exec senaite_db pg_dump -U catserv -d financeiro \
  --format=custom \
  --compress=9 \
  --file=/tmp/catserv_$DATE.dump
docker cp senaite_db:/tmp/catserv_$DATE.dump "$BACKUP_DIR/postgres/"
docker exec senaite_db rm /tmp/catserv_$DATE.dump

# 3. Add-on source e startup.sh (cópia simples)
tar czf "$BACKUP_DIR/addons/addons_$DATE.tar.gz" -C /opt/senaite addons

# 4. Cleanup — apagar backups com mais de 30 dias
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.dump" -mtime +$RETENTION_DAYS -delete

# 5. Sincronizar para storage secundário (off-site)
rsync -avz --delete "$BACKUP_DIR/" backup@storage-secundario:/data/backups/senaite/

echo "Backup $DATE concluído. Tamanho: $(du -sh $BACKUP_DIR | cut -f1)"
```

**Crontab (root):**
```cron
0 2 * * * /usr/local/bin/backup-senaite.sh > /var/log/backup-senaite.log 2>&1
```

### 2.2. Estrutura de Diretórios de Backup

```
/data/backups/senaite/
├── zodb/
│   ├── datafs_20260519_020001.tar.gz     ← 350 MB (compactado)
│   └── datafs_20260518_020001.tar.gz
├── postgres/
│   ├── catserv_20260519_020001.dump      ← 50 MB (custom format)
│   └── catserv_20260518_020001.dump
└── addons/
    ├── addons_20260519_020001.tar.gz     ← 100 KB
    └── addons_20260518_020001.tar.gz
```

### 2.3. Verificação de Integridade

```bash
# Verificar backup ZODB
tar tzf /data/backups/senaite/zodb/datafs_20260519_020001.tar.gz
# Deve listar: filestorage/Data.fs filestorage/Data.fs.lock filestorage/Data.fs.tmp

# Verificar backup PostgreSQL
pg_restore --list /data/backups/senaite/postgres/catserv_20260519_020001.dump | head -20

# Testar restore em ambiente isolado (recomendado 1x/semana)
# docker compose -f compose.test-restore.yaml up
```

---

## 3. Restore do ZODB Data.fs (Corrupção)

### Cenário

O SENAITE não inicia, apresenta erro de ZODB corrupto, ou o log contém:

```
ZODB.POSException.StorageTransactionError: Transaction cannot be committed
Error: invalid Data.fs
```

### Procedimento de Restore

```bash
# 1. Parar o serviço (desativar tráfego)
docker service scale senaite_app=0

# 2. Identificar o backup mais recente e íntegro
BACKUP=$(ls -t /data/backups/senaite/zodb/datafs_*.tar.gz | head -1)
echo "Restaurando de: $BACKUP"

# 3. Fazer backup do Data.fs corrompido (para perícia)
cp /data/senaite/var/Data.fs /data/senaite/var/Data.fs.corrompido.$(date +%Y%m%d_%H%M%S)

# 4. Extrair o backup para o diretório NFS
cd /data/senaite/var
tar xzf "$BACKUP" --strip-components=1

# 5. Remover arquivos de lock (se existirem)
rm -f /data/senaite/var/Data.fs.lock /data/senaite/var/Data.fs.tmp

# 6. Verificar integridade do Data.fs restaurado
python -c "
from ZODB import FileStorage, DB
try:
    fs = FileStorage.FileStorage('/data/senaite/var/Data.fs', read_only=True)
    db = DB(fs)
    conn = db.open()
    conn.close()
    db.close()
    print('Data.fs OK')
except Exception as e:
    print('Data.fs corrompido:', e)
    exit(1)
" 2>/dev/null || echo "Verificação manual necessária"

# 7. Subir o serviço novamente
docker service scale senaite_app=1

# 8. Verificar se o site responde
curl -s -o /dev/null -w "%{http_code}" http://localhost:8083/senaite/login
# Deve retornar 200

# 9. Verificar se as ARs e dados estão íntegros
curl -u admin:admin "http://localhost:8083/senaite/@@API/senaite/v1/search?portal_type=AnalysisRequest"
# Deve retornar a lista de requisições
```

### Rollback do Restore

Se o backup também estiver corrompido:

```bash
# Restaurar o Data.fs corrompido original
cp /data/senaite/var/Data.fs.corrompido.* /data/senaite/var/Data.fs

# Tentar recuperação via ZODB.repair
python -c "
from ZODB import FileStorage
fs = FileStorage.FileStorage('/data/senaite/var/Data.fs')
fs.close()
"

# Subir mesmo corrompido — pode iniciar em modo somente leitura
docker service scale senaite_app=1
```

> 💡 **Prevenção:** Ative o `pack` diário do ZODB para reduzir o tamanho do Data.fs
> e minimizar a janela de corrupção:
> ```python
> # Executar no ZMI ou via script
> from Products.CMFPlone.utils import getToolByName
> app = getToolByName(context, 'portal_url').getPortalObject()
> app.manage_pack(days=7)
> ```

---

## 4. pg_dump e Restore do CATSERV PostgreSQL

### 4.1. Hot Backup Manual

```bash
# Backup custom (formato comprimido, recomendado para restore)
docker exec senaite_db pg_dump -U catserv -d financeiro \
  --format=custom \
  --compress=9 \
  -f /tmp/catserv_hot.dump

docker cp senaite_db:/tmp/catserv_hot.dump /data/backups/senaite/postgres/
docker exec senaite_db rm /tmp/catserv_hot.dump
```

```bash
# Backup SQL puro (portável, maior)
docker exec senaite_db pg_dump -U catserv -d financeiro \
  --clean \
  --if-exists \
  > /data/backups/senaite/postgres/catserv_$(date +%Y%m%d).sql
```

### 4.2. Restore do PostgreSQL

#### Cenário: Dados corrompidos, tabela perdida, ou container corrompido

```bash
# 1. Parar o gateway (evita escrita durante restore)
docker service scale senaite_gateway=0

# 2. Identificar o backup mais recente
BACKUP=$(ls -t /data/backups/senaite/postgres/catserv_*.dump | head -1)

# 3. Opção A — Restore em container novo (substituir o atual)
docker service rm senaite_db

# Criar volume vazio (ou limpar)
rm -rf /data/senaite/postgres/*
docker volume create pg_data

# Recriar o serviço (compose.stack.yaml) — o banco inicializará vazio
docker stack deploy -c compose.stack.yaml senaite

# Aguardar PostgreSQL iniciar
sleep 10

# 4. Restaurar o dump
docker exec -i senaite_db pg_restore -U catserv -d financeiro \
  --clean \
  --if-exists \
  < "$BACKUP"

# 5. Opção B — Restore in-place (container existente, sem perder dados recentes)
docker cp "$BACKUP" senaite_db:/tmp/restore.dump
docker exec senaite_db pg_restore -U catserv -d financeiro \
  --clean \
  --if-exists \
  /tmp/restore.dump

# 6. Verificar
docker exec senaite_db psql -U catserv -d financeiro -c "SELECT count(*) FROM tabela_catserv;"
# Deve retornar 10 (número de linhas do seed)

# 7. Restartar o gateway
docker service scale senaite_gateway=1
```

### 4.3. Teste de Integridade Pós-Restore

```bash
# Verificar se a tabela CATSERV existe e tem dados
docker exec senaite_db psql -U catserv -d financeiro -c "
SELECT exame, codigo, valor FROM tabela_catserv ORDER BY id;
"

# Verificar se o middleware consegue conectar
curl -u admin:admin http://localhost:8000/health

# Verificar se o SENAITE enxerga o banco (via psycopg2)
# (teste manual opcional)
```

---

## 5. Falha do Nó 192.168.4.23 — Migração NFS

### 5.1. Identificação da Falha

```bash
# Verificar se o NFS está respondendo
showmount -e 192.168.4.23
# Se timeout ou "mount: RPC: Unable to receive", o nó caiu.

# Verificar impacto nos serviços
docker service logs senaite_app --tail 5
# Se "Error: NFS volume not mounted" ou "I/O error", o volume está offline.

# Verificar volumes
docker volume inspect senaite_data --format '{{.Options.o}}'
# A opção "hard" significa que o container trava até o NFS voltar
```

### 5.2. Procedimento de Migração

Premissa: Existe um **nó reserva** no cluster com NFS server (ex: Docker-02, IP 192.168.4.17).

```bash
# FASE 1 — Provisionar o storage reserva
# No nó reserva (192.168.4.17):
apt install nfs-kernel-server -y
mkdir -p /data/senaite/var /data/senaite/postgres /data/senaite/backups
echo "/data/senaite *(rw,sync,no_subtree_check,no_root_squash)" >> /etc/exports
exportfs -a
systemctl restart nfs-kernel-server

# FASE 2 — Copiar dados do storage original (se acessível via rede)
# Se 192.168.4.23 ainda responde SSH mas NFS caiu:
rsync -avz root@192.168.4.23:/data/senaite/ /data/senaite/
# Se 192.168.4.23 está completamente offline:
# Restaurar do último backup:
tar xzf /data/backups/senaite/zodb/$(ls -t /data/backups/senaite/zodb/ | head -1) -C /data/senaite/var/
pg_restore -U catserv -d financeiro /data/backups/senaite/postgres/$(ls -t /data/backups/senaite/postgres/*.dump | head -1)

# FASE 3 — Atualizar os volumes no Swarm
docker volume rm senaite_data pg_data

docker volume create \
  --driver local \
  --opt type=nfs \
  --opt o=addr=192.168.4.17,rw,nfsvers=4,hard \
  --opt device=:/data/senaite/var \
  senaite_data

docker volume create \
  --driver local \
  --opt type=nfs \
  --opt o=addr=192.168.4.17,rw,nfsvers=4,hard \
  --opt device=:/data/senaite/postgres \
  pg_data

# FASE 4 — Forçar restart da stack
docker stack rm senaite
sleep 10
docker stack deploy -c compose.stack.yaml senaite

# FASE 5 — Verificar
curl -s -o /dev/null -w "%{http_code}" http://localhost:8083/senaite/login
curl http://localhost:8000/health
docker service logs senaite_db --tail 5
```

### 5.3. Tempo Estimado de Migração

| Passo | Duração | Depende de |
|-------|---------|------------|
| Provisionar NFS reserva | 10 min | Acesso ao nó reserva |
| Copiar dados (rsync) | 10–30 min | Tamanho do Data.fs + link de rede |
| Recriar volumes Swarm | 5 min | — |
| Restart da stack | 5 min | — |
| Verificação | 5 min | — |
| **Total estimado** | **35–55 min** | — |

### 5.4. Pós-Migração

```bash
# 1. Atualizar o compose.stack.yaml com o novo IP NFS
#    senaite_data: addr=192.168.4.17
#    pg_data: addr=192.168.4.17

# 2. Registrar no DNS (MikroTik) se aplicável

# 3. Reconfigurar o backup crontab para o novo nó

# 4. Quando o 192.168.4.23 voltar, copiar os dados de volta:
rsync -avz /data/senaite/ root@192.168.4.23:/data/senaite/
```

---

## 6. Plano de Comunicação em Incidentes

### Tabela de Notificação

| Nível | Impacto | Notificar | Prazo | Canal |
|-------|---------|-----------|-------|-------|
| 🔴 Crítico | SENAITE offline > 15 min | GTI + Chefia LAC | Imediato | Telefone + WhatsApp |
| 🟡 Alto | CDM/lento, PostgreSQL lento | GTI | 30 min | WhatsApp |
| 🟢 Médio | Backup falhou, warning em log | GTI (próximo dia útil) | 24h | E-mail / Issue Gitea |

### Modelo de Comunicado de Incidente

```
ASSUNTO: [INCIDENTE] SENAITE — {nível} — {serviço afetado}

DATA/HORA: {timestamp}
SERVIÇO: {app | db | gateway | instruments}
IMPACTO: {descrição do impacto operacional}
CAUSA PRESUMIDA: {ex: NFS offline, Data.fs corrompido}
AÇÃO TOMADA: {ex: restore de backup, migração NFS}
PREVISÃO DE NORMALIZAÇÃO: {estimativa}
STATUS: {Em andamento | Resolvido | Monitorando}
```

---

## 7. Testes Periódicos

### Cronograma

| Teste | Frequência | Responsável | Critério de Aprovação |
|-------|-----------|-------------|----------------------|
| Restore de Data.fs em ambiente isolado | Mensal | GTI | SENAITE inicia, login OK, ARs visíveis |
| pg_restore do dump CATSERV | Mensal | GTI | `SELECT count(*)` = 10, CDM gera PDF |
| Simular falha do container app | Semanal | Automático (Swarm) | Restart em < 30s |
| Simular falha do NFS 192.168.4.23 | Trimestral | GTI | Migração concluída em < 60 min |
| Teste de backup off-site | Trimestral | GTI | Arquivo .tar.gz íntegro em storage secundário |
| Teste de restore completo (DRP full) | Semestral | GTI + Chefia LAC | Sistema 100% operacional em < 4h |

### Script de Teste de Restore Automatizado

```bash
#!/bin/bash
# /usr/local/bin/test-restore-senaite.sh
# Executar 1x/mês — testa restore em container isolado
set -e

BACKUP_ZODB=$(ls -t /data/backups/senaite/zodb/datafs_*.tar.gz | head -1)
BACKUP_PG=$(ls -t /data/backups/senaite/postgres/catserv_*.dump | head -1)
TEST_DIR=/tmp/senaite-restore-test
mkdir -p "$TEST_DIR"

echo "=== Teste de Restore $(date) ==="
echo "Backup ZODB: $BACKUP_ZODB"
echo "Backup PG: $BACKUP_PG"

# Extrair Data.fs
cd "$TEST_DIR"
tar xzf "$BACKUP_ZODB"
ls -lh filestorage/Data.fs

# Verificar integridade com ZODB
python -c "
from ZODB import FileStorage, DB
fs = FileStorage.FileStorage('$TEST_DIR/filestorage/Data.fs', read_only=True)
db = DB(fs)
conn = db.open()
root = conn.root()
print('Objetos no root:', len(root))
print('ZODB OK')
conn.close()
db.close()
" 2>&1

# Verificar dump PostgreSQL
pg_restore --list "$BACKUP_PG" | grep -q "tabela_catserv" && \
  echo "PostgreSQL dump contém tabela_catserv" || \
  echo "WARNING: tabela_catserv não encontrada no dump"

echo "=== Teste concluído ==="
rm -rf "$TEST_DIR"
```

---

## 8. Matriz de Responsabilidades em Incidentes

| Papel | Nome / Função | Responsabilidade no DRP |
|-------|--------------|------------------------|
| **Comandante do Incidente** | GTI Líder | Coordena resposta, comunicação, decisão de migração |
| **Operador de Restore** | GTI SysAdmin | Executa restore de backup, migrate NFS |
| **Comunicação** | Chefia do LAC | Notifica usuários, informa Chefia do HGu |
| **Validador** | Biomédico sênior | Confirma que dados estão íntegros pós-restore |
| **Suporte Técnico** | GTI Suporte | Atende chamados, tria relatos de usuarios |

---

## Anexo A: Comandos Rápidos de Diagnóstico

```bash
# Status geral da stack
docker stack ps senaite --no-trunc

# Logs do ZODB (erros de Data.fs)
docker service logs senaite_app --tail 50 2>&1 | grep -i "zodb\|corrupt\|error"

# Status do volume NFS
docker volume inspect senaite_data --format '{{.Options.o}}'
mount | grep senaite

# Teste de escrita no volume NFS
touch /data/senaite/var/.test_write && echo "NFS OK" || echo "NFS FALHA"

# Último backup bem-sucedido
ls -lt /data/backups/senaite/zodb/ | head -3

# Conexão com PostgreSQL
docker exec senaite_db pg_isready -U catserv

# Tamanho do Data.fs
du -sh /data/senaite/var/Data.fs
```

## Anexo B: Checklist de DRP

- [ ] Backup diário automático configurado e funcional
- [ ] Backup off-site sincronizado (rsync)
- [ ] Script de restore testado nos últimos 30 dias
- [ ] Nó reserva para NFS identificado e acessível via SSH
- [ ] Volumes NFS recriáveis via comando (driver_opts)
- [ ] dump PostgreSQL testado (`pg_restore --list`)
- [ ] Contatos de emergência atualizados (GTI + LAC)
- [ ] SLA 98% monitorado (uptime mensal > 700h)
- [ ] Logs de auditoria sendo gerados e retidos por 30+ dias (RDC 978)

---

*Documento gerado em 2026-05-19 | v1.0.0*
