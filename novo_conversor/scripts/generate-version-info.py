"""Gera metadados de versão do executável a partir da versão do pacote."""

from __future__ import annotations

from pathlib import Path

from conversor_folhas import __version__


def _numeric_version(version: str) -> tuple[int, int, int, int]:
    parts = [int(part) for part in version.split(".")]
    if len(parts) > 4:
        raise ValueError(f"Versão inválida: {version}")
    padded = parts + [0] * (4 - len(parts))
    return padded[0], padded[1], padded[2], padded[3]


def create_version_info(output_path: Path) -> None:
    numeric = _numeric_version(__version__)
    content = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={numeric},
    prodvers={numeric},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '041604B0',
        [StringStruct('CompanyName', 'Equipe de Infraestrutura de TI'),
         StringStruct('FileDescription', 'Conversor de Folhas — Implantação'),
         StringStruct('FileVersion', '{__version__}'),
         StringStruct('InternalName', 'ConversorFolhas'),
         StringStruct('OriginalFilename', 'ConversorFolhas.exe'),
         StringStruct('ProductName', 'Conversor de Folhas — Implantação'),
         StringStruct('ProductVersion', '{__version__}')]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1046, 1200])])
  ]
)
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    create_version_info(project_root / "build" / "version_info.txt")
