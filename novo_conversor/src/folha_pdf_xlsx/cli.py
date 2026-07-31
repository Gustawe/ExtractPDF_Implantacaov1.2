from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

from .batch import process_consolidated, process_individual
from .logging_config import configure_logging


def _expand_inputs(patterns: list[str]) -> list[Path]:
    resolved: list[Path] = []
    for pattern in patterns:
        matches = glob.glob(pattern)
        candidates = matches or [pattern]
        for candidate in candidates:
            path = Path(candidate).resolve()
            if path.is_file() and path.suffix.lower() == ".pdf" and path not in resolved:
                resolved.append(path)
    return resolved


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Converte folhas de pagamento em PDF para XLSX."
    )
    parser.add_argument("inputs", nargs="+", help="PDFs ou padrões glob.")
    parser.add_argument(
        "--mode",
        choices=("individual", "consolidated"),
        default="individual",
        help="Gera um XLSX por PDF ou um arquivo consolidado.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Diretório no modo individual ou arquivo XLSX no consolidado.",
    )
    parser.add_argument(
        "--diagnostic",
        action="store_true",
        help="Habilita log detalhado, que pode conter dados pessoais.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(Path.cwd() / "logs", diagnostic=args.diagnostic)
    pdf_paths = _expand_inputs(args.inputs)
    if not pdf_paths:
        print("Nenhum PDF válido foi encontrado.", file=sys.stderr)
        return 2

    output = Path(args.output).resolve()
    if args.mode == "individual":
        generated, failed_count = process_individual(pdf_paths, output)
        for path in generated:
            print(path)
        if failed_count:
            print(
                f"{failed_count} arquivo(s) foram reprovados. Consulte os XLSX e os logs.",
                file=sys.stderr,
            )
            return 1
        return 0

    if output.suffix.lower() != ".xlsx":
        output = output / "folhas_consolidadas.xlsx"
    generated_path, failed_count = process_consolidated(pdf_paths, output)
    print(generated_path)
    if failed_count:
        print(
            f"{failed_count} arquivo(s) foram reprovados. Consulte a aba Pendencias.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
