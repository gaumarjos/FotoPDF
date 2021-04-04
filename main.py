# Copyright Stefano Salati 2021
# Untested, have fun!

# Docs
# https://www.reportlab.com/docs/reportlab-userguide.pdf
# https://python-utilities.readthedocs.io/en/latest/dll.html
# https://www.techwithtim.net/tutorials/pyqt5-tutorial/basic-gui-application/
# https://www.reddit.com/r/learnpython/comments/97z5dq/pyqt5_drag_and_drop_file_option/

from os import listdir
from os.path import join, getsize, isfile, dirname, abspath, isdir
from fpdf import FPDF
import PIL.Image
import exifread
# import sys
# from pdfrw import PageMerge, PdfReader, PdfWriter
import re
# import getopt
import sys
import json
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph  # , Image, Flowable
from reportlab.lib.styles import getSampleStyleSheet  # , ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
import reportlab.rl_config
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit # QLabel, QMessageBox, QLineEdit
#from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

reportlab.rl_config.warnOnMissingFontGlyphs = 0

# Constants
GUI = True
USE_FPDF = False
USE_RL = True


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    return [atoi(c) for c in re.split(r'(\d+)', text)]


def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def fpdf_centeredtext(p, text, font, size, y, black=True):
    p.set_y(y)
    p.set_font(font, '', size)
    if black:
        p.set_text_color(0, 0, 0)
    else:
        p.set_text_color(255, 255, 255)
    p.cell(0, 0, text, 0, 1, align="C", fill=False)
    p.set_text_color(0, 0, 0)


def rl_singlelinecenteredtext(c, text, font, size, page_height, page_width, y, black=True):
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


def rl_text(c, text, font, alignment, size, interline, from_side, from_top, page_width, page_height, black=True):
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
        p.drawOn(c, from_side, (page_height - from_top - h) if (from_top > 0) else ((page_height - h) / 2.))
    else:
        print("Error: text cell too small for text.")


def rl_centeredimage(c, image, from_side, from_top, page_width, page_height):
    # Read ImageDescription field from JPG. Exifread is the only library that works.
    # Exif doesn't have this tag and Pillow corrupts the accented characters.
    tags = exifread.process_file(open(image, 'rb'))
    caption = str(tags['Image ImageDescription'])

    pil_image = PIL.Image.open(image)
    original_image_size = pil_image.size
    wanted_width = page_width - from_side * 2
    ratio = wanted_width / original_image_size[0]
    wanted_height = original_image_size[1] * ratio
    c.drawImage(image,
                x=from_side,
                y=page_height - from_top - wanted_height,
                width=wanted_width,
                height=wanted_height,
                mask=None)
    # Alternative solution (to be used only if used also in the grid,
    # otherwise the images are not recognised as the same and saved twice in the file.
    # im = Image(image, width=wanted_width, height=wanted_height)
    # im.hAlign = 'CENTER'
    # im.drawOn(c, from_side, page_height - from_side - wanted_height)
    return (from_top + wanted_height), caption


