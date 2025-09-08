from pdf2image import convert_from_path
from io import BytesIO

def pdf_to_jpg(
    path: str,
    page_number: int,
    path_output: str = None
    ):
    """ Converte PDF para JPG
    :param path: [str] Path do arquivo PDF a ser convertido
    :param path_output: [str|None] Path do arquivo JPG final (opcional)
    :param page_number: [int] Numero da pagina a ser convertida
    :return bytes: Bytes da imagem JPG
    """
    pages = convert_from_path(path, 100)
    img = pages[page_number-1]
    img_bytes = BytesIO()
    img.save(img_bytes, 'JPEG')
    img_bytes.seek(0)
    if path_output is not None:
        img.save(path_output, 'JPEG')
    return img_bytes.getvalue()
