from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from openpyxl import load_workbook

from folha_pdf_xlsx.batch import process_consolidated


class BatchTests(TestCase):
    def test_consolidated_records_failed_pdf_without_stopping(self):
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            output = directory / "consolidado.xlsx"
            with patch(
                "folha_pdf_xlsx.batch.process_pdf",
                side_effect=ValueError("layout não reconhecido"),
            ):
                generated, failed_count = process_consolidated(
                    [directory / "invalido.pdf"],
                    output,
                )

            self.assertEqual(failed_count, 1)
            self.assertEqual(generated, output.resolve())
            workbook = load_workbook(generated, data_only=True)
            self.assertEqual(
                workbook["Processamento"]["N2"].value,
                "REPROVADO",
            )
            self.assertEqual(
                workbook["Pendencias"]["C2"].value,
                "FALHA_PROCESSAMENTO",
            )
            workbook.close()
