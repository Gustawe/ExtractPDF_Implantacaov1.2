# Instruções para corrigir a extração da Folha 08-2024 e a publicação do XLSX em compartilhamento SMB

## Papel da IA que receber estas instruções

Atue como engenheiro de software Python sênior. Trabalhe no projeto `novo_conversor`, preserve a arquitetura existente e implemente correções pequenas, testáveis e retrocompatíveis. Não altere a cópia legada em `motor_conversao_pdf_xlsx` sem confirmar que ela ainda é utilizada. A aplicação empacotada 0.5.1 usa `novo_conversor/src`.

Antes de editar, leia os arquivos indicados, confirme as hipóteses com os testes e mantenha a garantia existente: gerar o XLSX ao lado do PDF, nunca sobrescrever um XLSX existente e limpar temporários mesmo quando ocorrer falha.

## Arquivos de entrada usados na análise

- `Folha 08-2024.pdf`
- `Folha 08-2024.xlsx`, gerado pela versão 0.5.1
- Primeira imagem: 40 divergências e 1 aviso
- Segunda imagem: `PermissionError: [WinError 5] Acesso negado` ao renomear o temporário para o XLSX final em caminho UNC
- Terceira imagem: linhas de divergência ilegíveis no modo escuro
- Quarta imagem: área dos eventos de desconto destacada em amarelo, ausente no XLSX gerado
- Quinta imagem: o status `Trabalhando` aparece concatenado ao nome, enquanto a célula ao lado de `Situação:` permanece vazia

Se os anexos não estiverem disponíveis no novo ambiente, solicite-os. Não inclua dados pessoais desses arquivos em logs novos ou fixtures versionadas.

## Resultado executivo da análise

Há cinco defeitos independentes, todos incluídos no escopo obrigatório da correção:

1. As 40 divergências de desconto são falsos positivos causados por limites fixos de coordenadas incompatíveis com este PDF. O parser lê os totais de desconto, mas rejeita todas as linhas detalhadas de desconto.
2. O `WinError 5` ocorre na etapa de publicação do XLSX no compartilhamento SMB, não na extração do PDF. O código trata colisão de nome somente como `FileExistsError`, mas um compartilhamento Windows/SMB pode responder `PermissionError [WinError 5]` quando o destino já existe, está bloqueado ou a ACL permite criar/gravar, mas não renomear/excluir.
3. No modo escuro, as linhas de divergência recebem fundo amarelo claro, mas continuam usando o texto claro herdado do tema. O contraste medido é aproximadamente `1,09:1`, muito abaixo do mínimo de `4,5:1` usado pelos testes de acessibilidade do próprio projeto.
4. O aviso `RESUMO_FISCAL_AUSENTE` é provavelmente falso: a página 10 contém a seção `Situações` e dados de INSS, IRRF e FGTS, mas os marcadores e limites verticais rígidos não reconhecem esta variante.
5. O parser inclui `Trabalhando` ou `Demitido` no nome e deixa `employee.status` vazio. O escritor do XLSX já possui o posicionamento correto; a correção deve separar os campos durante a extração.

## Defeito 1 - eventos de desconto não lidos

### Evidências reproduzidas

O processamento atual do PDF produziu:

| Métrica | Resultado atual |
|---|---:|
| Páginas | 10 |
| Funcionários/contribuintes | 40 |
| Eventos totais lidos | 48 |
| Eventos de provento (`P`) | 48 |
| Eventos de desconto (`D`) | 0 |
| Divergências | 40 |
| Avisos | 1 |
| Erros | 0 |

Todas as 40 divergências são da validação `Soma de descontos`. Os proventos conferem e o cálculo do líquido também confere. Exemplos:

| Funcionário | Total de descontos no PDF | Soma dos eventos lidos | Diferença |
|---|---:|---:|---:|
| Alison Felipe Domingos | R$ 2.378,01 | R$ 0,00 | -R$ 2.378,01 |
| CASSIO RONALDO PEREIRA DA SILVA | R$ 4.406,69 | R$ 0,00 | -R$ 4.406,69 |
| CAUANE VALENTE | R$ 110,88 | R$ 0,00 | -R$ 110,88 |

