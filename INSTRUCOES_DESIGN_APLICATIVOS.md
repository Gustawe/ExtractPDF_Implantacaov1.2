# Instruções de design para aplicativos corporativos

> Guia reutilizável baseado na identidade visual do **Conversor de Folhas — Implantação**.
> Use este arquivo como especificação de interface em novos projetos desktop, web ou internos.

## 1. Direção visual

Crie uma interface corporativa, limpa, sóbria e funcional. O aplicativo deve transmitir confiança, precisão e simplicidade, sem parecer excessivamente decorativo.

Princípios obrigatórios:

- Priorizar clareza operacional e leitura rápida.
- Manter alta densidade de informação sem deixar a tela apertada.
- Usar hierarquia visual por alinhamento, espaçamento, peso tipográfico e contraste.
- Reservar a cor de destaque para a ação principal, progresso, seleção e indicadores relevantes.
- Utilizar superfícies planas, bordas finas e cantos discretamente arredondados.
- Oferecer temas claro e escuro com a mesma hierarquia e legibilidade.
- Manter os controles próximos do conteúdo que eles afetam.
- Exibir o estado atual do sistema e o próximo passo esperado.
- Evitar efeitos chamativos, gradientes, sombras fortes, excesso de cores e animações sem função.

Palavras-chave do estilo: **corporativo, confiável, compacto, moderno, discreto, operacional e acessível**.

## 2. Tokens visuais

Centralize estes valores em variáveis, constantes ou tokens. Não espalhe cores e medidas diretamente pelo código.

### 2.1 Tipografia

| Uso | Família | Tamanho de referência | Peso |
|---|---|---:|---:|
| Texto padrão | Segoe UI, system-ui, sans-serif | 10 pt / 13–14 px | 400 |
| Instrução ou subtítulo | Segoe UI, system-ui, sans-serif | 11 pt / 15 px | 400 |
| Nome do aplicativo | Segoe UI, system-ui, sans-serif | 17 pt / 22–23 px | 600 |
| Cabeçalhos de tabela | Segoe UI, system-ui, sans-serif | 10 pt / 13–14 px | 600 |
| Botão principal | Segoe UI, system-ui, sans-serif | 10 pt / 13–14 px | 600 |

Use frases curtas, capitalização normal e linguagem direta. Evite títulos inteiros em letras maiúsculas.

### 2.2 Paleta — tema claro

| Token | Valor | Aplicação |
|---|---|---|
| `background` | `#FFFFFF` | Fundo principal |
| `surface-subtle` | `#F7F8FB` | Área de arrastar e superfícies leves |
| `surface-muted` | `#F2F4F8` | Mensagens e painéis informativos |
| `surface-control` | `#F5F6F8` | Botões secundários |
| `surface-header` | `#EEF1F6` | Cabeçalhos de tabela |
| `text-primary` | `#202124` | Texto principal |
| `text-secondary` | `#5F6368` | Versão, metadados e texto auxiliar |
| `text-instruction` | `#3C4043` | Instruções |
| `brand-primary` | `#010042` | Ação principal, título e progresso |
| `brand-hover` | `#17165A` | Hover da ação principal |
| `border-default` | `#C7C9D1` | Bordas de controles |
| `border-subtle` | `#D9DBE2` | Contornos de tabelas |
| `divider` | `#E6E7EB` | Divisores e grade |
| `selection` | `#DCE5F4` | Seleção de linhas |
| `disabled-text` | `#9AA0A6` | Texto desabilitado |

### 2.3 Paleta — tema escuro

| Token | Valor | Aplicação |
|---|---|---|
| `background` | `#17171C` | Fundo principal |
| `surface-base` | `#1B1B21` | Tabelas e áreas de conteúdo |
| `surface-subtle` | `#202029` | Área de arrastar |
| `surface-muted` | `#22222B` | Mensagens e painéis informativos |
| `surface-control` | `#2A2A33` | Botões secundários |
| `surface-header` | `#272730` | Cabeçalhos de tabela |
| `text-primary` | `#E8E8ED` | Texto principal |
| `text-secondary` | `#A9A9B5` | Metadados e texto auxiliar |
| `brand-primary` | `#3936A6` | Ação principal |
| `brand-accent` | `#5A57CC` | Progresso |
| `brand-info` | `#7F8CFF` | Destaque lateral de mensagens |
| `brand-hover` | `#4845B8` | Hover da ação principal |
| `border-default` | `#4A4A57` | Bordas de controles |
| `border-subtle` | `#3F3F49` | Contornos de tabelas |
| `divider` | `#34343D` | Divisores e grade |
| `selection` | `#39365F` | Seleção de linhas |
| `disabled-text` | `#74747F` | Texto desabilitado |