def create_pdf(input_folder, widget=None):
    # If used as command line (GUI = False), the input folder is sys.argv[1]
    if widget is None:
        input_folder = str(input_folder[0])

    # If it's a file instead of a folder, just take the folder containing the file
    if isfile(input_folder):
        input_folder = dirname(abspath(input_folder))

    # Lettura JSON
    with open(join(input_folder, 'settings.json'), 'r') as myjson:
        data = myjson.read()
    obj = json.loads(data)

    # Creazione file e impostazioni generali
    if obj["document"]["a4"]:
        W, H = landscape(A4)
    else:
        H = obj["document"]["height"]
        W = obj["document"]["width"]
    if widget is None:
        print("Slide format: {:f}x{:f}pt.".format(H, W))
    else:
        widget.append("Slide format: {:f}x{:f}pt.".format(H, W))


    output_filename = clean_html(obj['document']['title']) + ', ' + clean_html(obj['document']['author'])
    if len(obj['document']['suffix']) > 0:
        output_filename = output_filename + ', ' + clean_html(obj['document']['suffix']) + ".pdf"
    abs_output_filename = join(input_folder, output_filename)

    if USE_FPDF:
        # Constructor
        if widget is None:
            print("Generating PDF with FPDF...")
        else:
            widget.append("Generating PDF with FPDF...")
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
        if widget is None:
            print("Generating PDF with Reportlab...")
        else:
            widget.append("Generating PDF with Reportlab...")
        c = canvas.Canvas(abs_output_filename, enforceColorSpace='RGB')
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
            if obj["cover"]["use_image"] >= 0:
                pdf.image(join(input_folder, images[obj["cover"]["use_image"] - 1]), x=-10, y=0, w=0, h=H, type="JPEG")
            fpdf_centeredtext(pdf, obj['document']['title'], 'myfont', int(obj['cover']['title']['size']),
                              int(obj['cover']['title']['from_top']), obj["cover"]["title"]["black_text"])
            fpdf_centeredtext(pdf, obj["document"]["author"], 'myfont', int(obj['cover']['author']['size']),
                              int(obj['cover']['author']['from_top']), obj["cover"]["author"]["black_text"])
        if USE_RL:
            original_image_size = PIL.Image.open(join(input_folder, images[obj["cover"]["use_image"] - 1])).size
            c.drawImage(join(input_folder, images[obj["cover"]["use_image"] - 1]), (W - original_image_size[0]) / 2, 0,
                        width=None, height=H, preserveAspectRatio=True)
            rl_text(c, obj['document']['title'], 'font_title', 1, int(obj['cover']['title']['size']),
                    int(obj['cover']['title']['interline']), int(obj['cover']['title']['from_side']),
                    int(obj['cover']['title']['from_top']), W, H,
                    black=obj["cover"]["title"]["black_text"])
            rl_singlelinecenteredtext(c, obj["document"]["author"], 'font_author', int(obj['cover']['author']['size']),
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
            rl_text(c, text, 'font_text', 0, obj['description']['size'],
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
            text_x, caption = rl_centeredimage(c, join(input_folder, image),
                                               int(obj['photos']['from_side']),
                                               int(obj['photos']['from_top']),
                                               W, H)
            rl_text(c, caption, 'font_text', 0, obj['photos']['size'],
                    obj['photos']['interline'], obj['photos']['from_side'],
                    (text_x + obj['photos']['interline'] / 1.),
                    W, H)
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
        if bool(obj['contactsheet']['black_background']):
            c.setFillColorRGB(0, 0, 0)
            c.rect(0, 0, W, H, fill=1)
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
                fpdf_centeredtext(pdf,
                                  obj['document']['author'],
                                  'font_text',
                                  obj['final']['author']['size'],
                                  obj['final']['author']['from_top'], black=True)
            if USE_RL:
                rl_singlelinecenteredtext(c,
                                          obj['document']['author'],
                                          'font_text',
                                          obj['final']['author']['size'],
                                          H, W,
                                          obj['final']['author']['from_top'],
                                          True)

        if bool(obj['final']['website']['show']):
            if USE_FPDF:
                fpdf_centeredtext(pdf,
                                  obj['final']['website']['string'],
                                  'font_text',
                                  obj['final']['website']['size'],
                                  obj['final']['website']['from_top'], black=True)
            if USE_RL:
                rl_singlelinecenteredtext(c,
                                          obj['final']['website']['string'],
                                          'font_text',
                                          obj['final']['website']['size'],
                                          H, W,
                                          obj['final']['website']['from_top'],
                                          True)

        if bool(obj['final']['email']['show']):
            if USE_FPDF:
                fpdf_centeredtext(pdf,
                                  obj['final']['email']['string'],
                                  'font_text',
                                  obj['final']['email']['size'],
                                  obj['final']['email']['from_top'], black=True)
            if USE_RL:
                rl_singlelinecenteredtext(c,
                                          obj['final']['email']['string'],
                                          'font_text',
                                          obj['final']['email']['size'],
                                          H, W,
                                          obj['final']['email']['from_top'],
                                          True)

        if bool(obj['final']['phone']['show']):
            if USE_FPDF:
                fpdf_centeredtext(pdf,
                                  obj['final']['phone']['string'],
                                  'font_text',
                                  obj['final']['phone']['size'],
                                  obj['final']['phone']['from_top'], black=True)
            if USE_RL:
                rl_singlelinecenteredtext(c,
                                          obj['final']['phone']['string'],
                                          'font_text',
                                          obj['final']['phone']['size'],
                                          H, W,
                                          obj['final']['phone']['from_top'],
                                          True)

        if bool(obj['final']['phone']['show']):
            if USE_FPDF:
                fpdf_centeredtext(pdf,
                                  obj['final']['disclaimer']['string'],
                                  'font_text',
                                  obj['final']['disclaimer']['size'],
                                  obj['final']['disclaimer']['from_top'], black=True)
            if USE_RL:
                rl_singlelinecenteredtext(c,
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
        pdf.output(abs_output_filename, "F")
    if USE_RL:
        c.save()
    if widget is None:
        print("{:s} created ({:.1f}MB)!".format(abs_output_filename, getsize(abs_output_filename) / 1000000.))
    else:
        widget.append("{:s} created ({:.1f}MB)!".format(abs_output_filename, getsize(abs_output_filename) / 1000000.))


class FileEdit(QTextEdit):
    def __init__(self, parent):
        super(FileEdit, self).__init__(parent)
        # Si usa solo nel caso del QLineEdit
        # self.setDragEnabled(True)

    def dragEnterEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            event.acceptProposedAction()

    def dropEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            draggedpath = str(urls[0].path())
            if isfile(draggedpath) or isdir(draggedpath):
                # if filepath[-4:].lower() == ".jpg":
                self.setText(draggedpath)
                create_pdf(draggedpath, self)
            else:
                self.setText("Invalid file or folder.")


def main_gui(argv):
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setGeometry(200, 200, 400, 200)
    win.setWindowTitle("FotoPDF")
    app.setWindowIcon(QIcon('FotoPDF.png'))

    # Create widget to accept drag&drop
    widget = FileEdit(win)
    widget.setReadOnly(True)
    widget.setText("Drag folder or one of the images here")
    widget.setGeometry(0, 0, 400, 200)
    #widget.setAlignment(Qt.AlignHCenter)
    #widget.setAlignment(Qt.AlignVCenter)

    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    if GUI:
        main_gui(sys.argv[1:])
    else:
        create_pdf(sys.argv[1:], None)


# Unused code
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


# For more arguments, now unused
    # try:
    #     opts, args = getopt.getopt(argv, "i:",
    #                                ["input_folder="])
    # except getopt.GetoptError:
    #     print("Error: wrong arguments.")
    #     sys.exit(2)
    # for opt, arg in opts:
    #     if opt in ("-i", "--input_folder"):
    #         input_folder = arg
