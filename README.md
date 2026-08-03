# Conversor de Folhas — Implantação

Aplicativo Windows para converter folhas de pagamento em PDF para XLSX. O
processamento é local e utiliza o pacote `folha_pdf_xlsx` incluído no próprio
projeto.

## Estado atual

A versão `0.5.1` contém o fluxo funcional e distribuível:

- Seleção individual de vários PDFs.
- Seleção de uma pasta, sem percorrer subpastas.
- Arrastar e soltar arquivos ou pastas.
- Fila compacta com estado individual.
- Conversão serial fora da thread da interface.
- Progresso geral do lote.
- Saída na mesma pasta do PDF.
- Renomeação automática sem sobrescrever XLSX existentes.
- Abertura do XLSX ou da pasta de destino.
- Histórico local em SQLite, carregado somente quando o usuário o abre.
- Consulta, limpeza e abertura de resultados pelo histórico.
- Detalhes estruturados de validações e ocorrências, com filtros e busca.
- Estados distintos para avisos, divergências e erros.
- Abas de auditoria e destaque das células divergentes no XLSX.
- Tratamento auditável de validações não aplicáveis em folhas de 13º reconhecidas.
- Reconhecimento de resumos fiscais de 13º mesmo sem a seção opcional de apuração federal.
- Contraste legível dos estados da fila e do histórico nos temas claro e escuro.
- Tema claro e escuro.
- Logs rotativos em `%LOCALAPPDATA%\ConversorFolhas\logs`.
- Empacotamento em pasta para inicialização mais rápida.
- Instalador gráfico por usuário, sem exigir permissão de administrador.

O banco de histórico fica em
`%LOCALAPPDATA%\ConversorFolhas\history.sqlite3`. Não há consulta periódica:
ele é gravado ao fim de uma conversão e lido quando a tela **Histórico** é
aberta.

## Arquitetura

```text
Interface PySide6
    -> QueueManager
    -> ConversionService
    -> PayrollEngineAdapter
    -> folha_pdf_xlsx
```

A interface não importa `pdfplumber` ou `openpyxl`. O motor copiado permanece em
`src/folha_pdf_xlsx` e deve ser alterado somente quando houver erro comprovado.

## Preparar o ambiente de desenvolvimento

Requisitos:

- Windows 10 1809 ou posterior, ou Windows 11.
- Python 3.10 a 3.13.

No PowerShell, a partir da raiz de `novo_conversor`:

```powershell
.\scripts\setup-dev.ps1 -PythonExecutable "C:\caminho\para\python.exe"
```

O script cria `.venv` e instala a aplicação e as dependências de desenvolvimento.

## Executar

```powershell
.\.venv\Scripts\python.exe -m conversor_folhas
```

## Testar

```powershell
.\scripts\test.ps1
```

Para habilitar os testes com os documentos reais:

```powershell
$env:FOLHA_LAYOUT_SAMPLE_PDF = "C:\caminho\folha-layout.pdf"
$env:FOLHA_SAMPLE_PDF = "C:\caminho\folha-estruturada.pdf"
.\scripts\test.ps1
```

PDFs, XLSX, ambientes virtuais, logs e artefatos de build estão excluídos do Git.

## Gerar o aplicativo e o instalador

Pré-requisito adicional na máquina de build: Inno Setup 6.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

O script executa os testes, gera o ícone, cria o aplicativo em modo `onedir` e
compila o instalador. Os artefatos ficam em:

```text
dist\ConversorFolhas\
installer\output\Conversor-de-Folhas-Setup-<versão>.exe
```

Para validar somente o empacotamento, sem criar instalador:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build.ps1 -SkipInstaller
```
