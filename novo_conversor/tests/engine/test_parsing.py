from decimal import Decimal
from unittest import TestCase

from folha_pdf_xlsx.parsing import parse_br_date, parse_br_decimal, parse_br_number
from folha_pdf_xlsx.extractor import PdfLine, PayrollPdfExtractor


def _pdf_line(top: float, *words: tuple[str, float]) -> PdfLine:
    return PdfLine(
        top=top,
        words=[{"text": text, "x0": x0} for text, x0 in words],
    )


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

    def test_discount_marker_and_long_value_are_parsed_at_current_boundary(self):
        line = _pdf_line(
            200.0,
            ("998", 312.42),
            ("I.N.S.S.", 333.84),
            ("11,00", 482.22),
            ("4.406,69", 524.10),
            ("D", 556.56),
        )

        event = PayrollPdfExtractor._parse_event_half(
            "folha.pdf", 1, "funcionario", "71", line, "D"
        )

        self.assertIsNotNone(event)
        self.assertEqual(event.code, "998")
        self.assertEqual(event.description, "I.N.S.S.")
        self.assertEqual(event.reference, "11,00")
        self.assertEqual(event.value, Decimal("4406.69"))

    def test_employee_header_separates_name_status_cpf_and_admission(self):
        header = _pdf_line(
            105.12,
            ("Empr.:", 14.82),
            ("71", 69.06),
            ("Pessoa", 72.78),
            ("de", 98.03),
            ("Teste", 117.86),
            ("Situação:Trabalhando", 218.34),
            ("CPF:123.456.789-00", 361.26),
            ("Adm:", 473.76),
            ("22/05/2024", 536.28),
        )

        employee = PayrollPdfExtractor()._parse_employee(
            "folha.pdf",
            1,
            1,
            [header, _pdf_line(115.44), _pdf_line(125.76)],
        )

        self.assertEqual(employee.registration, "71")
        self.assertEqual(employee.name, "Pessoa de Teste")
        self.assertEqual(employee.status, "Trabalhando")
        self.assertEqual(employee.cpf, "123.456.789-00")
        self.assertEqual(employee.admission_date.isoformat(), "2024-05-22")

    def test_long_contributor_name_is_split_inside_combined_status_token(self):
        header = _pdf_line(
            352.80,
            ("Contr:", 14.82),
            ("1NOME", 72.78),
            ("COMPOSTO", 103.34),
            ("LONGSAituação:Demitido", 182.60),
            ("CPF:987.654.321-00", 361.26),
            ("Adm:", 473.76),
            ("03/03/2022", 536.28),
        )

        employee = PayrollPdfExtractor()._parse_employee(
            "folha.pdf",
            9,
            1,
            [header, _pdf_line(363.12), _pdf_line(373.44)],
        )

        self.assertEqual(employee.record_type, "CONTRIBUINTE")
        self.assertEqual(employee.registration, "1")
        self.assertEqual(employee.name, "NOME COMPOSTO LONGA")
        self.assertEqual(employee.status, "Demitido")

    def test_employee_header_keeps_coordinate_fallback_for_legacy_layout(self):
        header = _pdf_line(
            100.0,
            ("Empr.:", 14.0),
            ("9", 69.0),
            ("Pessoa", 75.0),
            ("Legada", 110.0),
            ("Trabalhando", 260.0),
            ("123.456.789-00", 390.0),
            ("01/01/2020", 536.0),
        )

        employee = PayrollPdfExtractor()._parse_employee(
            "legada.pdf",
            1,
            1,
            [header, _pdf_line(110.0), _pdf_line(120.0)],
        )

        self.assertEqual(employee.registration, "9")
        self.assertEqual(employee.name, "Pessoa Legada")
        self.assertEqual(employee.status, "Trabalhando")
        self.assertEqual(employee.cpf, "123.456.789-00")