O XLSX confirma o mesmo padrão: a aba `Folha` preserva os totais de descontos, mas não contém as linhas detalhadas desses eventos; a aba `Validações` registra `Apurado = 0` para os 40 funcionários. Não foram encontrados erros de fórmula no arquivo.

### Confirmação da ausência da origem dos descontos no XLSX

O relato do setor usuário está correto. Não é apenas uma diferença visual: os eventos que explicam a origem dos descontos não foram incluídos no modelo processado e, por consequência, não foram gravados no XLSX.

No PDF, o primeiro funcionário possui um provento e cinco descontos:

| Lado | Código | Descrição | Referência | Valor |
|---|---:|---|---:|---:|
| Provento | 8781 | DIAS NORMAIS | 31,00 | R$ 4.000,00 |
| Desconto | 203 | DESCONTO VALE REFEIÇÃO | 143,00 | R$ 143,00 |
| Desconto | 998 | I.N.S.S. | 9,46 | R$ 376,61 |
| Desconto | 981 | DESC.ADIANT.SALARIAL | 1.600,00 | R$ 1.600,00 |
| Desconto | 8069 | HORAS FALTAS PARCIAL | 0:55 | R$ 18,40 |
| Desconto | 48 | VALE TRANSPORTE | 6,00 | R$ 240,00 |

Os cinco descontos somam exatamente `143,00 + 376,61 + 1.600,00 + 18,40 + 240,00 = 2.378,01`, valor exibido no total do funcionário.

No XLSX atual, o intervalo `Folha!A6:N12` contém:

- cabeçalho do funcionário nas linhas 6 e 7;
- somente o provento 8781 na linha 8;
- nenhuma informação nas colunas da metade direita da linha de evento;
- bases nas linhas 9 a 11;
- total de descontos de R$ 2.378,01 na linha 12, sem as rubricas que o compõem.

Portanto, o XLSX guarda **o total**, mas perde **código, descrição, referência e valor individual** de cada desconto. Isso impede o setor de identificar se o desconto veio de INSS, vale-transporte, adiantamento salarial, faltas ou outra rubrica.

### Por que o writer não mostra os descontos

O writer visual já está preparado para exibir os eventos dos dois lados. Em `novo_conversor/src/folha_pdf_xlsx/layout_writer.py`, `_write_structured_employee` executa:

```python
earnings = [event for event in employee.events if event.kind == "P"]
discounts = [event for event in employee.events if event.kind == "D"]
for earning, discount in zip_longest(earnings, discounts):
    _write_row(
        sheet,
        row,
        _structured_event_row(earning, discount),
        "event",
    )
```

Quando recebe um desconto, `_structured_event_row` grava:

- código em H;
- descrição em I;
- referência em L;
- valor em M.

O teste existente `StructuredPayrollVisualWriterTests.test_structured_document_uses_approved_single_sheet_layout`, em `novo_conversor/tests/engine/test_layout_pdf.py`, já comprova que um `PayrollEvent(kind="D")` fornecido ao writer aparece na célula M8.

Logo, a causa primária não está na exportação Excel. O extractor entrega `employee.events` com 48 proventos e zero descontos. Com `discounts = []`, o `zip_longest` escreve somente o lado esquerdo e deixa H:I e L:M vazios. A validação soma a mesma lista vazia, obtém R$ 0,00 e gera a divergência.

Corrigir a extração dos marcadores e valores `D` deve resolver simultaneamente:

- as 40 divergências falsas;
- a ausência da origem dos descontos no XLSX;
- a falta de rubricas detalhadas na área direita de cada funcionário.

### Causa raiz no código

Arquivo principal: `novo_conversor/src/folha_pdf_xlsx/extractor.py`.

Na função `_parse_event_half`, o lado de descontos usa atualmente:

```python
code_words = line.between(300, 329)
description_words = line.between(329, 470)
reference_words = line.between(470, 529)
value_words = line.between(529, 562)
type_words = line.after(562)
```

