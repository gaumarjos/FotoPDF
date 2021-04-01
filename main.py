# Stefano Salati 2021-03-17
# Untested, have fun!

# Docs
# https://www.reportlab.com/docs/reportlab-userguide.pdf
# https://python-utilities.readthedocs.io/en/latest/dll.html

from os import listdir
from os.path import join, getsize  # , isfile
from fpdf import FPDF
import PIL.Image
from PIL.ExifTags import TAGS
# import sys
# from pdfrw import PageMerge, PdfReader, PdfWriter
import re
import getopt
import sys
import json
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph  # , Image, Flowable
from reportlab.lib.styles import getSampleStyleSheet  # , ParagraphStyle
from reportlab.lib import colors
# from reportlab.lib.pagesizes import A4, landscape
import reportlab.rl_config
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
reportlab.rl_config.warnOnMissingFontGlyphs = 0

# Constants
USE_FPDF = False
USE_RL = True


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    return [atoi(c) for c in re.split(r'(\d+)', text)]


def FPDFCenteredText(p, text, font, size, y, black=True):
    p.set_y(y)
    p.set_font(font, '', size)
    if black:
        p.set_text_color(0, 0, 0)
    else:
        p.set_text_color(255, 255, 255)
    p.cell(0, 0, text, 0, 1, align="C", fill=False)
    p.set_text_color(0, 0, 0)


def RLSingleLineCenteredText(c, text, font, size, page_height, page_width, y, black=True):
    c.setFont(font, size)
    if black:
        c.setFillColorRGB(0, 0, 0)
    else:
        c.setFillColorRGB(1, 1, 1)
    text_width = c.stringWidth(text, font, size)
    c.drawString((page_width - text_width) / 2.0, page_height - y, text)
    # Alternative solution
    # t = c.beginText()
    # t.setTextOrigin(int(obj['description']['from_side']*MM2PT), int(H-obj['description']['from_top']*MM2PT))
    # t.setFont('myfont', 16)
    # t.textLine(obj['description']['string'])
    # c.drawText(t)


def RLText(c, text, font, alignment, size, interline, from_side, from_top, page_width, page_height, black=True):
    stylesheet = getSampleStyleSheet()
    style = stylesheet['BodyText']
    style.fontSize = size
    style.fontName = font
    style.alignment = alignment
    if black:
        style.textColor = colors.black
    else:
        style.textColor = colors.white
    style.leading = size + interline
    p = Paragraph(text, style)
    aW = page_width - (from_side * 2)
    aH = page_height - from_top
    w, h = p.wrap(aW, aH)
    if w <= aW and h <= aH:
        p.drawOn(c, from_side, page_height - from_top - h)
    else:
        print("Error: text cell too small for text.")


def RLCenteredImage(c, image, from_side, page_width, page_height):
    pil_image = PIL.Image.open(image)
    original_image_size = pil_image.size

    # Read EXIF ImageDescription field from JPG
    info = pil_image.getexif()
    try:
        caption = info[270]
    except:
        caption = ""
    # Code to read all EXIF fields
    # exif_table = {}
    # for tag, value in info.items():
    #    decoded = TAGS.get(tag, tag)
    #    exif_table[decoded] = value
    # print(exif_table)

    wanted_width = page_width - from_side * 2
    ratio = wanted_width / original_image_size[0]
    wanted_height = original_image_size[1] * ratio
    c.drawImage(image,
                x=from_side,
                y=page_height - from_side - wanted_height,
                width=wanted_width,
                height=wanted_height,
                mask=None)
    # Alternative solution (to be used only if used also in the grid,
    # otherwise the images are not recognised as the same and saved twice in the file.
    # im = Image(image, width=wanted_width, height=wanted_height)
    # im.hAlign = 'CENTER'
    # im.drawOn(c, from_side, page_height - from_side - wanted_height)
    return caption


