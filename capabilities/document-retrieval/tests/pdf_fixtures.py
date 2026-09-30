"""Original synthetic PDFs created in pytest temporary directories only."""
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject, ArrayObject


def make_pdf(path, pages, *, invisible=False, prefix=""):
    writer = PdfWriter()
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type0'),
        NameObject('/BaseFont'): NameObject('/STSong-Light'), NameObject('/Encoding'): NameObject('/UniGB-UCS2-H'),
        NameObject('/DescendantFonts'): ArrayObject([DictionaryObject({NameObject('/Type'): NameObject('/Font'),
        NameObject('/Subtype'): NameObject('/CIDFontType0'), NameObject('/BaseFont'): NameObject('/STSong-Light'),
        NameObject('/CIDSystemInfo'): DictionaryObject()})])})
    for text in pages:
        page = writer.add_blank_page(width=612, height=792)
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): font})})
        stream = DecodedStreamObject()
        data = prefix + f'BT /F1 12 Tf {3 if invisible else 0} Tr 20 700 Td <{text.encode("utf-16-be").hex()}> Tj ET'
        stream.set_data(data.encode())
        page[NameObject('/Contents')] = writer._add_object(stream)
    writer.write(path)
    return path