Neste PDF, todos os marcadores `D` das páginas de funcionários começam em `x0 = 556,56` e terminam aproximadamente em `x1 = 561,20`. Portanto, `line.after(562)` retorna vazio e o teste `type_text != kind` descarta cada desconto.

Há um segundo limite incorreto na mesma linha: o valor monetário à direita começa entre `x0 = 524,10` e `x0 = 541,08`, dependendo da quantidade de dígitos. O início fixo em `529` perde valores mais longos, como `1.600,00`, `14.233,00` e `56.686,81`. Além disso, o fim em `562` inclui o próprio marcador `D` neste layout.

Exemplo real de tokens de uma linha:

```text
203        x0=312,420
DESCONTO   x0=333,840
143,00     x0=482,220   # referência
143,00     x0=533,640   # valor
D          x0=556,560
```

### Correção requerida

Prefira uma correção semântica: localize o marcador final `D` entre os tokens da metade direita e use a posição desse marcador para delimitar o valor. Evite depender apenas de um número mágico rígido.

Como correção mínima comprovada para este perfil, os intervalos abaixo funcionaram:

```python
value_words = line.between(520, 556)
type_words = line.after(550)
```

Esses limites devem ser encapsulados como constantes documentadas ou, preferencialmente, substituídos por uma estratégia baseada no token final `D`. Não aplique o intervalo do desconto ao lado de proventos, pois o caso legado de `P` em `x0` próximo de `281,7` já possui teste específico.

Uma simulação em memória, sem editar o código do projeto, com `value_words = line.between(520, 556)` e `type_words = line.after(550)` produziu:

| Métrica | Resultado simulado |
|---|---:|
| Eventos totais | 232 |
| Proventos | 48 |
| Descontos | 184 |
| Soma dos eventos de desconto | R$ 98.556,17 |
| Soma dos totais de desconto dos funcionários | R$ 98.556,17 |
| Divergências | 0 |
| Avisos | 1 |
| Erros | 0 |

Isso confirma a causa e o efeito esperado da correção.

### Testes obrigatórios para o defeito 1

1. Adicione teste unitário em `novo_conversor/tests/engine/test_parsing.py` com `PdfLine` contendo:
   - código de desconto na metade direita;
   - valor longo começando em `x0 = 524,10`;
   - marcador `D` em `x0 = 556,56`;
   - asserções de código, descrição, valor e `kind == "D"`.
2. Preserve o teste existente do marcador `P` no limite legado.
3. Execute teste de regressão com o PDF real, quando disponível, e valide:
   - 40 registros;
   - 48 proventos;
   - 184 descontos;
   - soma de descontos `98556.17`;
   - zero divergências de valor.
4. Confirme visualmente no XLSX regenerado que as linhas de desconto aparecem na aba `Folha` e que a aba `Validações` não marca falsos positivos.
5. Estenda `StructuredPayrollVisualWriterTests` com um provento e vários descontos para validar o comportamento de `zip_longest`: os descontos excedentes devem continuar em linhas próprias, com o lado de proventos vazio.
6. No teste com o PDF real, localize o bloco do funcionário pela matrícula/nome, sem depender apenas de números fixos de linha, e confirme as rubricas 203, 998, 981, 8069 e 48 com suas descrições, referências e valores.
7. Confirme que a soma dos valores exibidos no lado direito do bloco é igual ao total de descontos do funcionário.
8. Execute toda a suíte, pois alterações de limites podem afetar folhas de 13º e outros layouts já suportados.

## Defeito 2 - `PermissionError [WinError 5]` ao publicar o XLSX

### Onde a falha ocorre

Arquivo: `novo_conversor/src/conversor_folhas/application/conversion_service.py`.

O fluxo atual é:

1. Resolver o PDF de origem.
2. Criar o nome temporário na própria pasta do PDF:

   ```python
   temporary_output = source.parent / (
       f".{source.stem}.{uuid4().hex}.temporario.xlsx"
   )
   ```

3. Gerar o XLSX temporário.
4. Publicá-lo com `os.rename(temporary_output, candidate)`.
5. Em `_publish_without_overwrite`, repetir somente quando ocorre `FileExistsError`.

