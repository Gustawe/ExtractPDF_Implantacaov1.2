# Briefing para evolução do Conversor de Folhas

## Como usar este arquivo em outra conversa

Anexe este arquivo à nova conversa ou cole o texto abaixo como pedido inicial:

> Implemente as melhorias descritas em `MELHORIAS_CONVERSOR_FOLHAS.md` no projeto atual. Antes de alterar qualquer arquivo, inspecione a arquitetura e os testes existentes. Preserve o comportamento de conversões já aprovadas, não sobrescreva XLSX existentes e implemente testes automatizados para todos os critérios de aceite. Ao final, execute os testes relevantes e informe os arquivos alterados, os resultados e quaisquer limitações.

---

## Contexto e problema identificado

O conversor processou o arquivo de teste `Folha 13° - 1ª Parcela 2025.pdf` e o marcou como **Concluído com alertas**, com:

- 21 validações de **Soma de proventos** divergentes;
- 1 ocorrência: `RESUMO_FISCAL_AUSENTE`.

As 21 divergências não representam diferenças reais nos valores da folha. O total de proventos de cada funcionário foi lido, mas os eventos detalhados que seriam somados pela validação não existem nesse formato de folha de 13º, ou não são aplicáveis a ele. A validação somou R$ 0,00 em eventos e comparou o resultado com o total de proventos, produzindo falsos positivos.

Atualmente:

- o botão **Ver detalhes** exibe apenas uma mensagem com as quantidades;
- os detalhes estruturados de validações e ocorrências não são mantidos para consulta pela interface e pelo histórico;
- o fluxo de planilha do layout visual não apresenta abas de auditoria equivalentes às do fluxo genérico;
- a fila exibe `Concluído com alertas` para qualquer resultado diferente de aprovado, inclusive para divergências de valores.

## Objetivo

Tornar os resultados da conversão auditáveis e claros, separando avisos de divergências reais e eliminando o falso positivo do formato reconhecido de folha de 13º.

## Requisitos funcionais

### 1. Validação correta para folha de 13º

1. Reconhecer de forma confiável o layout de folha de 13º sem eventos detalhados. A regra deve considerar características concretas do documento, como título/período/tipo de parcela e a ausência de linhas de eventos, em vez de depender somente do nome do arquivo.
2. Nessa condição, as validações **Soma de proventos** e **Soma de descontos** que dependem dos eventos devem receber o estado `NÃO APLICÁVEL`, com uma mensagem explicativa, por exemplo: `Validação não aplicável: este modelo de 13º não apresenta eventos detalhados.`
3. Uma validação `NÃO APLICÁVEL` não pode gerar divergência, aviso ou alterar o estado final da conversão.
4. Não ignorar silenciosamente a ausência de eventos em layouts normais. Se um layout não reconhecido ou uma folha mensal esperada com eventos não tiver seus eventos lidos, registrar uma ocorrência clara de leitura/validação para investigação.
5. Não ocultar ocorrências independentes. Por exemplo, `RESUMO_FISCAL_AUSENTE` deve continuar sendo avaliada segundo sua própria regra de aplicabilidade; ela não deve ser removida apenas porque o documento é de 13º.

### 2. Resultado estruturado da conversão

Criar uma estrutura de dados única para transportar e persistir os detalhes do resultado. Ela deve ser usada pelo motor, serviço de conversão, fila, histórico, interface e escritor do XLSX.

Para cada validação, preservar no mínimo:

- arquivo de origem;
- página, quando disponível;
- escopo (`FUNCIONÁRIO`, `DOCUMENTO`, etc.);
- identificador e nome do funcionário, quando aplicável;
- nome da validação;
- valor esperado;
- valor apurado;
- diferença;
- estado (`OK`, `DIVERGÊNCIA`, `AVISO`, `NÃO APLICÁVEL`);
- mensagem explicativa;
- referência da célula de destino, quando for possível destacá-la na planilha.

Para cada ocorrência, preservar no mínimo:

- severidade (`INFORMAÇÃO`, `AVISO` ou `ERRO`);
- código;
- mensagem;
- arquivo, página e funcionário relacionados, quando disponíveis.

O histórico local deve guardar esses detalhes em formato estruturado, por exemplo em uma coluna JSON com migração compatível para bancos SQLite já existentes. Registros antigos, que contêm somente a mensagem resumida, devem continuar consultáveis e indicar que os detalhes estruturados não estão disponíveis.

### 3. Tela `Ver detalhes`

Substituir a caixa de mensagem simples por um diálogo não editável contendo:

- resumo no topo com as quantidades de divergências, avisos e erros;
- uma tabela de validações com as colunas: **Situação**, **Funcionário**, **Validação**, **Esperado**, **Apurado**, **Diferença**, **Página** e **Mensagem**;
- uma tabela ou seção de ocorrências com: **Severidade**, **Código**, **Funcionário**, **Página** e **Mensagem**;
- filtros por situação/severidade e busca textual por funcionário, código ou mensagem;
- formatação monetária brasileira e destaque visual discreto para divergências;
- comportamento consistente na fila atual e no histórico de conversões.

