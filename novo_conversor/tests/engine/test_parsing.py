from decimal import Decimal
from unittest import TestCase

from folha_pdf_xlsx.parsing import parse_br_date, parse_br_decimal, parse_br_number
from folha_pdf_xlsx.extractor import PdfLine, PayrollPdfExtractor


class ParsingTests(TestCase):
    def test_parse_br_decimal(self):
        self.assertEqual(parse_br_decimal("3.387,29"), Decimal("3387.29"))
        self.assertEqual(parse_br_decimal("-20,87"), Decimal("-20.87"))
        self.assertIsNone(parse_br_decimal("2:54"))

    def test_parse_br_date(self):
        parsed = parse_br_date("11/02/2025")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.isoformat(), "2025-02-11")

    def test_parse_br_number_accepts_integer(self):
        self.assertEqual(parse_br_number("32"), Decimal("32"))
        self.assertEqual(parse_br_number("14.459,58"), Decimal("14459.58"))

    def test_thirteenth_event_marker_at_legacy_boundary_is_parsed(self):
        line = PdfLine(
            top=200.0,
            words=[
                {"text": "13", "x0": 40.5},
                {"text": "13", "x0": 50.8},
                {"text": "SALARIO", "x0": 60.4},
                {"text": "ADIANTADO", "x0": 89.6},
                {"text": "12,00", "x0": 202.2},
                {"text": "2.500,00", "x0": 253.6},
                {"text": "P", "x0": 281.7},
            ],
        )

        event = PayrollPdfExtractor._parse_event_half(
            "folha.pdf", 1, "funcionario", "130", line, "P"
        )

        self.assertIsNotNone(event)
        self.assertEqual(event.code, "13")
        self.assertEqual(event.description, "13 SALARIO ADIANTADO")
        self.assertEqual(event.value, Decimal("2500.00"))