def main(argv):
    # ciao = sysfont.get_font(name: string[, style = STYLE_NORMAL[, ftype = None]]) -> (str, str, int, str, str)

    # Default
    input_folder = "."
    output_filename = "slides"

    # Command line
    try:
        opts, args = getopt.getopt(argv, "i:o:",
                                   ["input_folder=", "output_filename="])
    except getopt.GetoptError:
        print("Error: wrong arguments.")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-i", "--input_folder"):
            input_folder = arg
        elif opt in ("-o", "--output_filename"):
            output_filename = arg

    # Lettura JSON
    with open(input_folder + 'settings.json', 'r') as myjson:
        data = myjson.read()
    obj = json.loads(data)
    H = obj["document"]["height"]
    W = obj["document"]["width"]
    print("Slide format: {:d}x{:d}pt.".format(H, W))

    # Creazione file e impostazioni generali
    if USE_FPDF:
        # Constructor
        print("Generating PDF with FPDF...")
        full_output_filename = join(input_folder, output_filename + ".pdf")
        pdf = FPDF(orientation='L', unit='pt', format=(H, W))
        pdf.set_compression(True)
        pdf.set_margins(0, 0, 0)
        pdf.set_auto_page_break(False)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(0, 0, 0)
        pdf.set_title(obj["document"]["title"])
        pdf.set_author(obj["document"]["author"])

        # Use user-defined True Type Font (TTF)
        pdf.add_font('font_title', '', obj["fonts"]["title"], uni=True)
        pdf.add_font('font_author', '', obj["fonts"]["author"], uni=True)
        pdf.add_font('font_text', '', obj["fonts"]["text"], uni=True)

    if USE_RL:
        # Constructor
        print("Generating PDF with Reportlab...")
        full_output_filename_reportlab = join(input_folder, output_filename + "_reportlab.pdf")
        c = canvas.Canvas(full_output_filename_reportlab, enforceColorSpace='RGB')
        c.setPageSize((W, H))
        c.setTitle(obj["document"]["title"])
        c.setAuthor(obj["document"]["author"])

        # Use user-defined True Type Font (TTF)
        pdfmetrics.registerFont(TTFont('font_title', obj["fonts"]["title"]))
        pdfmetrics.registerFont(TTFont('font_author', obj["fonts"]["author"]))
        pdfmetrics.registerFont(TTFont('font_text', obj["fonts"]["text"]))
        c.setFont('font_text', 16)

    # Ricerca immagini
    images = [f for f in listdir(input_folder) if f.endswith(".jpg")]
    images.sort(key=natural_keys)

    # Cover page
    if bool(obj['cover']['show']):
        if USE_FPDF:
            pdf.add_page()
            if obj["cover"]["useimage"] >= 0:
                pdf.image(join(input_folder, images[obj["cover"]["useimage"] - 1]), x=-10, y=0, w=0, h=H, type="JPEG")
            FPDFCenteredText(pdf, obj['document']['title'], 'myfont', int(obj['cover']['title']['size']),
                             int(obj['cover']['title']['from_top']), obj["cover"]["title"]["black_text"])
            FPDFCenteredText(pdf, obj["document"]["author"], 'myfont', int(obj['cover']['author']['size']),
                             int(obj['cover']['author']['from_top']), obj["cover"]["author"]["black_text"])
        if USE_RL:
            original_image_size = PIL.Image.open(join(input_folder, images[obj["cover"]["useimage"] - 1])).size
            c.drawImage(join(input_folder, images[obj["cover"]["useimage"] - 1]), (W - original_image_size[0]) / 2, 0,
                        width=None, height=H, preserveAspectRatio=True)
            RLText(c, obj['document']['title'], 'font_title', 1, int(obj['cover']['title']['size']),
                   int(obj['cover']['title']['interline']), int(obj['cover']['title']['from_side']), int(obj['cover']['title']['from_top']), W, H,
                   black=obj["cover"]["title"]["black_text"])
            RLSingleLineCenteredText(c, obj["document"]["author"], 'font_author', int(obj['cover']['author']['size']),
                                     H, W,
                                     int(obj['cover']['author']['from_top']), obj["cover"]["author"]["black_text"])
            c.showPage()

    # Text page
    if bool(obj['description']['show']):
        if USE_FPDF:
            pdf.add_page()
            pdf.set_y(int(obj['description']['from_top']))
            pdf.set_x(int(obj['description']['from_side']))
            pdf.set_font_size(int(obj['description']['size']))
            pdf.multi_cell(w=W - int(obj['description']['from_side']) * 2, h=int(obj['description']['interline']),
                           txt=obj['description']['string'], border=0, align="L", fill=False)

        if USE_RL:
            text = obj['description']['string']
            text = text.replace("\n", "<br/>")
            RLText(c, text, 'font_text', 0, obj['description']['size'],
                   obj['description']['interline'], obj['description']['from_side'],
                   obj['description']['from_top'], W, H)
            c.showPage()

    # Full-page images
    if USE_FPDF:
        pdf.set_font_size(int(obj['photos']['size']))
        for i, image in enumerate(images):
            pdf.add_page()
            pdf.image(join(input_folder, image), x=12, y=10, w=W - 24, h=0, type="JPEG")
            pdf.set_y(H - 16)
            pdf.set_x(int(obj['photos']['from_side']))
            pdf.multi_cell(w=W - int(obj['photos']['from_side']) * 2, h=int(obj['photos']['interline']),
                           txt=str(obj['photos']['captions'][i]['caption']), border=0, align="L", fill=False)

    if USE_RL:
        for i, image in enumerate(images):
            caption = RLCenteredImage(c, join(input_folder, image), 24, W, H)
            # caption = obj['photos']['captions'][i]['caption']
            RLText(c, caption, 'font_text', 0, obj['photos']['size'],
                   obj['photos']['interline'], obj['photos']['from_side'],
                   690, W, H)
            c.showPage()

    # Grid
    R = int(obj['contactsheet']['rows'])
    C = int(obj['contactsheet']['columns'])
    m_oriz = obj["contactsheet"]["horizontal_margin"]
    m_vert = obj["contactsheet"]["vertical_margin"]
    m_lat = obj["contactsheet"]["lateral_margin"]

    # Parto dalle colonne e vedo se l'altezza sta nei margini
    w = (W - 2 * m_lat - (C - 1) * m_oriz) / C
    h = w / 3. * 2.
    total_h = R * h + (R - 1) * m_vert + m_lat
    # E' troppo alta, devo ripartire dalle righe e calcolare le colonne di conseguenza
    if total_h > H:
        h = (H - 2 * m_lat - (R - 1) * m_vert) / R
        w = h * 3. / 2.
        total_w = C * w + (C - 1) * m_oriz + m_lat
        if total_w > W:
            print("Non può essere.")

    if USE_FPDF:
        pdf.add_page()
        if bool(obj['contactsheet']['black_background']):
            pdf.set_fill_color(0, 0, 0)
            pdf.cell(0, H, "", 0, 1, align="C", fill=True)
        for i, image in enumerate(images):
            pdf.image(join(input_folder, image),
                      x=(W - (C * w + (C - 1) * m_oriz)) / 2 + (i % C) * (w + m_oriz),
                      y=(H - (R * h + (R - 1) * m_vert)) / 2 + int(i / C) * (h + m_vert),
                      w=w, h=0)
    if USE_RL:
        for i, image in enumerate(images):
            c.drawImage(join(input_folder, image),
                        x=(W - (C * w + (C - 1) * m_oriz)) / 2 + (i % C) * (w + m_oriz),
                        y=H - h - ((H - (R * h + (R - 1) * m_vert)) / 2 + int(i / C) * (h + m_vert)),
                        width=w,
                        height=h,
                        mask=None)
        c.showPage()

    # Pagina finale
    if obj['final']['show']:
        if USE_FPDF:
            pdf.add_page()

        if bool(obj['final']['author']['show']):
            if USE_FPDF:
                FPDFCenteredText(pdf,
                                 obj['document']['author'],
                                 'font_text',
                                 obj['final']['author']['size'],
                                 obj['final']['author']['from_top'], black=True)
            if USE_RL:
                RLSingleLineCenteredText(c,
                                         obj['document']['author'],
                                         'font_text',
                                         obj['final']['author']['size'],
                                         H, W,
                                         obj['final']['author']['from_top'],
                                         True)

        if bool(obj['final']['website']['show']):
            if USE_FPDF:
                FPDFCenteredText(pdf,
                                 obj['final']['website']['string'],
                                 'font_text',
                                 obj['final']['website']['size'],
                                 obj['final']['website']['from_top'], black=True)
            if USE_RL:
                RLSingleLineCenteredText(c,
                                         obj['final']['website']['string'],
                                         'font_text',
                                         obj['final']['website']['size'],
                                         H, W,
                                         obj['final']['website']['from_top'],
                                         True)

        if bool(obj['final']['email']['show']):
            if USE_FPDF:
                FPDFCenteredText(pdf,
                                 obj['final']['email']['string'],
                                 'font_text',
                                 obj['final']['email']['size'],
                                 obj['final']['email']['from_top'], black=True)
            if USE_RL:
                RLSingleLineCenteredText(c,
                                         obj['final']['email']['string'],
                                         'font_text',
                                         obj['final']['email']['size'],
                                         H, W,
                                         obj['final']['email']['from_top'],
                                         True)

        if bool(obj['final']['phone']['show']):
            if USE_FPDF:
                FPDFCenteredText(pdf,
                                 obj['final']['phone']['string'],
                                 'font_text',
                                 obj['final']['phone']['size'],
                                 obj['final']['phone']['from_top'], black=True)
            if USE_RL:
                RLSingleLineCenteredText(c,
                                         obj['final']['phone']['string'],
                                         'font_text',
                                         obj['final']['phone']['size'],
                                         H, W,
                                         obj['final']['phone']['from_top'],
                                         True)

        if bool(obj['final']['phone']['show']):
            if USE_FPDF:
                FPDFCenteredText(pdf,
                                 obj['final']['disclaimer']['string'],
                                 'font_text',
                                 obj['final']['disclaimer']['size'],
                                 obj['final']['disclaimer']['from_top'], black=True)
            if USE_RL:
                RLSingleLineCenteredText(c,
                                         obj['final']['disclaimer']['string'],
                                         'font_text',
                                         obj['final']['disclaimer']['size'],
                                         H, W,
                                         obj['final']['disclaimer']['from_top'],
                                         True)

        if USE_RL:
            c.showPage()

    # Salva
    if USE_FPDF:
        pdf.output(full_output_filename, "F")
        print("{:s} created ({:.1f}MB)!".format(full_output_filename, getsize(full_output_filename) / 1000000.))
    if USE_RL:
        c.save()
        print("{:s} created ({:.1f}MB)!".format(full_output_filename_reportlab,
                                                getsize(full_output_filename_reportlab) / 1000000.))


