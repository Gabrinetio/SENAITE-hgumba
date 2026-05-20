# Plano de Continuidade e Disaster Recovery (DRP)

> **Objetivo:** Estabelecer os procedimentos de backup a quente, failover e recuperaÃ§Ã£o de desastres para o ecossistema SENAITE LIS e Middleware HGUMBA garantindo o SLA de 98% e a preservaÃ§Ã£o do banco de dados (RDC 978/2025).

---

## 1. EstratÃ©gia de Backup (Hot Backup)

A arquitetura opera com dois bancos de dados distintos que exigem rotinas de backup independentes, executadas sem interrupÃ§Ã£o dos serviÃ§os.

### 1.1. ZODB (SENAITE LIS - Dados ClÃ­nicos)
O banco de dados orientado a objetos do Plone/SENAITE (`Data.fs`) nÃ£o pode ser copiado diretamente enquanto o contÃªiner estiver em execuÃ§Ã£o. Utiliza-se a ferramenta nativa `repozo` para backups incrementais e completos a quente.

* **FrequÃªncia:** Incremental a cada 4 horas; Completo (Full) aos domingos Ã s 02h00.
* **Comando de ExecuÃ§Ã£o (via host Swarm):**
  ```bash
  docker exec -it <id_container_senaite> bin/repozo -Bv -r /data/backup -f /data/filestorage/Data.fs
  ```
* **RetenÃ§Ã£o:** 30 dias de backups incrementais no volume de rede (NFS).

### 1.2. PostgreSQL (Middleware - MÃ³dulo CATSERV)

O banco de dados relacional que armazena a `tabela_catserv` e configuraÃ§Ãµes financeiras.

* **FrequÃªncia:** Dump completo diÃ¡rio (03h00).
* **Comando de ExecuÃ§Ã£o:**
```bash
docker exec -t <id_container_postgres> pg_dump -U catserv -F c financeiro > /var/backups/pg_financeiro_$(date +%Y%m%d).dump
```

---

## 2. Procedimentos de RecuperaÃ§Ã£o (Restore)

### 2.1. CorrupÃ§Ã£o do Data.fs (ZODB)

Caso o banco principal do laboratÃ³rio corrompa ou dados crÃ­ticos sejam perdidos:

1. Drene o nÃ³ ou pare o serviÃ§o temporariamente:
```bash
docker service scale senaite_app=0
```

2. Restaure o Ãºltimo estado vÃ¡lido utilizando o `repozo`:
```bash
docker run --rm -v senaite_data:/data senaite:2.x bin/repozo -Rv -r /data/backup -D <DATA_ALVO_YYYY-MM-DD> -o /data/filestorage/Data.fs
```

3. Reinicie o serviÃ§o:
```bash
docker service scale senaite_app=1
```

### 2.2. Perda da Tabela CATSERV (PostgreSQL)

1. Recrie o contÃªiner do banco, caso tenha sido destruÃ­do.
2. Restaure o dump mais recente:
```bash
docker exec -i <id_container_postgres> pg_restore -U catserv -d financeiro -1 < /var/backups/pg_financeiro_ultimo.dump
```

---

## 3. Plano de ContingÃªncia de Infraestrutura (Swarm)

* **Queda do NÃ³ Principal (Ex: 192.168.4.23):** Como os serviÃ§os estÃ£o fixados via *placement constraints*, em caso de falha catastrÃ³fica de hardware do servidor *bare-metal*, os volumes persistentes (`senaite_data` e `pgdata_financeiro`) montados via storage externo devem ser mapeados para um nÃ³ secundÃ¡rio.
* **RecuperaÃ§Ã£o de Rede:** Atualize as *constraints* no `deploy.yml` para apontar para o novo nÃ³ ativo e reimplante a *Stack*:
```bash
docker stack deploy -c deploy.yml senaite
```

---

## 4. Testes de ValidaÃ§Ã£o do DRP

* **Simulado Semestral:** A equipe de TI deve realizar um teste de *restore* do ZODB em um ambiente isolado (Docker Desktop local) a cada 6 meses, validando a integridade dos arquivos gerados pelo `repozo`.