O botão deve ficar disponível quando houver detalhes estruturados ou mensagem legada. Para uma conversão legada, exibir o resumo disponível e informar que os detalhes completos não foram armazenados naquela execução.

### 4. Abas de auditoria no XLSX

Quando houver divergências, incluir uma aba **Validações** no XLSX com os mesmos dados mostrados na interface. Quando houver ocorrências, incluir uma aba **Ocorrências**.

Regras:

- aplicar o requisito aos dois fluxos de geração: o layout visual de folha e o escritor genérico;
- usar tabela do Excel, cabeçalho congelado, filtro e formatos adequados para moeda, número e data;
- diferenciar visualmente `DIVERGÊNCIA`, `AVISO` e `NÃO APLICÁVEL`, sem depender apenas de cor;
- a aba de auditoria deve ser a fonte de conferência quando uma célula não puder ser destacada na aba principal;
- `NÃO APLICÁVEL` pode constar para rastreabilidade, mas não deve ser contado como divergência nem fazer a planilha parecer reprovada.

### 5. Destaque das células afetadas

Para cada divergência que tenha um mapeamento confiável para a planilha final:

1. preencher a célula do total relacionado em amarelo claro;
2. adicionar comentário/nota com validação, valor esperado, valor apurado, diferença e página de origem;
3. manter o formato numérico original da célula;
4. não alterar células sem mapeamento confiável.

Exemplos de campos que devem poder ser mapeados: totais de proventos, descontos e líquido do funcionário, e totais de departamento/documento. A ausência de mapeamento não pode impedir a geração do arquivo; nesse caso, a divergência continua disponível na aba **Validações** e em **Ver detalhes**.

### 6. Estados claros na fila e no histórico

Separar o resultado técnico da conversão do rótulo exibido ao usuário. O comportamento esperado é:

| Resultado | Rótulo na interface | Regra |
|---|---|---|
| Sem pendências | `Concluído` | Sem avisos, divergências ou erros. |
| Com avisos | `Concluído com avisos` | Há avisos de leitura/informação, mas nenhuma divergência de valor ou erro. |
| Com divergências | `Concluído com divergências` | O XLSX foi gerado, mas há ao menos uma divergência que exige conferência. Pode coexistir com avisos. |
| Falha | `Erro` | O XLSX não pôde ser gerado de modo válido. |

Para fins de prioridade de exibição: `Erro` > `Concluído com divergências` > `Concluído com avisos` > `Concluído`.

Não usar mais um único estado genérico de alerta para representar tanto aviso quanto divergência. Atualizar também os rótulos, tooltips, cores, histórico e resumo final do lote.

## Diretrizes de implementação

- Reutilizar as estruturas de validação e ocorrências existentes em vez de duplicar regras na interface ou no escritor do XLSX.
- Evitar que a interface interprete uma string de mensagem para inferir tipos de problema. Ela deve consumir dados tipados/estruturados.
- Manter compatibilidade com o banco de histórico existente e com registros antigos.
- Preservar a criação atômica do XLSX e a proteção contra sobrescrita de arquivos existentes.
- Não registrar conteúdo sensível desnecessário em logs. Usar logs de diagnóstico com código da regra, arquivo e página quando necessário.
- Aplicar a nova regra do 13º ao perfil de layout reconhecido; não assumir que toda folha sem eventos é uma folha de 13º válida.
- Atualizar a documentação de uso, caso o projeto possua manual ou instruções do aplicativo.

## Critérios de aceite e testes automatizados

1. **Folha mensal com eventos e valores consistentes:** estado `Concluído`; nenhuma divergência; nenhum destaque amarelo.
2. **Folha mensal com diferença real em um total:** estado `Concluído com divergências`; a linha aparece em `Ver detalhes` e na aba **Validações**; a célula mapeada fica amarela e recebe nota explicativa.
3. **Folha de 13º reconhecida e sem eventos detalhados:** as validações dependentes de eventos ficam `NÃO APLICÁVEL`; não há divergência falsa; o resultado final só terá aviso se existir uma ocorrência independente e aplicável.
4. **Arquivo de 13º usado neste diagnóstico:** não deve voltar a apresentar as 21 divergências de `Soma de proventos` com valor apurado de R$ 0,00.
5. **Layout normal sem eventos inesperadamente:** o sistema não deve marcar a validação como `NÃO APLICÁVEL` de forma silenciosa; deve registrar aviso de leitura/validação identificável.
6. **Histórico:** detalhes de uma nova conversão continuam disponíveis após fechar e reabrir o aplicativo. Um registro antigo continua abrindo sem erro e informa a limitação dos detalhes.
7. **Falha de conversão:** permanece classificada como `Erro`, sem ser confundida com aviso ou divergência.
8. Executar a suíte de testes existente e adicionar testes unitários/integrados para as regras novas, incluindo a migração do histórico.

## Fora de escopo nesta etapa

- Alterar valores extraídos do PDF automaticamente.
- Tentar corrigir divergências financeiras sem confirmação humana.
- Destacar células quando não existir uma correspondência confiável entre a validação e a planilha.
- Remover avisos legítimos apenas para deixar o resultado visualmente "limpo".

