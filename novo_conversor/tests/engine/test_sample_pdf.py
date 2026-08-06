import os
from decimal import Decimal
from pathlib import Path
from unittest import TestCase, skipUnless

from folha_pdf_xlsx.extractor import PayrollPdfExtractor
from folha_pdf_xlsx.validation import validate_document


SAMPLE = os.environ.get("FOLHA_SAMPLE_PDF", "")
AUGUST_2024_SAMPLE = os.environ.get("FOLHA_AUGUST_2024_PDF", "")


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


@skipUnless(
    AUGUST_2024_SAMPLE and Path(AUGUST_2024_SAMPLE).is_file(),
    "FOLHA_AUGUST_2024_PDF não definido",
)
class August2024RegressionTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = PayrollPdfExtractor().extract(AUGUST_2024_SAMPLE)
        cls.document.validations = validate_document(cls.document)

    def test_event_counts_totals_and_validations_reconcile(self):
        earnings = [event for event in self.document.events if event.kind == "P"]
        discounts = [event for event in self.document.events if event.kind == "D"]

        self.assertEqual(len(earnings), 48)
        self.assertEqual(len(discounts), 184)
        self.assertEqual(
            sum((event.value for event in earnings), Decimal()),
            Decimal("177320.84"),
        )
        self.assertEqual(
            sum((event.value for event in discounts), Decimal()),
            Decimal("98556.17"),
        )
        self.assertFalse(
            any(
                check.status in {"DIVERGÊNCIA", "FALHA"}
                for check in self.document.validations
            )
        )

    def test_names_statuses_and_fiscal_summary_are_processed(self):
        known_statuses = ("Trabalhando", "Demitido")

        self.assertTrue(self.document.fiscal_records)
        self.assertFalse(self.document.issues)
        self.assertTrue(all(employee.status for employee in self.document.employees))
        self.assertFalse(
            any(
                employee.name.endswith(known_statuses)
                or "Situação:" in employee.name
                for employee in self.document.employees
            )
        )
