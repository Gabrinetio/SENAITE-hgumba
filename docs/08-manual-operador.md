# POP â€” Manual do Operador do LAC

> Procedimento Operacional PadrÃ£o para recepcionistas, biomÃ©dicos e mÃ©dicos militares
> do LaboratÃ³rio de AnÃ¡lises ClÃ­nicas (LAC) do HGUMBA

---

## SumÃ¡rio

1. [Acessar o Sistema](#1-acessar-o-sistema)
2. [Cadastrar um Paciente com MÃ©dico Solicitante](#2-cadastrar-um-paciente-com-m-dico-solicitante)
3. [Solicitar Exames com MÃºltiplos MÃ©dicos (CoPhysicians)](#3-solicitar-exames-com-m-ltiplos-m-dicos-cophysicians)
4. [Gerar o PDF do CDM (Faturamento)](#4-gerar-o-pdf-do-cdm-faturamento)
5. [Interpretar Flags [ALTO] e [BAIXO] nos Laudos](#5-interpretar-flags-alto-e-baixo-nos-laudos)
6. [Assinar e Publicar o Laudo (Publish â†’ SANDRA)](#6-assinar-e-publicar-o-laudo-publish-sandra)
7. [Verificar se o Laudo Chegou ao SANDRA](#7-verificar-se-o-laudo-chegou-ao-sandra)
8. [SoluÃ§Ã£o de Problemas Comuns](#8-solu-o-de-problemas-comuns)

---

## 1. Acessar o Sistema

### Pelo Computador do LaboratÃ³rio

| InformaÃ§Ã£o | Valor |
|-----------|-------|
| **URL** | `http://senaite.gti.local/senaite` (ou o IP definido pela TI) |
| **UsuÃ¡rio** | Seu login do SENAITE (fornecido pela chefia) |
| **Senha** | Sua senha pessoal |

### Tela Inicial

ApÃ³s o login, vocÃª verÃ¡ o painel principal do SENAITE com:

- **Clients** â†’ Clique em "HGU" para acessar os pacientes e requisiÃ§Ãµes do hospital
- **Analysis Requests** â†’ Lista de todas as requisiÃ§Ãµes de exames pendentes e concluÃ­das
- **Tasks** â†’ Suas tarefas pendentes (resultados para liberar)

---

## 2. Cadastrar um Paciente com MÃ©dico Solicitante

### Passo a Passo

1. No menu lateral, clique em **Clients** â†’ **HGU**
2. Clique na aba **Analysis Requests**
3. Clique no botÃ£o **Add** (ou o Ã­cone de "+" no canto superior direito)

   ![Add AR]

4. Preencha o formulÃ¡rio:

   | Campo | O que preencher | Exemplo |
   |-------|----------------|---------|
   | **Title / ID** | CÃ³digo de identificaÃ§Ã£o da requisiÃ§Ã£o | `HGU-AR-042` |
   | **Patient Full Name** | Nome completo do paciente | `MARIA DA SILVA SANTOS` |
   | **Medical Record Number (MRN)** | RG / CPF / prontuÃ¡rio | `12345678901` ou `MRN-042` |
   | **Client** | Deve vir preenchido como "HGU" | `HGU` |
   | **Primary Physician / MÃ©dico Solicitante** | Nome do mÃ©dico que pediu o exame | `Dr. CARLOS ALMEIDA` |

5. Role para baixo e clique em **Save**

> âš ï¸ **Importante:** O campo **Medical Record Number** Ã© usado para vincular o paciente ao histÃ³rico de exames anteriores. Sempre preencha com o CPF ou nÃºmero de prontuÃ¡rio.

---

## 3. Solicitar Exames com MÃºltiplos MÃ©dicos (CoPhysicians)

Quando um paciente Ã© atendido por **mais de um mÃ©dico** (ex: clÃ­nico geral + infectologista + cirurgiÃ£o), todos devem constar no laudo para faturamento.

### Como Adicionar MÃ©dicos Adicionais

1. Na tela de criaÃ§Ã£o/ediÃ§Ã£o da **Analysis Request**, localize o campo
   **Co-Profissionais Solicitantes** (fica logo abaixo do campo "Primary Physician")

   ![CoPhysicians field]

2. Clique no campo de busca e digite o nome do mÃ©dico adicional
3. Selecione o nome na lista que aparece
4. Repita para cada mÃ©dico que deseja adicionar
5. Clique em **Save**

### Como Fica no CDM

No PDF do CDM, os mÃ©dicos aparecem assim:

```
Profissionais Solicitantes:
- Dr. CARLOS ALMEIDA (principal)
- Dr. ANA BEATRIZ PEREIRA (co-solicitante)
- Dr. JOSE ROBERTO LIMA (co-solicitante)
```

> ðŸ’¡ **Dica:** Use o CoPhysicians para mÃ©dicos que acompanham o caso mas nÃ£o sÃ£o o solicitante principal. Isso garante que todos os profissionais sejam cobrados corretamente no faturamento.

---

## 4. Gerar o PDF do CDM (Faturamento)

O **Comprovante de Despesas MÃ©dicas (CDM)** Ã© o documento que lista os exames realizados e seus valores para cobranÃ§a.

### Como Gerar

1. Na lista de **Analysis Requests**, encontre a requisiÃ§Ã£o desejada
2. Clique no **ID** da requisiÃ§Ã£o para abrir os detalhes
3. Na barra de aÃ§Ãµes, clique no botÃ£o **CDM PDF** (ou acesse diretamente:

   ```
   http://senaite.gti.local/senaite/clients/hgu/HGU-AR-042/@@cdm-pdf
   ```

4. O navegador farÃ¡ o download de um arquivo PDF com nome `cdm_HGU-AR-042.pdf`

### O Que Vem no PDF

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚        COMPROVANTE DE DESPESAS MÃ‰DICAS        â”‚
â”‚                                              â”‚
â”‚  RequisiÃ§Ã£o: HGU-AR-042                      â”‚
â”‚  Paciente: MARIA DA SILVA SANTOS             â”‚
â”‚                                              â”‚
â”‚  Profissionais Solicitantes:                 â”‚
â”‚   - Dr. CARLOS ALMEIDA (principal)           â”‚
â”‚   - Dr. ANA BEATRIZ PEREIRA (co-solicitante) â”‚
â”‚                                              â”‚
â”‚  Exame            CÃ³digo     Valor           â”‚
â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€        â”‚
â”‚  Glicemia         03.02.005  R$ 8,90         â”‚
â”‚  Hemograma        01.01.001  R$ 12,50        â”‚
â”‚  Colesterol Total 04.01.001  R$ 15,00        â”‚
â”‚                              â”€â”€â”€â”€â”€â”€â”€â”€â”€        â”‚
â”‚                     TOTAL:   R$ 36,40         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Para Imprimir

- Abra o PDF baixado
- Clique em **Arquivo â†’ Imprimir** (ou `Ctrl + P`)
- Escolha a impressora do laboratÃ³rio
- O CDM impresso deve acompanhar a requisiÃ§Ã£o fÃ­sica para o setor de faturamento

---

## 5. Interpretar Flags [ALTO] e [BAIXO] nos Laudos

Quando um resultado de exame estÃ¡ **fora do intervalo de referÃªncia**, o laudo exibe
uma flag visÃ­vel:

| Flag | Significado | Exemplo |
|------|-------------|---------|
| **[ALTO]** | Resultado acima do valor mÃ¡ximo esperado | Glicemia 200 mg/dL (normal atÃ© 99) |
| **[BAIXO]** | Resultado abaixo do valor mÃ­nimo esperado | Hemoglobina 8 g/dL (normal 12-16) |

### Como Aparece no Laudo

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚              LAUDO DE EXAMES                  â”‚
â”‚                                              â”‚
â”‚  Paciente: MARIA DA SILVA SANTOS             â”‚
â”‚  RequisiÃ§Ã£o: HGU-AR-042                      â”‚
â”‚                                              â”‚
â”‚  Glicemia: 200.0 mg/dL  **[ALTO]**           â”‚
â”‚  Hemoglobina: 8.0 g/dL  **[BAIXO]**          â”‚
â”‚  Colesterol: 180.0 mg/dL                     â”‚
â”‚                                              â”‚
â”‚  â”€â”€ GrÃ¡fico de HistÃ³rico: Glicemia â”€â”€        â”‚
â”‚  [grÃ¡fico mostrando evoluÃ§Ã£o]                â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### O Que Fazer

| Quem | AÃ§Ã£o |
|------|------|
| **BiomÃ©dico** | Verificar se o valor faz sentido clÃ­nico. Se o equipamento estava calibrado, se a amostra nÃ£o hemolisou. Se houver dÃºvida, repetir o exame. |
| **MÃ©dico** | Analisar o resultado no contexto do paciente. A flag Ã© um alerta, nÃ£o um diagnÃ³stico. |
| **Recepcionista** | Ao imprimir o laudo, a flag aparece automaticamente no PDF. NÃ£o precisa fazer nada adicional. |

> âš ï¸ **CritÃ©rios de RejeiÃ§Ã£o:** Se o resultado estiver **muito acima** do crÃ­tico
> (ex: glicemia > 500 mg/dL), o sistema registra um alerta. O biomÃ©dico deve
> **repetir a dosagem** antes de liberar.

---

## 6. Assinar e Publicar o Laudo (Publish â†’ SANDRA)

ApÃ³s os resultados ficarem prontos, o laudo precisa ser **assinado eletronicamente**
(publicado) para que:
1. O PDF seja gerado com o status oficial
2. O sistema envie automaticamente o laudo para o prontuÃ¡rio do paciente no **SANDRA**

### Fluxo de PublicaÃ§Ã£o

```
Resultados digitados/importados
        â”‚
        â–¼
   BiomÃ©dico verifica resultados
   (confere flags [ALTO]/[BAIXO])
        â”‚
        â–¼
   BiomÃ©dico clica em "Publish" (Assinar)
        â”‚
        â–¼
   Laudo muda para estado "published"
        â”‚
        â–¼
   Sistema envia PDF para o SANDRA (automÃ¡tico)
        â”‚
        â–¼
   MÃ©dico acessa o laudo pelo prontuÃ¡rio no SANDRA
```

### Passo a Passo

1. Na lista de **Analysis Requests**, localize a requisiÃ§Ã£o com resultados prontos
2. Abra a requisiÃ§Ã£o clicando no ID
3. Verifique os resultados na aba **Analyses**

   - Confira se todos os exames solicitados estÃ£o preenchidos
   - Veja se hÃ¡ flags **[ALTO]** ou **[BAIXO]** â€” se houver, o biomÃ©dico deve validar

4. Clique no botÃ£o **Publish** (no topo da tela)

5. Confirme a aÃ§Ã£o na janela que aparece:

   ```
   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
   â”‚  Publicar AnÃ¡lises                  â”‚
   â”‚                                     â”‚
   â”‚  Deseja publicar esta requisiÃ§Ã£o?   â”‚
   â”‚  O laudo serÃ¡ enviado ao SANDRA.    â”‚
   â”‚                                     â”‚
   â”‚  [Cancelar]  [Confirmar]            â”‚
   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
   ```

6. ApÃ³s confirmar, o estado muda para **`published`**

   - Uma mensagem verde aparece: "AnÃ¡lises publicadas com sucesso"
   - O PDF do laudo Ã© gerado automaticamente
   - O sistema envia o PDF para o SANDRA (prontuÃ¡rio) em segundos

### VerificaÃ§Ã£o

ApÃ³s publicar, vocÃª pode:

- Ver o status na lista: o Ã­cone da requisiÃ§Ã£o muda para verde (publicado)
- Clicar em **View PDF** para visualizar o laudo final
- Na aba **History**, ver o registro: "Transition: publish â†’ published by usuario"

---

## 7. Verificar se o Laudo Chegou ao SANDRA

ApÃ³s a publicaÃ§Ã£o, o sistema tenta enviar o laudo automaticamente para o SANDRA.
VocÃª pode confirmar se deu certo:

### Pelo SENAITE

1. Abra a requisiÃ§Ã£o publicada
2. Role atÃ© o campo **Remarks**
3. Se o envio foi bem-sucedido, nÃ£o aparece mensagem de erro
4. Se houve falha, a equipe de TI verÃ¡ nos logs do sistema

### Pelo SANDRA (ProntuÃ¡rio)

1. Acesse o prontuÃ¡rio do paciente no SANDRA
2. Procure a seÃ§Ã£o de **Resultados de Exames** ou **Laudos**
3. O laudo deve aparecer listado com o ID da requisiÃ§Ã£o

> â±ï¸ O envio ao SANDRA leva **segundos** apÃ³s a publicaÃ§Ã£o. Se nÃ£o aparecer
> em atÃ© 5 minutos, comunique a TI.

---

## 8. SoluÃ§Ã£o de Problemas Comuns

| Problema | Causa ProvÃ¡vel | O Que Fazer |
|----------|---------------|-------------|
| **NÃ£o consigo acessar o sistema** | Senha errada ou usuÃ¡rio bloqueado | Solicitar reset de senha Ã  TI |
| **O mÃ©dico nÃ£o aparece na busca do CoPhysicians** | MÃ©dico nÃ£o cadastrado no sistema | Solicitar Ã  TI o cadastro do mÃ©dico |
| **O PDF do CDM nÃ£o abre** | Pop-up bloqueado pelo navegador | Permitir pop-ups do site do SENAITE |
| **Flag [ALTO] aparece mas o valor parece normal** | Intervalo de referÃªncia do sistema diferente do laboratÃ³rio | O biomÃ©dico deve verificar e ajustar se necessÃ¡rio |
| **BotÃ£o Publish nÃ£o aparece** | UsuÃ¡rio nÃ£o tem permissÃ£o | Solicitar Ã  TI que libere a permissÃ£o "Manage Analysis Requests" |
| **O laudo publicado nÃ£o aparece no SANDRA** | Falha de comunicaÃ§Ã£o entre sistemas | Informar a TI para verificar os logs de auditoria |
| **Resultado de exame nÃ£o veio do equipamento** | Analisador nÃ£o conectou ou frame ASTM rejeitado | Verificar se o equipamento estÃ¡ ligado e conectado Ã  rede |
| **A lista de pacientes estÃ¡ muito lenta** | Muitas requisiÃ§Ãµes abertas | Usar o campo de busca para filtrar por ID ou nome |

---

## GlossÃ¡rio

| Termo | Significado |
|-------|-------------|
| **AR / Analysis Request** | RequisiÃ§Ã£o de anÃ¡lise â€” o "pedido de exame" |
| **CDM** | Comprovante de Despesas MÃ©dicas â€” usado para faturamento |
| **CoPhysicians** | MÃ©dicos co-solicitantes â€” profissionais adicionais que acompanham o caso |
| **MRN** | Medical Record Number â€” nÃºmero de prontuÃ¡rio do paciente |
| **Publish** | AÃ§Ã£o de assinar e publicar o laudo, tornando-o oficial |
| **SANDRA** | Sistema de prontuÃ¡rio do ExÃ©rcito |
| **Flag [ALTO]/[BAIXO]** | Indicador de resultado fora do intervalo de referÃªncia |
| **Remarks** | Campo de observaÃ§Ãµes na requisiÃ§Ã£o (usado para trilha de auditoria) |

---

## Anexo: Checklist DiÃ¡rio do Operador

### Recepcionista (InÃ­cio do Turno)

- [ ] Login no SENAITE OK
- [ ] Conferir se hÃ¡ pedidos do SANDRA para cadastrar
- [ ] Cadastrar pacientes com MRN e mÃ©dico solicitante
- [ ] Adicionar CoPhysicians quando houver mÃºltiplos mÃ©dicos
- [ ] Imprimir CDM e encaminhar ao faturamento

### BiomÃ©dico (Durante o Turno)

- [ ] Verificar resultados que chegaram dos analisadores
- [ ] Conferir flags [ALTO] e [BAIXO] â€” validar clinicamente
- [ ] Se necessÃ¡rio, repetir exames com flags crÃ­ticas
- [ ] Publicar (assinar) laudos com resultados OK

### MÃ©dico / Chefia (Fim do Turno)

- [ ] Conferir se todos os laudos do dia foram publicados
- [ ] Verificar se hÃ¡ pendÃªncias na lista de Analysis Requests
- [ ] Se houver laudo nÃ£o publicado, identificar o motivo e resolver

---

*Documento gerado em 2026-05-19 | v1.0.0*