### 2.4 Cores semânticas

Além da identidade principal, defina tokens próprios para estados. As cores nunca devem ser o único meio de comunicação: combine-as com texto, ícone ou ambos.

| Estado | Claro | Escuro | Uso |
|---|---|---|---|
| Sucesso | `#137333` | `#81C995` | Operação concluída |
| Aviso | `#B06000` | `#FDD663` | Resultado que exige atenção |
| Erro | `#B3261E` | `#F28B82` | Falha ou ação inválida |
| Informação | `#010042` | `#7F8CFF` | Orientação e status neutro |

Valide contraste segundo WCAG 2.1 AA: mínimo de 4,5:1 para texto normal e 3:1 para texto grande e componentes gráficos essenciais.

## 3. Espaçamento e geometria

Adote uma escala baseada em múltiplos de 4 px:

| Token | Valor | Uso típico |
|---|---:|---|
| `space-1` | 4 px | Ajustes pequenos |
| `space-2` | 8 px | Espaço interno compacto |
| `space-3` | 12 px | Distância entre controles relacionados |
| `space-4` | 16 px | Espaço interno confortável |
| `space-5` | 20 px | Seções secundárias |
| `space-6` | 24 px | Margens de diálogos |
| `space-7` | 28 px | Margens da janela principal |

Regras de geometria:

- Margem da janela principal: aproximadamente `28 px` nas laterais e `22–24 px` no topo e rodapé.
- Espaçamento vertical entre blocos: `14 px`.
- Margem de diálogos: `22 px` nas laterais e `18–20 px` na vertical.
- Raio padrão: `4 px`; barras de progresso podem usar `3 px`.
- Bordas: `1 px`; destaque informativo lateral: `3 px`.
- Botões: padding aproximado de `7 px 14 px`.
- Botão principal: padding aproximado de `8 px 20 px`.
- Área de arrastar: padding mínimo de `16 px`, conteúdo centralizado e borda tracejada.
- Alvos interativos devem ter, sempre que possível, pelo menos `36 px` de altura; em interfaces web responsivas, prefira `40–44 px`.

## 4. Estrutura recomendada da tela

Organize a janela principal nesta ordem:

1. **Cabeçalho compacto**: nome do aplicativo à esquerda; versão e ações globais à direita.
2. **Instrução contextual**: uma frase dizendo o que o usuário deve fazer.
3. **Ações de entrada**: inclusão de arquivos, pastas ou outros dados.
4. **Área alternativa de entrada**: por exemplo, arrastar e soltar.
5. **Área principal de trabalho**: tabela, formulário, lista, editor ou painel.
6. **Ações contextuais**: remover, detalhar, abrir resultado ou operar sobre a seleção.
7. **Progresso e ação principal**: estado resumido, progresso e botão de execução.
8. **Mensagem persistente**: retorno operacional mais recente, em linguagem clara.

Em uma linha de ações, coloque operações destrutivas ou de limpeza à esquerda, use espaço flexível no centro e deixe detalhes, abertura e ações relacionadas ao resultado à direita. A ação principal deve ser visualmente única.

## 5. Componentes

### 5.1 Cabeçalho

- Mostre o nome do produto com peso `600` e cor da marca no tema claro.
- Mostre versão ou ambiente como metadado discreto.
- Posicione configurações globais, histórico e alternância de tema à direita.
- Não use uma barra alta ou decorativa quando um cabeçalho compacto for suficiente.

### 5.2 Botões

- Use botão primário apenas para a ação que avança ou executa o fluxo principal.
- Use botões secundários neutros para as demais ações.
- Todos os botões devem ter estados normal, hover, pressionado, foco e desabilitado.
- Desabilite ações impossíveis no estado atual em vez de permitir cliques que resultem em erro.
- Use rótulos objetivos com verbo: “Adicionar PDFs”, “Abrir pasta”, “Iniciar conversão”.
- Para uma ação destrutiva, solicite confirmação quando houver perda relevante e torne a consequência explícita.

### 5.3 Tabelas e listas