A mensagem da tela contém a seta do temporário para o destino final. Portanto, a falha aconteceu no passo 4. O nome temporário foi construído e a geração chegou à publicação.

### Causas possíveis, em ordem de probabilidade

1. **O XLSX final já existia.** A aplicação promete gerar `Folha 08-2024 (1).xlsx`, mas em alguns compartilhamentos SMB a tentativa de renomear sobre um destino existente retorna `PermissionError [WinError 5]`, e não `FileExistsError`. O `except FileExistsError` não incrementa a sequência nesse caso.
2. **O destino estava aberto ou bloqueado**, por exemplo no Excel, antivírus, indexador, backup ou DLP. Se já existir, a ação correta continua sendo escolher o próximo nome, sem sobrescrever.
3. **ACL insuficiente para renomear/excluir.** Em Windows/SMB, criar e gravar um arquivo não implica necessariamente possuir `Delete`, `Delete subfolders and files` ou permissão equivalente para renomear. É possível gerar o temporário e falhar ao movê-lo.
4. Menos provável: política do compartilhamento bloqueando nomes temporários ocultos iniciados por ponto ou alguma regra de segurança/DLP.

Não conclua que é somente “falta de permissão de gravação”: a evidência aponta especificamente para renomeação/colisão/bloqueio.

### Estado da confirmação operacional

Ainda não foi possível confirmar com o colaborador se o XLSX final já existia ou estava aberto no momento da falha. Essa informação deve ser coletada posteriormente e registrada no chamado, mas não bloqueia a correção defensiva: o código precisa distinguir colisão confirmada de uma falha real de ACL, bloqueio ou política do compartilhamento.

### Diagnóstico operacional antes de alterar ACL

Peça ao usuário para confirmar se `Folha 08-2024.xlsx` já existia ou estava aberto no momento do erro. Em seguida, execute com a mesma conta do usuário, em uma pasta de homologação no mesmo compartilhamento:

```powershell
$testDirectory = '\\servidor\compartilhamento\pasta-de-homologacao'
$sourceFile = Join-Path $testDirectory 'teste-renomeacao.tmp'
$destinationFile = Join-Path $testDirectory 'teste-renomeacao.xlsx'

try {
    Set-Content -LiteralPath $sourceFile -Value 'teste' -Encoding UTF8 -ErrorAction Stop
    Rename-Item -LiteralPath $sourceFile -NewName (Split-Path $destinationFile -Leaf) -ErrorAction Stop
    Remove-Item -LiteralPath $destinationFile -Force -ErrorAction Stop
    Write-Host 'Criar, renomear e excluir: OK'
}
catch {
    Write-Error $_
}
```

Use apenas pasta de homologação e nomes descartáveis. Não execute esse teste na pasta produtiva sem autorização. Para conferir permissões efetivas:

```powershell
Get-Acl -LiteralPath '\\servidor\compartilhamento\pasta' | Format-List Owner,AccessToString
icacls '\\servidor\compartilhamento\pasta'
```

Também confirme permissões de compartilhamento e NTFS; a permissão efetiva é a combinação mais restritiva.

### Correção requerida no código

Implemente tratamento explícito e seguro para SMB, mantendo a regra de não sobrescrever:

1. Antes do `rename`, se o candidato existir, incremente a sequência.
2. Continue tratando `FileExistsError` como colisão.
3. Ao receber `PermissionError`, trate como colisão somente se for possível confirmar que o candidato existe. Nesse caso, tente `Folha 08-2024 (1).xlsx`, depois `(2)` e assim por diante.
4. Se o candidato não existir, não esconda o erro. Gere mensagem clara informando que a pasta permite leitura/criação, mas a publicação por renomeação pode estar bloqueada por ACL, arquivo em uso ou política do SMB.
5. Mantenha limite defensivo de tentativas para impedir laço infinito quando o compartilhamento responde de forma inconsistente.
6. Garanta que apenas o temporário pertencente à execução atual seja removido no `finally`.

