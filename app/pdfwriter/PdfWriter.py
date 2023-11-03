from fillpdf import fillpdfs

class PdfWriter:
    def __init__(self, input_filename, output_filename) -> None:
        self.input_filename = input_filename
        self.output_filename = output_filename

    def fillForm(self, data_dict):
        fillpdfs.write_fillable_pdf(self.input_filename, self.output_filename, data_dict)
        #fillpdfs.flatten_pdf(self.output_filename, self.output_filename)