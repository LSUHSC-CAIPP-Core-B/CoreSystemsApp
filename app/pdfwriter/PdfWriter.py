from fillpdf import fillpdfs

class PdfWriter:
    """
    Fills data to PDF

    input_filename (str): path to input PDF file to fill data into
    input_filename (str): path to which save filled PDF
    """
    def __init__(self, input_filename, output_filename) -> None:
        self.input_filename = input_filename
        self.output_filename = output_filename

    def fillForm(self, data_dict):
        """
        Fill data to PDF and save to another PDF

        data_dict (dict): dict of field keys to which input provided values
        """
        fillpdfs.write_fillable_pdf(self.input_filename, self.output_filename, data_dict)