- Use cabeçalho com fundo levemente contrastante, texto semibold e padding de `8 px`.
- Alterne suavemente o fundo das linhas para facilitar varredura visual.
- Selecione a linha inteira, mantendo contraste de texto adequado.
- Oculte elementos sem função, como cabeçalho vertical vazio.
- Ajuste colunas curtas ao conteúdo e deixe a coluna principal ocupar o espaço restante.
- Use tooltip para caminhos, mensagens e conteúdos truncados.
- Suporte duplo clique apenas como atalho; mantenha a mesma ação disponível em botão visível.
- Evite edição direta quando a tabela representar uma fila, histórico ou resultado.

### 5.4 Área de arrastar e soltar

- Use superfície sutil, borda tracejada, raio de `4 px` e conteúdo centralizado.
- Explique exatamente o tipo de item aceito.
- Ofereça seleção por botão como alternativa equivalente.
- Destaque a área durante o arraste válido e rejeite visualmente formatos inválidos.
- Desabilite a entrada enquanto uma operação incompatível estiver em execução.

### 5.5 Progresso e mensagens

- Combine texto quantitativo com uma barra: “3 de 8 concluídos”.
- Nunca dependa apenas da barra para comunicar andamento.
- Use a cor da marca no preenchimento da barra.
- Exiba abaixo uma mensagem persistente com superfície discreta e borda lateral de destaque.
- Mensagens devem informar o que aconteceu e, em caso de falha, o que o usuário pode fazer em seguida.
- Para operações longas, processe em segundo plano e mantenha a interface responsiva.

### 5.6 Diálogos

- Reutilize o mesmo tema, tipografia, espaçamento e componentes da janela principal.
- Use título direto, resumo curto, conteúdo principal e ações no rodapé.
- Confirmações devem indicar claramente o objeto e o efeito da ação.
- Detalhes técnicos podem ficar em área expansível ou copiável; a mensagem inicial deve ser compreensível para o usuário final.

## 6. Comportamento e estados

Cada tela deve prever, no mínimo:

- Estado inicial vazio com orientação do próximo passo.
- Dados carregados, sem seleção.
- Item selecionado e ações contextuais habilitadas.
- Processamento em andamento, com entradas incompatíveis bloqueadas.
- Sucesso completo.
- Sucesso com alertas.
- Falha parcial e falha total.
- Ausência de dados no histórico ou pesquisa.
- Recurso opcional indisponível, acompanhado de tooltip ou explicação.

Preserve as escolhas do usuário, como tema e preferências de visualização. Não permita fechar a aplicação silenciosamente durante uma operação crítica; informe o motivo e ofereça uma saída segura quando possível.

## 7. Tema claro e escuro

- Implemente ambos a partir dos mesmos tokens semânticos.
- Não crie o tema escuro apenas invertendo cores.
- No tema escuro, use cinzas muito escuros em vez de preto puro para preservar profundidade.
- Reduza o brilho de superfícies grandes e mantenha textos principais em branco suavizado.
- Persista a escolha entre sessões.
- Use o rótulo do botão para indicar a ação disponível: “Modo escuro” no tema claro e “Modo claro” no tema escuro.
- Teste tabelas, seleção, hover, foco, progresso, mensagens, diálogos e estados desabilitados nos dois temas.

## 8. Acessibilidade e operação por teclado

- Garanta ordem de foco coerente com a ordem visual.
- Exiba um indicador de foco perceptível em todos os controles interativos.
- Forneça atalhos para ações frequentes quando fizer sentido.
- Permita acionar botões com teclado e navegar em tabelas sem mouse.
- Associe rótulos acessíveis a ícones e controles.
- Não use apenas cor para distinguir sucesso, alerta, erro ou seleção.
- Respeite escala de fonte e DPI do sistema operacional.
- Evite animações ou intermitências desnecessárias.

## 9. Responsividade e adaptação

Para desktop, defina um tamanho mínimo que preserve o fluxo principal; a referência deste padrão é `980 × 640 px`. Em janelas menores:

- Preserve primeiro o conteúdo principal e a ação primária.
- Permita que grupos de ações quebrem linha ou migrem para um menu secundário.
- Evite rolagem horizontal da tela inteira; limite-a a componentes como tabelas quando inevitável.
- Trunque textos longos com reticências e exponha o conteúdo completo em tooltip.
- Em aplicações web, converta linhas densas de ações em grupos empilhados para larguras menores.

## 10. Arquitetura de implementação