Para ambientes cuja ACL não permite renomear/excluir, ofereça uma estratégia alternativa controlada:

- gerar o temporário em `%LOCALAPPDATA%\ConversorFolhas\temp`;
- abrir o destino com modo exclusivo `xb` e copiar o conteúdo, escolhendo outro nome em caso de `FileExistsError`;
- verificar tamanho e integridade ZIP/XLSX após a cópia;
- registrar claramente qualquer arquivo parcial que não puder ser removido.

Essa alternativa dispensa renomear dentro do compartilhamento, mas a cópia deixa de ser uma publicação atomicamente visível. Documente esse trade-off e prefira manter o `rename` atômico quando as ACLs do compartilhamento forem adequadas.

Não use `os.replace`, pois ele pode sobrescrever um XLSX existente e viola o requisito do projeto.

### Testes obrigatórios para o defeito 2

Adicione testes em `novo_conversor/tests/unit/test_conversion_service.py`:

1. Destino inexistente: publica `folha.xlsx`.
2. `folha.xlsx` e `folha (1).xlsx` existentes: publica `folha (2).xlsx` sem alterar os anteriores.
3. `os.rename` retorna `PermissionError(5, "Acesso negado")` e o candidato existe: considera colisão e tenta o próximo nome.
4. `os.rename` retorna `PermissionError` e o candidato não existe: interrompe e apresenta diagnóstico útil; não mascara como colisão.
5. Falha do motor: remove somente o temporário da execução.
6. Falha de publicação: não deixa um XLSX final inválido ou vazio.
7. Teste de integração em SMB de homologação, quando disponível: converter o mesmo PDF duas vezes deve criar `Folha 08-2024.xlsx` e `Folha 08-2024 (1).xlsx`.

## Defeito 3 - linhas coloridas ilegíveis no modo escuro

### Evidência visual e causa raiz

Na janela `Detalhes`, as linhas com `DIVERGÊNCIA` aparecem com fundo amarelo muito claro e texto quase branco. A linha fica legível no tema claro, mas praticamente invisível no tema escuro.

Arquivos envolvidos:

- `novo_conversor/src/conversor_folhas/ui/result_details_dialog.py`
- `novo_conversor/src/conversor_folhas/ui/theme.py`
- `novo_conversor/tests/unit/test_result_details_dialog.py`
- `novo_conversor/tests/unit/test_status_contrast.py`

Em `ResultDetailsDialog._populate`, o código define somente o fundo do item:

```python
color = _status_color(check.status)
...
if color is not None:
    item.setBackground(color)
```

O mesmo ocorre para as linhas da aba `Ocorrências`. Não há `item.setForeground(...)` nem `Qt.ForegroundRole` para essas células.

O tema escuro define globalmente:

```css
QWidget {
    background-color: #17171c;
    color: #e8e8ed;
}
```

Assim, a célula mantém texto `#e8e8ed` e recebe fundo `#fff2cc`. O contraste calculado é:

| Tipo de linha | Fundo | Texto herdado | Contraste aproximado |
|---|---|---|---:|
| Divergência/falha | `#fff2cc` | `#e8e8ed` | `1,09:1` |
| Aviso | `#fce4d6` | `#e8e8ed` | `1,00:1` |
| Não aplicável | `#e7e6e6` | `#e8e8ed` | `1,02:1` |
| Erro de ocorrência | `#f4cccc` | `#e8e8ed` | `1,20:1` |

Todos falham com grande margem no critério `4,5:1` já adotado em `test_status_contrast.py`.

As tabelas da fila e do histórico não apresentam o mesmo defeito porque seus modelos implementam explicitamente `Qt.ForegroundRole` e retornam `QColor("#202124")` para células com fundo de status. Os testes atuais verificam somente fila e histórico; não incluem `ResultDetailsDialog`.

### Correção requerida

Para qualquer linha que use os fundos claros de status, defina também uma cor de texto escura, por exemplo `#202124`, independentemente de o aplicativo estar no tema claro ou escuro. O contraste de `#202124` sobre o amarelo `#fff2cc` é aproximadamente `14,43:1`.

