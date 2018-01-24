from wand.image import Image
from PIL import Image as PI
import pyocr
import pyocr.builders
import io

''' Template de código para reconhecimento de imagem
    fonte: https://xiaofeima1990.github.io/2016/12/19/extract-text-from-sanned-pdf/
'''

def scan_pdf(path_to_pdf):
    tool = pyocr.get_available_tools()[0]
    lang = tool.get_available_languages()[0]

    req_image = []
    final_text = []

    image_pdf =  Image(filename=path_to_pdf, resolution=300)
    image_jpeg = image_pdf.convert('jpeg')

    for img in image_jpeg.sequence:
        img_page = Image(image=img)
        req_image.append(img_page.make_blob('jpeg'))

    for img in req_image:
        txt = tool.image_to_string(
            PI.open(io.BytesIO(img)),
            lang=lang,
            builder=pyocr.builders.TextBuilder()
        )
        final_text.append(txt)

    return final_text
