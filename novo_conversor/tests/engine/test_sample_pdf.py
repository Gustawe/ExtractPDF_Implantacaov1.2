import os
from decimal import Decimal
from pathlib import Path
from unittest import TestCase, skipUnless

from folha_pdf_xlsx.extractor import PayrollPdfExtractor
from folha_pdf_xlsx.validation import validate_document


SAMPLE = os.environ.get("FOLHA_SAMPLE_PDF", "")


@skipUnless(SAMPLE and Path(SAMPLE).is_file(), "FOLHA_SAMPLE_PDF não definido")
class SamplePdfTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = PayrollPdfExtractor().extract(SAMPLE)
        cls.document.validations = validate_document(cls.document)

    def test_employee_and_contributor_count(self):
        employees = [
            item for item in self.document.employees if item.record_type == "EMPREGADO"
        ]
        contributors = [
            item
            for item in self.document.employees
            if item.record_type == "CONTRIBUINTE"
        ]
        self.assertEqual(len(employees), 32)
        self.assertEqual(len(contributors), 1)

    def test_document_totals_reconcile(self):
        document_checks = [
            check
            for check in self.document.validations
            if check.scope == "DOCUMENTO"
        ]
        self.assertTrue(document_checks)
        self.assertTrue(all(check.status == "OK" for check in document_checks))

    def test_fiscal_summary_preserves_headcount_and_total_due(self):
        fiscal_index = {
            (item.section, item.subgroup, item.item): item.value
            for item in self.document.fiscal_records
        }
        self.assertEqual(
            fiscal_index[("Situações", "ESQUERDA", "No. Empregados:")],
            Decimal("32"),
        )
        self.assertEqual(
            fiscal_index[
                ("Apuração Tributos Federais", "TOTAL", "Saldo à recolher")
            ],
            Decimal("43768.65"),
        )