Aplique a combinação de fundo e texto a todas as células da linha, tanto na aba `Validações` quanto em `Ocorrências`. Não corrija apenas `DIVERGÊNCIA`, pois `AVISO`, `NÃO APLICÁVEL` e `ERRO` têm a mesma falha estrutural.

Prefira centralizar pares de cores em uma função ou estrutura reutilizável, por exemplo uma paleta de status que devolva `(background, foreground)`. Hoje há lógica semelhante duplicada em:

- `result_details_dialog.py`;
- `queue_table_model.py`;
- `history_dialog.py`.

Uma centralização reduz o risco de os três componentes divergirem novamente. Contudo, preserve uma mudança pequena se a refatoração ampliar demais o risco da correção.

O estado selecionado também precisa continuar legível. O tema escuro já define `selection-background-color: #39365f` e `selection-color: #ffffff`; confirme visualmente que a seleção prevalece durante a renderização e não fica com texto escuro sobre fundo escuro.

### Testes obrigatórios para o defeito 3

1. Estenda `test_status_contrast.py` ou `test_result_details_dialog.py` para criar um `ResultDetailsDialog` nos temas claro e escuro.
2. Cubra, no mínimo:
   - `DIVERGÊNCIA`;
   - `FALHA`;
   - `AVISO`;
   - `NÃO APLICÁVEL`;
   - ocorrência com severidade `ERRO`;
   - ocorrência com severidade `AVISO`.
3. Para cada célula colorida, obtenha `item.foreground().color()` e `item.background().color()` e exija razão de contraste maior ou igual a `4,5`.
4. Confirme que todas as colunas da linha recebem o mesmo par de cores, inclusive valores monetários, página e mensagem.
5. Selecione uma linha no modo escuro e valide visualmente o contraste do estado selecionado.
6. Gere uma captura da janela em ambos os temas para inspeção humana; evite teste de pixel excessivamente frágil na suíte automatizada.

### Critério específico de aceite visual

- Todas as linhas coloridas devem ser legíveis sem hover ou seleção nos temas claro e escuro.
- O contraste normal deve ser `>= 4,5:1`.
- A seleção deve continuar distinguível e legível.
- Cabeçalhos, linhas `OK`, filtros e campos de busca não devem mudar de aparência inadvertidamente.

## Defeito 4 - aviso fiscal falso e resumo fiscal não processado

### Evidência e causa provável

A página 10 do PDF contém `Situações`, número de empregados/contribuintes e diversos totais de INSS, IRRF e FGTS. Mesmo assim, `_find_fiscal_page` exige combinações de frases muito específicas, como `FGTS, PIS e ISS` e `IRRF conforme competência do cálculo`, e emite `RESUMO_FISCAL_AUSENTE`.

Além da detecção rígida da página, `_parse_fiscal_records` espera a seção em uma faixa vertical fixa (`455 <= top <= 570`). Nesta variante, `Situações` aparece por volta de `top = 115`, muito acima desse intervalo. Portanto, apenas suprimir o aviso esconderia uma falha real de processamento.

### Correção requerida

1. Detecte a página fiscal por um conjunto de marcadores normalizados e semanticamente suficientes, tolerando variações de acentuação, caixa, espaços e texto do cabeçalho.
2. Localize as seções pelos próprios rótulos da página e derive seus limites verticais dinamicamente, em vez de depender exclusivamente de coordenadas absolutas.
3. Preserve um fallback para o layout antigo já suportado.
4. Só considere o resumo disponível quando os registros esperados tiverem sido efetivamente extraídos e validados; não remova o aviso de forma artificial.
5. Se a página for detectada, mas nenhuma linha fiscal válida for produzida, emita ocorrência específica que diferencie “página ausente” de “página encontrada, porém formato não reconhecido”.

### Testes obrigatórios para o defeito 4

