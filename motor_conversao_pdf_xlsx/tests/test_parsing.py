from decimal import Decimal
from unittest import TestCase

from folha_pdf_xlsx.parsing import parse_br_date, parse_br_decimal, parse_br_number


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
