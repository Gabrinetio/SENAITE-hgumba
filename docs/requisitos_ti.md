# Documento de Requisitos de Integração (Pós-Sigilo)

> **Destinatário:** Seção de Informática / Diretoria de Tecnologia da Informação do Exército
> **Objetivo:** Solicitar formalmente os dados técnicos, dicionários de dados, credenciais e liberações de rede necessários para a integração real do ecossistema SENAITE LIS via API Gateway com os sistemas homologados (SANDRA, SIRE e CADBEN).

---

## 1. Escopo da Integração

O API Gateway local (desenvolvido em Python 3.12+ / FastAPI) atuará como intermediário síncrono e assíncrono para garantir o fluxo ponta a ponta do Laboratório de Análises Clínicas (LAC). Para consolidar a interoperabilidade, dividimos os requisitos em três pilares funcionais.

```
┌─────────────────┐       (REST / JSON)       ┌────────────────────────┐
│   Middleware    │ <───────────────────────> │ SANDRA / SIRE / CADBEN │
│ (Porta 8000/TCP)│                           │    (Legado Exército)   │
└─────────────────┘                           └────────────────────────┘
```

---

## 2. Requisitos de Conectividade e Rede

Para que o Middleware (hospedado localmente em ambiente contêinerizado) consiga se comunicar com os barramentos de serviços do Exército, solicita-se a liberação das seguintes regras de Firewall/Proxy:

### 2.1. Tráfego de Saída (Outbound)
O Gateway local precisa consumir os *endpoints* centrais dos sistemas militares. Solicita-se liberação para os IPs/Domínios de Homologação e Produção nas seguintes portas:
* **Porta HTTP/HTTPS (80/443):** Para chamadas REST direcionadas ao CADBEN (Consulta de elegibilidade), SIRE (Validação de verba/guia) e SANDRA (Injeção de resultados).

### 2.2. Tráfego de Entrada (Inbound)
O sistema SANDRA precisará notificar o Middleware local quando uma nova Ordem de Serviço (pedido de exame) for gerada pelo médico assistente.
* **Porta Destino:** `8000/TCP` (ou porta customizada a ser definida em conjunto).
* **Protocolo:** REST / HTTP POST.

---

## 3. Especificações Técnicas dos Endpoints (Contratos de Dados)

Solicitamos o fornecimento da documentação técnica (*Swagger/OpenAPI*, esquemas JSON ou arquivos WSDL) correspondente aos seguintes fluxos:

### 3.1. Módulo CADBEN (Validação de Elegibilidade)
O Middleware precisa validar o status do beneficiário do FUSEX/SAMMED em tempo real antes da triagem da amostra.
* **Necessidade:** Endpoint de consulta por CPF ou Identidade Militar.
* **Campos requeridos no retorno:** Situação do cadastro (Ativo/Inativo), Nome Completo, Posto/Graduação, Categoria de Dependência e Margem/Elegibilidade para atendimento no LAC.

### 3.2. Módulo SIRE (Autorização e Custos)
Garantia de conformidade financeira para evitar a execução de procedimentos sem prévia cobertura orçamentária.
* **Necessidade:** Endpoint para verificação de número de guia de encaminhamento ou autorização prévia.
* **Campos requeridos no retorno:** Status da guia (Liberada/Pendente), código de barras associado e limite de exames permitidos.

### 3.3. Módulo SANDRA (Prontuário Eletrônico e Pedidos)
O coração da operação clínico-hospitalar.
* **Entrada no Middleware:** Layout do payload JSON enviado pelo SANDRA contendo a requisição médica (ID do pedido, dados do paciente, profissional solicitante e lista de códigos CATSERV dos exames).
* **Saída do Middleware (Devolução de Laudos):** Endpoint do SANDRA configurado para receber o laudo assinado eletronicamente pelo analista clínico (formato estruturado JSON + arquivo binário PDF em Base64 ou via *Multipart Form*).

---

## 4. Segurança, Autenticação e Criptografia

Considerando a criticidade e o sigilo das informações de saúde dos militares e seus dependentes, necessitamos da definição do padrão de segurança exigido pela Diretoria de TI do Exército:

* **Mecanismo de Autenticação:** Definição se a comunicação consumirá tokens **OAuth2 / JWT** (com rotatividade de chaves), chaves estáticas de API (`X-API-Key`) ou autenticação baseada em certificados de infraestrutura de chaves públicas.
* **Camada de Transporte (mTLS):** Confirmação se haverá exigência de autenticação mútua via TLS (mTLS) com troca de certificados digitais privativos entre as pontas.

---

## 5. Ambientes para Homologação

Para mitigar impactos em produção e cumprir a janela de 15 dias de validação técnica estipulada em edital, solicita-se:
1. Disponibilização de credenciais exclusivas para o **Ambiente de Homologação / Staging** das APIs do SANDRA, SIRE e CADBEN.
2. Massa de dados simulada (militar ativo, dependente elegível, dependente inelegível e guias rejeitadas) para execução dos testes de estresse e validação das regras do Pydantic no Gateway.
