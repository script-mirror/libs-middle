from pdf2image import convert_from_path

def pdf_to_jpg(
    path:str,
    page_number:int,
    path_output:str
    ):
    """ Converte PDF para JPG
    :param path: [str] Path do arquivo PDF a ser convertido
    :param path_output: [str] Path do arquivo JPG final
    :param page_number: [int] Numero da pagina a ser convertida
    :return None: 
    """
    pages = convert_from_path(path, 100)
    pages[page_number-1].save(path_output, 'JPEG')