1. Variante atual, com `Situações` próxima ao topo: a página deve ser encontrada, os registros fiscais devem ser extraídos e `RESUMO_FISCAL_AUSENTE` não deve ser emitido.
2. Variante antiga: deve continuar sendo reconhecida sem regressão.
3. PDF realmente sem resumo fiscal: deve manter uma ocorrência clara.
4. Página com apenas um marcador isolado: não deve gerar falso positivo.
5. Teste de integração com o PDF real fora do repositório: conferir contagens e valores representativos de INSS, IRRF e FGTS.

## Defeito 5 - status concatenado ao nome do funcionário

### Evidência reproduzida

No primeiro bloco do XLSX atual:

| Célula | Conteúdo atual | Conteúdo esperado |
|---|---|---|
| `E6` | `Alison Felipe Domingos Trabalhando` | `Alison Felipe Domingos` |
| `D7` | `Situação:` | `Situação:` |
| `E7` | vazia | `Trabalhando` |

O mesmo padrão afeta outros empregados com `Trabalhando` e `Demitido`. Há ainda um caso de nome longo em que o texto extraído do PDF forma um único token: `RODRIGUEZSituação:Trabalhando`.

O posicionamento solicitado já existe em `novo_conversor/src/folha_pdf_xlsx/layout_writer.py`: o cabeçalho grava `employee.name`, e a linha seguinte grava `"Situação:"` seguida de `employee.status`. Portanto, não redesenhe a planilha. Corrija a origem dos dados no extrator.

### Causa raiz

Em `novo_conversor/src/folha_pdf_xlsx/extractor.py`, `_parse_employee` usa faixas fixas:

```python
identity_words = header.between(60, 250)
status = clean_label_artifacts(words_text(header.between(250, 365)))
```

Nesta folha, o token `Situação:Trabalhando` ocupa aproximadamente `x0 = 218,34` até `x1 = 287,10`. Como ele começa antes de `250`, entra inteiro na faixa de identidade e não entra na faixa de status. O resultado é nome contaminado e status vazio. O mesmo tipo de risco existe para `CPF:` e `Adm:` quando rótulo e valor vêm unidos no mesmo token.

### Correção requerida

1. Implemente uma segmentação do cabeçalho orientada pelos rótulos `Empr.:`/`Contr:`, `Situação:`, `CPF:` e `Adm:`.
2. Reconheça rótulos mesmo quando estiverem unidos ao valor ou ao final do campo anterior, como `Situação:Trabalhando`, `CPF:392...` e `RODRIGUEZSituação:Trabalhando`.
3. Extraia o nome entre a matrícula e `Situação:`; extraia o status entre `Situação:` e `CPF:`; extraia o CPF entre `CPF:` e `Adm:`; extraia a admissão após `Adm:`.
4. Use as coordenadas dos rótulos para preservar a ordem e resolver ambiguidades, mas faça a separação textual dentro de um token quando o rótulo estiver concatenado.
5. Mantenha um fallback de coordenadas para variantes legadas sem todos os rótulos, com validação explícita do resultado.
6. Não mantenha uma lista fechada de status como mecanismo principal. Ela pode ser usada apenas para validação, pois novos estados podem aparecer.
7. Ao final, normalize espaços sem alterar acentos, caixa ou partículas legítimas do nome.
8. Se um cabeçalho não puder ser segmentado com segurança, gere uma ocorrência acionável sem registrar CPF ou salário no log.

### Testes obrigatórios para o defeito 5

1. Empregado normal: `Alison Felipe Domingos` e status `Trabalhando` em campos separados.
2. Status `Demitido`.
3. Nome longo com `RODRIGUEZSituação:Trabalhando` no mesmo token.
4. Registro iniciado por `Contr:` para contribuinte.
5. Nome com acentos, partículas e caixa mista.
6. Tokens combinados `CPF:<valor>` e rótulo `Adm:` separado.
7. Variante legada coberta pelo fallback.
8. Teste do XLSX estruturado: no primeiro bloco, `E6` deve conter somente o nome, `D7` deve continuar com `Situação:` e `E7` deve conter `Trabalhando`.
9. Teste de regressão em todos os registros: nenhum nome deve terminar com um status conhecido e nenhum status reconhecido pode ficar vazio.

## Critérios de aceite

A correção só está concluída quando:

