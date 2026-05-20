# POP ” Manual do Operador do LAC

> Procedimento Operacional Padrão para recepcionistas, biomédicos e médicos militares
> do Laboratório de Análises Clínicas (LAC) do HGUMBA

---

## Sumário

1. [Acessar o Sistema](#1-acessar-o-sistema)
2. [Cadastrar um Paciente com Médico Solicitante](#2-cadastrar-um-paciente-com-m-dico-solicitante)
3. [Solicitar Exames com Múltiplos Médicos (CoPhysicians)](#3-solicitar-exames-com-m-ltiplos-m-dicos-cophysicians)
4. [Gerar o PDF do CDM (Faturamento)](#4-gerar-o-pdf-do-cdm-faturamento)
5. [Interpretar Flags [ALTO] e [BAIXO] nos Laudos](#5-interpretar-flags-alto-e-baixo-nos-laudos)
6. [Assinar e Publicar o Laudo (Publish → SANDRA)](#6-assinar-e-publicar-o-laudo-publish-sandra)
7. [Verificar se o Laudo Chegou ao SANDRA](#7-verificar-se-o-laudo-chegou-ao-sandra)
8. [Solução de Problemas Comuns](#8-solu-o-de-problemas-comuns)

---

## 1. Acessar o Sistema

### Pelo Computador do Laboratório

| Informação | Valor |
|-----------|-------|
| **URL** | `http://senaite.gti.local/senaite` (ou o IP definido pela TI) |
| **Usuário** | Seu login do SENAITE (fornecido pela chefia) |
| **Senha** | Sua senha pessoal |

### Tela Inicial

Após o login, você verá o painel principal do SENAITE com:

- **Clients** → Clique em "HGU" para acessar os pacientes e requisições do hospital
- **Analysis Requests** → Lista de todas as requisições de exames pendentes e concluídas
- **Tasks** → Suas tarefas pendentes (resultados para liberar)

---

## 2. Cadastrar um Paciente com Médico Solicitante

### Passo a Passo

1. No menu lateral, clique em **Clients** → **HGU**
2. Clique na aba **Analysis Requests**
3. Clique no botão **Add** (ou o ícone de "+" no canto superior direito)

   ![Add AR]

4. Preencha o formulário:

   | Campo | O que preencher | Exemplo |
   |-------|----------------|---------|
   | **Title / ID** | Código de identificação da requisição | `HGU-AR-042` |
   | **Patient Full Name** | Nome completo do paciente | `MARIA DA SILVA SANTOS` |
   | **Medical Record Number (MRN)** | RG / CPF / prontuário | `12345678901` ou `MRN-042` |
   | **Client** | Deve vir preenchido como "HGU" | `HGU` |
   | **Primary Physician / Médico Solicitante** | Nome do médico que pediu o exame | `Dr. CARLOS ALMEIDA` |

5. Role para baixo e clique em **Save**

> âš ï¸ **Importante:** O campo **Medical Record Number** é usado para vincular o paciente ao histórico de exames anteriores. Sempre preencha com o CPF ou número de prontuário.

---

## 3. Solicitar Exames com Múltiplos Médicos (CoPhysicians)

Quando um paciente é atendido por **mais de um médico** (ex: clínico geral + infectologista + cirurgião), todos devem constar no laudo para faturamento.

### Como Adicionar Médicos Adicionais

1. Na tela de criação/edição da **Analysis Request**, localize o campo
   **Co-Profissionais Solicitantes** (fica logo abaixo do campo "Primary Physician")

   ![CoPhysicians field]

2. Clique no campo de busca e digite o nome do médico adicional
3. Selecione o nome na lista que aparece
4. Repita para cada médico que deseja adicionar
5. Clique em **Save**

### Como Fica no CDM

No PDF do CDM, os médicos aparecem assim:

```
Profissionais Solicitantes:
- Dr. CARLOS ALMEIDA (principal)
- Dr. ANA BEATRIZ PEREIRA (co-solicitante)
- Dr. JOSE ROBERTO LIMA (co-solicitante)
```

> ðŸ’¡ **Dica:** Use o CoPhysicians para médicos que acompanham o caso mas não são o solicitante principal. Isso garante que todos os profissionais sejam cobrados corretamente no faturamento.

---

## 4. Gerar o PDF do CDM (Faturamento)

O **Comprovante de Despesas Médicas (CDM)** é o documento que lista os exames realizados e seus valores para cobrança.

### Como Gerar

1. Na lista de **Analysis Requests**, encontre a requisição desejada
2. Clique no **ID** da requisição para abrir os detalhes
3. Na barra de ações, clique no botão **CDM PDF** (ou acesse diretamente:

   ```
   http://senaite.gti.local/senaite/clients/hgu/HGU-AR-042/@@cdm-pdf
   ```

4. O navegador fará o download de um arquivo PDF com nome `cdm_HGU-AR-042.pdf`

### O Que Vem no PDF

```
┌──────────────────────────────────────────────┐
│        COMPROVANTE DE DESPESAS MÃ‰DICAS        │
│                                              │
│  Requisição: HGU-AR-042                      │
│  Paciente: MARIA DA SILVA SANTOS             │
│                                              │
│  Profissionais Solicitantes:                 │
│   - Dr. CARLOS ALMEIDA (principal)           │
│   - Dr. ANA BEATRIZ PEREIRA (co-solicitante) │
│                                              │
│  Exame            Código     Valor           │
│  ─────────────────────────────────────        │
│  Glicemia         03.02.005  R$ 8,90         │
│  Hemograma        01.01.001  R$ 12,50        │
│  Colesterol Total 04.01.001  R$ 15,00        │
│                              ─────────        │
│                     TOTAL:   R$ 36,40         │
└──────────────────────────────────────────────┘
```

### Para Imprimir

- Abra o PDF baixado
- Clique em **Arquivo → Imprimir** (ou `Ctrl + P`)
- Escolha a impressora do laboratório
- O CDM impresso deve acompanhar a requisição física para o setor de faturamento

---

## 5. Interpretar Flags [ALTO] e [BAIXO] nos Laudos

Quando um resultado de exame está **fora do intervalo de referência**, o laudo exibe
uma flag visível:

| Flag | Significado | Exemplo |
|------|-------------|---------|
| **[ALTO]** | Resultado acima do valor máximo esperado | Glicemia 200 mg/dL (normal até 99) |
| **[BAIXO]** | Resultado abaixo do valor mínimo esperado | Hemoglobina 8 g/dL (normal 12-16) |

### Como Aparece no Laudo

```
┌──────────────────────────────────────────────┐
│              LAUDO DE EXAMES                  │
│                                              │
│  Paciente: MARIA DA SILVA SANTOS             │
│  Requisição: HGU-AR-042                      │
│                                              │
│  Glicemia: 200.0 mg/dL  **[ALTO]**           │
│  Hemoglobina: 8.0 g/dL  **[BAIXO]**          │
│  Colesterol: 180.0 mg/dL                     │
│                                              │
│  ── Gráfico de Histórico: Glicemia ──        │
│  [gráfico mostrando evolução]                │
└──────────────────────────────────────────────┘
```

### O Que Fazer

| Quem | Ação |
|------|------|
| **Biomédico** | Verificar se o valor faz sentido clínico. Se o equipamento estava calibrado, se a amostra não hemolisou. Se houver dúvida, repetir o exame. |
| **Médico** | Analisar o resultado no contexto do paciente. A flag é um alerta, não um diagnóstico. |
| **Recepcionista** | Ao imprimir o laudo, a flag aparece automaticamente no PDF. Não precisa fazer nada adicional. |

> âš ï¸ **Critérios de Rejeição:** Se o resultado estiver **muito acima** do crítico
> (ex: glicemia > 500 mg/dL), o sistema registra um alerta. O biomédico deve
> **repetir a dosagem** antes de liberar.

---

## 6. Assinar e Publicar o Laudo (Publish → SANDRA)

Após os resultados ficarem prontos, o laudo precisa ser **assinado eletronicamente**
(publicado) para que:
1. O PDF seja gerado com o status oficial
2. O sistema envie automaticamente o laudo para o prontuário do paciente no **SANDRA**

### Fluxo de Publicação

```
Resultados digitados/importados
        │
        ▼
   Biomédico verifica resultados
   (confere flags [ALTO]/[BAIXO])
        │
        ▼
   Biomédico clica em "Publish" (Assinar)
        │
        ▼
   Laudo muda para estado "published"
        │
        ▼
   Sistema envia PDF para o SANDRA (automático)
        │
        ▼
   Médico acessa o laudo pelo prontuário no SANDRA
```

### Passo a Passo

1. Na lista de **Analysis Requests**, localize a requisição com resultados prontos
2. Abra a requisição clicando no ID
3. Verifique os resultados na aba **Analyses**

   - Confira se todos os exames solicitados estão preenchidos
   - Veja se há flags **[ALTO]** ou **[BAIXO]** ” se houver, o biomédico deve validar

4. Clique no botão **Publish** (no topo da tela)

5. Confirme a ação na janela que aparece:

   ```
   ┌─────────────────────────────────────┐
   │  Publicar Análises                  │
   │                                     │
   │  Deseja publicar esta requisição?   │
   │  O laudo será enviado ao SANDRA.    │
   │                                     │
   │  [Cancelar]  [Confirmar]            │
   └─────────────────────────────────────┘
   ```

6. Após confirmar, o estado muda para **`published`**

   - Uma mensagem verde aparece: "Análises publicadas com sucesso"
   - O PDF do laudo é gerado automaticamente
   - O sistema envia o PDF para o SANDRA (prontuário) em segundos

### Verificação

Após publicar, você pode:

- Ver o status na lista: o ícone da requisição muda para verde (publicado)
- Clicar em **View PDF** para visualizar o laudo final
- Na aba **History**, ver o registro: "Transition: publish → published by usuario"

---

## 7. Verificar se o Laudo Chegou ao SANDRA

Após a publicação, o sistema tenta enviar o laudo automaticamente para o SANDRA.
Você pode confirmar se deu certo:

### Pelo SENAITE

1. Abra a requisição publicada
2. Role até o campo **Remarks**
3. Se o envio foi bem-sucedido, não aparece mensagem de erro
4. Se houve falha, a equipe de TI verá nos logs do sistema

### Pelo SANDRA (Prontuário)

1. Acesse o prontuário do paciente no SANDRA
2. Procure a seção de **Resultados de Exames** ou **Laudos**
3. O laudo deve aparecer listado com o ID da requisição

> â±ï¸ O envio ao SANDRA leva **segundos** após a publicação. Se não aparecer
> em até 5 minutos, comunique a TI.

---

## 8. Solução de Problemas Comuns

| Problema | Causa Provável | O Que Fazer |
|----------|---------------|-------------|
| **Não consigo acessar o sistema** | Senha errada ou usuário bloqueado | Solicitar reset de senha à TI |
| **O médico não aparece na busca do CoPhysicians** | Médico não cadastrado no sistema | Solicitar à TI o cadastro do médico |
| **O PDF do CDM não abre** | Pop-up bloqueado pelo navegador | Permitir pop-ups do site do SENAITE |
| **Flag [ALTO] aparece mas o valor parece normal** | Intervalo de referência do sistema diferente do laboratório | O biomédico deve verificar e ajustar se necessário |
| **Botão Publish não aparece** | Usuário não tem permissão | Solicitar à TI que libere a permissão "Manage Analysis Requests" |
| **O laudo publicado não aparece no SANDRA** | Falha de comunicação entre sistemas | Informar a TI para verificar os logs de auditoria |
| **Resultado de exame não veio do equipamento** | Analisador não conectou ou frame ASTM rejeitado | Verificar se o equipamento está ligado e conectado à rede |
| **A lista de pacientes está muito lenta** | Muitas requisições abertas | Usar o campo de busca para filtrar por ID ou nome |

---

## Glossário

| Termo | Significado |
|-------|-------------|
| **AR / Analysis Request** | Requisição de análise ” o "pedido de exame" |
| **CDM** | Comprovante de Despesas Médicas ” usado para faturamento |
| **CoPhysicians** | Médicos co-solicitantes ” profissionais adicionais que acompanham o caso |
| **MRN** | Medical Record Number ” número de prontuário do paciente |
| **Publish** | Ação de assinar e publicar o laudo, tornando-o oficial |
| **SANDRA** | Sistema de prontuário do Exército |
| **Flag [ALTO]/[BAIXO]** | Indicador de resultado fora do intervalo de referência |
| **Remarks** | Campo de observações na requisição (usado para trilha de auditoria) |

---

## Anexo: Checklist Diário do Operador

### Recepcionista (Início do Turno)

- [ ] Login no SENAITE OK
- [ ] Conferir se há pedidos do SANDRA para cadastrar
- [ ] Cadastrar pacientes com MRN e médico solicitante
- [ ] Adicionar CoPhysicians quando houver múltiplos médicos
- [ ] Imprimir CDM e encaminhar ao faturamento

### Biomédico (Durante o Turno)

- [ ] Verificar resultados que chegaram dos analisadores
- [ ] Conferir flags [ALTO] e [BAIXO] ” validar clinicamente
- [ ] Se necessário, repetir exames com flags críticas
- [ ] Publicar (assinar) laudos com resultados OK

### Médico / Chefia (Fim do Turno)

- [ ] Conferir se todos os laudos do dia foram publicados
- [ ] Verificar se há pendências na lista de Analysis Requests
- [ ] Se houver laudo não publicado, identificar o motivo e resolver

---

*Documento gerado em 2026-05-19 | v1.0.0*