if __name__ == "__main__":
    main(sys.argv[1:])

# if C == -1 or R == -1:
#     print("Calcolo miglior disposizione griglia...")
#     N = len(images)
#     possibili_colonne = np.arange(N * 1.) + 1
#     possibili_righe = np.ceil(N / possibili_colonne)
#     possibili_aree_immagini_a_guida_colonne = ((W - 2 * m_lat) / possibili_colonne) ** 2 * (2 / 3)
#     possibili_aree_immagini_a_guida_righe = ((H - 2 * m_lat) / possibili_righe) ** 2 * (3 / 2)
#     aree_risultanti = np.minimum(possibili_aree_immagini_a_guida_colonne, possibili_aree_immagini_a_guida_righe)
#     i_migliore = np.where(aree_risultanti == np.max(aree_risultanti))
#     R = possibili_righe[i_migliore]
#     C = possibili_colonne[i_migliore]
#     # print(possibili_colonne)
#     # print(possibili_righe)
#     # print(aree_risultanti)
#     max_to_min_sort_index = np.argsort(aree_risultanti)[::-1]
#     print(possibili_righe[max_to_min_sort_index][:4])
#     print(possibili_colonne[max_to_min_sort_index][:4])
#     print(aree_risultanti[max_to_min_sort_index][:4])


# def new_content():
#     ...
#
# reader = PdfReader(fdata=bytes(pdf.output()))
#         return reader
#
#     ciao = new_content()
#
#     y = PdfWriter()
#     for i in range(len(ciao.pages)):
#         y.addpage(ciao.pages[i])
#     y.write('result.pdf')