- o PDF `Folha 08-2024.pdf` gera 48 eventos `P` e 184 eventos `D`;
- a soma dos eventos `D` é `98556.17`;
- as validações de proventos, descontos e líquido não apresentam divergências neste arquivo;
- o bloco do primeiro funcionário mostra, no lado direito, as rubricas 203, 998, 981, 8069 e 48, e não apenas o total de R$ 2.378,01;
- cada funcionário apresenta código, descrição, referência e valor individual dos descontos extraídos;
- a soma dos detalhes exibidos em cada bloco reconcilia com o respectivo total de descontos;
- os totais gerais continuam em `177320.84` de proventos, `98556.17` de descontos e `78764.67` de líquido;
- converter duas vezes em compartilhamento SMB não sobrescreve o primeiro XLSX;
- colisões de nome geram sufixos sequenciais;
- falhas reais de ACL/bloqueio apresentam mensagem acionável;
- temporários são limpos sem remover arquivos preexistentes;
- as linhas de divergência, aviso, não aplicável e erro têm contraste `>= 4,5:1` nos temas claro e escuro;
- o estado selecionado das tabelas permanece legível;
- a página fiscal desta folha é reconhecida, seus registros são efetivamente extraídos e o falso `RESUMO_FISCAL_AUSENTE` desaparece;
- a variante fiscal antiga continua funcionando e um PDF realmente sem resumo ainda produz diagnóstico correto;
- nomes e situações são armazenados em campos separados para empregados e contribuintes;
- no primeiro bloco da aba `Folha`, `E6` contém somente `Alison Felipe Domingos`, `D7` contém `Situação:` e `E7` contém `Trabalhando`;
- o caso de nome longo concatenado a `Situação:` é separado corretamente, sem truncar o sobrenome;
- toda a suíte de testes existente permanece verde;
- o XLSX final é aberto e inspecionado visualmente, com eventos de desconto presentes e sem células essenciais truncadas.

## Arquivos que provavelmente serão alterados

- `novo_conversor/src/folha_pdf_xlsx/extractor.py`
- `novo_conversor/src/conversor_folhas/application/conversion_service.py`
- `novo_conversor/tests/engine/test_parsing.py`
- `novo_conversor/tests/engine/test_sample_pdf.py`, somente se o teste real permanecer opcional
- `novo_conversor/tests/unit/test_conversion_service.py`
- `novo_conversor/src/conversor_folhas/ui/result_details_dialog.py`
- `novo_conversor/tests/unit/test_result_details_dialog.py`
- `novo_conversor/tests/unit/test_status_contrast.py`
- `novo_conversor/tests/engine/test_layout_pdf.py`
- testes de detecção fiscal e segmentação do cabeçalho, preferencialmente em `novo_conversor/tests/engine/test_parsing.py`

## Sequência recomendada de implementação

1. Adicionar testes de regressão que falham com o código atual.
2. Corrigir a segmentação de nome, status, CPF e admissão por rótulos.
3. Corrigir a leitura do lado de descontos.
4. Corrigir a detecção e a extração do resumo fiscal.
5. Reprocessar o PDF real e reconciliar campos, contagens e totais.
6. Corrigir e testar o contraste das linhas coloridas nos dois temas.
7. Corrigir o tratamento de colisão/`PermissionError` na publicação.
8. Executar testes unitários e de integração local.
9. Validar em compartilhamento SMB de homologação com a mesma política/ACL da pasta produtiva.
10. Manter correções em commits separados por defeito para facilitar revisão e rollback.

## Restrições de segurança e operação

- Não alterar ACL de produção automaticamente.
- Não sobrescrever XLSX existentes.
- Não registrar CPF, salário ou conteúdo integral do PDF em logs.
- Não versionar o PDF/XLSX real sem aprovação, pois contêm dados pessoais.
- Usar logs estruturados com caminho, etapa (`extração`, `gravação temporária`, `publicação`) e código do erro, evitando dados de funcionários.
- Preparar rollback simples e validar o instalador empacotado, não somente a execução pelo ambiente de desenvolvimento.
