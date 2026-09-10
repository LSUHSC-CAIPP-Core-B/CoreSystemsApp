from unittest.mock import patch

from app.pdfwriter.PdfWriter import PdfWriter


class TestPdfWriterInit:
    def test_stores_input_and_output_filenames(self):
        writer = PdfWriter("input.pdf", "output.pdf")
        assert writer.input_filename == "input.pdf"
        assert writer.output_filename == "output.pdf"


class TestFillForm:
    @patch("app.pdfwriter.PdfWriter.fillpdfs.write_fillable_pdf")
    def test_calls_write_fillable_pdf_with_filenames_and_data(self, mock_write):
        writer = PdfWriter("input.pdf", "output.pdf")
        data = {"Name": "John Smith", "Date": "2024-01-01"}

        writer.fillForm(data)

        mock_write.assert_called_once_with("input.pdf", "output.pdf", data)

    @patch("app.pdfwriter.PdfWriter.fillpdfs.write_fillable_pdf")
    def test_empty_data_dict_still_calls_write(self, mock_write):
        writer = PdfWriter("input.pdf", "output.pdf")

        writer.fillForm({})

        mock_write.assert_called_once_with("input.pdf", "output.pdf", {})
