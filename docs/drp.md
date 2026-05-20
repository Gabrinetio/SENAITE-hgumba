# Plano de Continuidade e Disaster Recovery (DRP)

> **Objetivo:** Estabelecer os procedimentos de backup a quente, failover e recuperação de desastres para o ecossistema SENAITE LIS e Middleware HGUMBA garantindo o SLA de 98% e a preservação do banco de dados (RDC 978/2025).

---

## 1. Estratégia de Backup (Hot Backup)

A arquitetura opera com dois bancos de dados distintos que exigem rotinas de backup independentes, executadas sem interrupção dos serviços.

### 1.1. ZODB (SENAITE LIS - Dados Clínicos)
O banco de dados orientado a objetos do Plone/SENAITE (`Data.fs`) não pode ser copiado diretamente enquanto o contêiner estiver em execução. Utiliza-se a ferramenta nativa `repozo` para backups incrementais e completos a quente.

* **Frequência:** Incremental a cada 4 horas; Completo (Full) aos domingos às 02h00.
* **Comando de Execução (via host Swarm):**
  ```bash
  docker exec -it <id_container_senaite> bin/repozo -Bv -r /data/backup -f /data/filestorage/Data.fs
  ```
* **Retenção:** 30 dias de backups incrementais no volume de rede (NFS).

### 1.2. PostgreSQL (Middleware - Módulo CATSERV)

O banco de dados relacional que armazena a `tabela_catserv` e configurações financeiras.

* **Frequência:** Dump completo diário (03h00).
* **Comando de Execução:**
```bash
docker exec -t <id_container_postgres> pg_dump -U catserv -F c financeiro > /var/backups/pg_financeiro_$(date +%Y%m%d).dump
```

---

## 2. Procedimentos de Recuperação (Restore)

### 2.1. Corrupção do Data.fs (ZODB)

Caso o banco principal do laboratório corrompa ou dados críticos sejam perdidos:

1. Drene o nó ou pare o serviço temporariamente:
```bash
docker service scale senaite_app=0
```

2. Restaure o último estado válido utilizando o `repozo`:
```bash
docker run --rm -v senaite_data:/data senaite:2.x bin/repozo -Rv -r /data/backup -D <DATA_ALVO_YYYY-MM-DD> -o /data/filestorage/Data.fs
```

3. Reinicie o serviço:
```bash
docker service scale senaite_app=1
```

### 2.2. Perda da Tabela CATSERV (PostgreSQL)

1. Recrie o contêiner do banco, caso tenha sido destruído.
2. Restaure o dump mais recente:
```bash
docker exec -i <id_container_postgres> pg_restore -U catserv -d financeiro -1 < /var/backups/pg_financeiro_ultimo.dump
```

---

## 3. Plano de Contingência de Infraestrutura (Swarm)

* **Queda do Nó Principal (Ex: 192.168.4.23):** Como os serviços estão fixados via *placement constraints*, em caso de falha catastrófica de hardware do servidor *bare-metal*, os volumes persistentes (`senaite_data` e `pgdata_financeiro`) montados via storage externo devem ser mapeados para um nó secundário.
* **Recuperação de Rede:** Atualize as *constraints* no `deploy.yml` para apontar para o novo nó ativo e reimplante a *Stack*:
```bash
docker stack deploy -c deploy.yml senaite
```

---

## 4. Testes de Validação do DRP

* **Simulado Semestral:** A equipe de TI deve realizar um teste de *restore* do ZODB em um ambiente isolado (Docker Desktop local) a cada 6 meses, validando a integridade dos arquivos gerados pelo `repozo`.
