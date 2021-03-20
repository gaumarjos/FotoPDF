# Stefano Salati 2021-03-17
# Untested, have fun!

# Docs
# https://www.reportlab.com/docs/reportlab-userguide.pdf

from os import listdir
from os.path import isfile, join, getsize
from fpdf import FPDF
import PIL.Image
#import sys
#from pdfrw import PageMerge, PdfReader, PdfWriter
import re
import getopt
import sys
import json
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Flowable
from reportlab.lib.pagesizes import A4, landscape
import reportlab.rl_config
reportlab.rl_config.warnOnMissingFontGlyphs = 0
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


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


def RLCenteredText(c, text, font, size, page_height, page_width, y, black=True):
    c.setFont(font, size)
    if black:
        c.setFillColorRGB(0, 0, 0)
    else:
        c.setFillColorRGB(0.9, 0.9, 0.9)
    text_width = c.stringWidth(text, font, size)
    c.drawString((page_width - text_width) / 2.0, page_height-y, text)


def main(argv):

    # Constants
    USE_FPDF = True
    USE_RL = True

    # Valori default
    input_folder = "."
    output_filename = "slides"

    # Interpretazione linea di comando
    try:
        opts, args = getopt.getopt(argv, "i:o:",
                                   ["input_folder=", "output_filename="])
    except getopt.GetoptError:
        print("Dai su...")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-i", "--input_folder"):
            input_folder = arg
        elif opt in ("-o", "--output_filename"):
            output_filename = arg

    # Lettura JSON
    with open(input_folder+'settings.json', 'r') as myjson:
        data = myjson.read()
    obj = json.loads(data)

    # Creazione file e impostazioni generali
    if USE_FPDF:
        H = obj["document"]["height"]
        W = obj["document"]["width"]
        H_px = H * 0.0393701 * 72
        W_px = W * 0.0393701 * 72
        print("File format: {:.1f}x{:.1f}mm, corresponding to {:.1f}x{:.1f}px in 72dpi.".format(H, W, H_px, W_px))

        full_output_filename = join(input_folder, output_filename + ".pdf")
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.set_compression(True)
        pdf.set_margins(0, 0, 0)
        pdf.set_auto_page_break(False)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(0, 0, 0)
        pdf.set_title(obj["document"]["title"])
        pdf.set_author(obj["document"]["author"])

        # Use user-defined True Type Font (TTF)
        if bool(obj["font"]["usemyfont"]):
            try:
                pdf.add_font('myfont', '', obj["font"]["myfont"], uni=True)
                pdf.set_font('myfont', '', 48)
            except:
                pdf.set_font(obj["font"]["family"], '', 48)
        else:
            pdf.set_font(obj["font"]["family"], '', 48)

    if USE_RL:
        WIDTH, HEIGHT = landscape(A4)
        MM2PT = 2.83465

        full_output_filename_reportlab = join(input_folder, output_filename + "reportlab.pdf")
        c = canvas.Canvas(full_output_filename_reportlab, enforceColorSpace='RGB')
        c.setPageSize((landscape(A4)))
        c.setTitle(obj["document"]["title"])
        c.setAuthor(obj["document"]["author"])

        # Use user-defined True Type Font (TTF)
        if bool(obj["font"]["usemyfont"]):
            try:
                pdfmetrics.registerFont(TTFont('myfont', obj["font"]["myfont"]))
                c.setFont('myfont', 32)
            except:
                pass
        else:
            pass

    # Ricerca immagini
    images = [f for f in listdir(input_folder) if f.endswith(".jpg")]
    images.sort(key=natural_keys)

    # Copertina
    if bool(obj['cover']['show']):
        if USE_FPDF:
            pdf.add_page()
            if obj["cover"]["useimage"] >= 0:
                pdf.image(join(input_folder, images[obj["cover"]["useimage"]-1]), x=-10, y=0, w=0, h=H, type="JPEG")
            FPDFCenteredText(pdf, obj['cover']['title']['string'], 'myfont', int(obj['cover']['title']['size']),
                             int(obj['cover']['title']['from_top']), obj["cover"]["title"]["black_text"])
            FPDFCenteredText(pdf, obj["document"]["author"], 'myfont', int(obj['cover']['author']['size']),
                             int(obj['cover']['author']['from_top']), obj["cover"]["author"]["black_text"])
        if USE_RL:
            original_image_size = PIL.Image.open(join(input_folder, images[obj["cover"]["useimage"]-1])).size
            print(original_image_size)
            c.drawImage(join(input_folder, images[obj["cover"]["useimage"]-1]), (WIDTH-original_image_size[0])/2, 0,
                        width=None, height=HEIGHT, preserveAspectRatio=True)
            RLCenteredText(c, obj['cover']['title']['string'], 'myfont', int(obj['cover']['title']['size']), HEIGHT, WIDTH,
                           int(obj['cover']['title']['from_top'] * MM2PT), obj["cover"]["title"]["black_text"])
            RLCenteredText(c, obj["document"]["author"], 'myfont', int(obj['cover']['author']['size']), HEIGHT, WIDTH,
                           int(obj['cover']['author']['from_top'] * MM2PT), obj["cover"]["author"]["black_text"])
            c.showPage()

    # Pagina testo
    if bool(obj['description']['show']):
        pdf.add_page()
        pdf.set_y(int(obj['description']['from_top']))
        pdf.set_x(int(obj['description']['from_side']))
        pdf.set_font_size(int(obj['description']['size']))
        pdf.multi_cell(w=W-int(obj['description']['from_side'])*2, h=int(obj['description']['interline']), txt=obj['description']['string'], border=0, align="L", fill=False)

    # Aggiungi immagini
    pdf.set_font_size(int(obj['photos']['size']))
    for i, image in enumerate(images):
        pdf.add_page()
        pdf.image(join(input_folder, image), x=12, y=10, w=W-24, h=0, type="JPEG")
        pdf.set_y(H - 16)
        pdf.set_x(int(obj['photos']['from_side']))
        pdf.multi_cell(w=W - int(obj['photos']['from_side']) * 2, h=int(obj['photos']['interline']),
                       txt=str(obj['photos']['captions'][i]['caption']), border=0, align="L", fill=False)
        # Write number of photo in sequence
        #pdf.cell(0, 12, str(i + 1), 0, 1, align="C", fill=False)

    # Pagina contact sheet
    pdf.add_page()
    R = int(obj['contactsheet']['rows'])
    C = int(obj['contactsheet']['columns'])
    m_oriz = obj["contactsheet"]["horizontal_margin"]
    m_vert = obj["contactsheet"]["vertical_margin"]
    m_lat = obj["contactsheet"]["lateral_margin"]
    if bool(obj['contactsheet']['black_background']):
        pdf.set_fill_color(0, 0, 0)
        pdf.cell(0, H, "", 0, 1, align="C", fill=True)

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

    for i, image in enumerate(images):
        pdf.image(join(input_folder, image), x=(W - (C * w + (C - 1) * m_oriz)) / 2 + (i % C) * (w + m_oriz),
                  y=(H - (R * h + (R - 1) * m_vert)) / 2 + int(i / C) * (h + m_vert), w=w, h=0)

    # Pagina finale
    if True:
        pdf.add_page()

        if bool(obj['final']['author']['show']):
            pdf.set_y(int(obj['final']['author']['from_top']))
            pdf.set_font_size(int(obj['final']['author']['size']))
            pdf.cell(0, 0, obj["document"]["author"], 0, 1, align="C", fill=False)

        if bool(obj['final']['website']['show']):
            pdf.set_y(int(obj['final']['website']['from_top']))
            pdf.set_font_size(int(obj['final']['website']['size']))
            pdf.cell(0, 0, obj['final']['website']['string'], 0, 1, align="C", fill=False)

        if bool(obj['final']['email']['show']):
            pdf.set_y(int(obj['final']['email']['from_top']))
            pdf.set_font_size(int(obj['final']['email']['size']))
            pdf.cell(0, 0, obj['final']['email']['string'], 0, 1, align="C", fill=False)

        if bool(obj['final']['phone']['show']):
            pdf.set_y(int(obj['final']['phone']['from_top']))
            pdf.set_font_size(int(obj['final']['phone']['size']))
            pdf.cell(0, 0, obj['final']['phone']['string'], 0, 1, align="C", fill=False)

        if bool(obj['final']['disclaimer']['show']):
            pdf.set_y(int(obj['final']['disclaimer']['from_top']))
            pdf.set_font_size(int(obj['final']['disclaimer']['size']))
            pdf.cell(0, 0, obj['final']['disclaimer']['string'], 0, 1, align="C", fill=False)

    # Salva
    if USE_FPDF:
        pdf.output(full_output_filename, "F")
        print("{:s} created ({:.1f}MB)!".format(full_output_filename, getsize(full_output_filename) / 1000000.))
    if USE_RL:
        c.save()
        print("{:s} created ({:.1f}MB)!".format(full_output_filename_reportlab, getsize(full_output_filename_reportlab) / 1000000.))


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
