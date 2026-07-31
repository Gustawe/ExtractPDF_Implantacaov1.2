# Conversor de Folhas — Implantação

Aplicativo Windows para converter folhas de pagamento em PDF para XLSX. O
processamento é local e utiliza o pacote `folha_pdf_xlsx` incluído no próprio
projeto.

## Estado atual

A versão `0.3.0` contém o primeiro fluxo executável:

- Seleção individual de vários PDFs.
- Seleção de uma pasta, sem percorrer subpastas.
- Arrastar e soltar arquivos ou pastas.
- Fila compacta com estado individual.
- Conversão serial fora da thread da interface.
- Progresso geral do lote.
- Saída na mesma pasta do PDF.
- Renomeação automática sem sobrescrever XLSX existentes.
- Abertura do XLSX ou da pasta de destino.
- Tema claro e escuro.
- Logs rotativos em `%LOCALAPPDATA%\ConversorFolhas\logs`.

Histórico local e empacotamento com instalador serão implementados nas próximas
etapas.

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