- Mantenha tokens de tema em um único módulo ou arquivo.
- Separe estrutura, estilo, estado e regras de negócio.
- Crie componentes reutilizáveis para botões, mensagens, tabelas, progresso e áreas de entrada.
- Modele estados da interface explicitamente em vez de espalhar condições por manipuladores de evento.
- Centralize textos para facilitar revisão, padronização e futura internacionalização.
- Registre erros técnicos em logs, mas apresente mensagens curtas e acionáveis na interface.
- Salve apenas preferências necessárias e não armazene dados sensíveis em configurações locais sem proteção.
- Inclua testes automatizados para transições de estado, habilitação de ações e persistência do tema.
- Faça revisão visual nos temas claro e escuro, em 100%, 125% e 150% de escala de tela.

## 11. O que evitar

- Mais de uma ação primária competindo na mesma tela.
- Excesso de cartões, sombras, ícones ou divisórias.
- Bordas muito arredondadas que deixem a interface com aparência informal.
- Gradientes e cores saturadas em grandes superfícies.
- Texto cinza com contraste insuficiente.
- Mensagens genéricas como “Ocorreu um erro” sem orientação.
- Ações habilitadas que não podem funcionar no estado atual.
- Modal para toda mensagem de sucesso; prefira retorno persistente e não bloqueante.
- Operações longas executadas na thread da interface.
- Tabelas editáveis quando o objetivo é somente acompanhar ou consultar.
- Mudanças de layout imprevisíveis durante o processamento.

## 12. Checklist de aceite visual

Antes de concluir uma tela, confirme:

- [ ] A ação principal é identificável em menos de três segundos.
- [ ] O próximo passo está explícito no estado vazio.
- [ ] Os controles estão alinhados e seguem a escala de espaçamento.
- [ ] As cores vêm de tokens centralizados.
- [ ] Temas claro e escuro foram verificados.
- [ ] Hover, pressionado, foco e desabilitado estão implementados.
- [ ] Textos longos, caminhos e erros não quebram o layout.
- [ ] Seleção e estados não dependem apenas de cor.
- [ ] A navegação por teclado funciona.
- [ ] A interface permanece responsiva em tarefas demoradas.
- [ ] Estados vazio, carregando, sucesso, alerta e erro foram testados.
- [ ] Escalas de DPI de 100%, 125% e 150% foram verificadas.
- [ ] Mensagens explicam resultado e próxima ação.
- [ ] Operações destrutivas têm confirmação proporcional ao risco.

## 13. Bloco pronto para usar em novos projetos

Copie o texto abaixo para o briefing ou prompt do próximo aplicativo:

```text
Crie a interface seguindo um estilo corporativo, limpo, sóbrio e funcional.
Use Segoe UI ou a fonte nativa do sistema, fundo branco no tema claro e cinza
muito escuro no tema escuro. A cor principal é azul-marinho (#010042 no tema
claro e #3936A6 no escuro). Empregue superfícies planas, bordas finas de 1 px,
raio de 4 px e espaçamento baseado em múltiplos de 4 px.

Construa uma hierarquia compacta: cabeçalho com nome do produto e ações globais,
instrução contextual, entrada de dados, área principal de trabalho, ações da
seleção, progresso com ação primária e mensagem operacional persistente. Use uma
única ação primária por contexto. Mantenha ações indisponíveis desabilitadas e
comunique sempre o estado atual e o próximo passo.

Implemente temas claro e escuro com tokens semânticos centralizados. Preveja os
estados vazio, carregando, selecionado, processando, sucesso, alerta, erro e
desabilitado. Garanta contraste WCAG AA, foco visível, navegação por teclado,
suporte a DPI e comunicação que não dependa apenas de cores.

Evite gradientes, sombras fortes, excesso de cartões, animações decorativas,
cantos muito arredondados e múltiplos botões primários. Tarefas demoradas devem
rodar em segundo plano, com progresso quantitativo e interface responsiva.
```

## 14. Aplicação em diferentes tecnologias

- **PySide6/Qt:** use `QApplication.setStyle("Fusion")`, QSS centralizado, `objectName` apenas para variantes semânticas e `QSettings` para persistir o tema.
- **Web:** transforme os tokens em CSS Custom Properties e respeite `prefers-color-scheme`, mantendo uma escolha manual persistida.
- **WPF/WinUI:** centralize cores, espaçamentos e estilos em `ResourceDictionary` e use recursos de tema para alternância.
- **.NET MAUI:** use `ResourceDictionary`, `AppThemeBinding` e estilos implícitos para manter consistência.
- **Electron:** compartilhe os mesmos tokens CSS entre janelas e persista somente a preferência de aparência.

Independentemente da tecnologia, preserve a direção visual e o comportamento; adapte apenas os controles às convenções nativas da plataforma.
