# Copyright Stefano Salati 2021

# Docs
# https://www.reportlab.com/docs/reportlab-userguide.pdf
# https://python-utilities.readthedocs.io/en/latest/dll.html
# https://www.techwithtim.net/tutorials/pyqt5-tutorial/basic-gui-application/
# https://www.reddit.com/r/learnpython/comments/97z5dq/pyqt5_drag_and_drop_file_option/
# https://blog.aaronhktan.com/posts/2018/05/14/pyqt5-pyinstaller-executable
# https://github.com/pyinstaller/pyinstaller/issues/5107

import os
from os import listdir
from os.path import join, getsize, isfile, dirname, abspath, isdir
from fpdf import FPDF
import PIL.Image
import exifread
import re
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
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit  # QLabel, QMessageBox, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# import getopt
# from pdfrw import PageMerge, PdfReader, PdfWriter

reportlab.rl_config.warnOnMissingFontGlyphs = 0

# Constants
GUI = True
USE_FPDF = False
USE_RL = True


# Translate asset paths to useable format for PyInstaller
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    return [atoi(c) for c in re.split(r'(\d+)', text)]


def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


class FotoPDF:

    def fpdf_centered_text(self, text, font, size, y, black=True):
        self.pdf.set_y(y)
        self.pdf.set_font(font, '', size)
        if black:
            self.pdf.set_text_color(0, 0, 0)
        else:
            self.pdf.set_text_color(255, 255, 255)
        self.pdf.cell(0, 0, text, 0, 1, align="C", fill=False)
        self.pdf.set_text_color(0, 0, 0)

    def rl_single_line_centered_text(self, text, font, size, y, black=True):
        self.c.setFont(font, size)
        if black:
            self.c.setFillColorRGB(0, 0, 0)
        else:
            self.c.setFillColorRGB(1, 1, 1)
        text_width = self.c.stringWidth(text, font, size)
        self.c.drawString((self.W - text_width) / 2.0, self.H - y, text)
        # Alternative solution
        # t = c.beginText()
        # t.setTextOrigin(int(obj['description']['from_side']*MM2PT), int(H-obj['description']['from_top']*MM2PT))
        # t.setFont('myfont', 16)
        # t.textLine(obj['description']['string'])
        # c.drawText(t)

    def rl_text(self, text, font, alignment, size, interline, from_side, from_top, black=True):
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
        aw = self.W - (from_side * 2)
        ah = self.H - from_top
        w, h = p.wrap(aw, ah)
        if w <= aw and h <= ah:
            p.drawOn(self.c, from_side, (self.H - from_top - h) if (from_top > 0) else ((self.H - h) / 2.))
        else:
            if self.widget is None:
                print("Error: text cell too small for text.")
            else:
                self.widget.append("Error: text cell too small for text.")

    def rl_centered_image(self, image, from_side, from_top):
        # Read ImageDescription field from JPG. Exifread is the only library that works.
        # Exif doesn't have this tag and Pillow corrupts the accented characters.
        tags = exifread.process_file(open(image, 'rb'))
        caption = str(tags['Image ImageDescription'])

        pil_image = PIL.Image.open(image)
        original_image_size = pil_image.size
        wanted_width = self.W - from_side * 2
        ratio = wanted_width / original_image_size[0]
        wanted_height = original_image_size[1] * ratio
        self.c.drawImage(image,
                         x=from_side,
                         y=self.H - from_top - wanted_height,
                         width=wanted_width,
                         height=wanted_height,
                         mask=None)
        # Alternative solution (to be used only if used also in the grid,
        # otherwise the images are not recognised as the same and saved twice in the file.
        # im = Image(image, width=wanted_width, height=wanted_height)
        # im.hAlign = 'CENTER'
        # im.drawOn(c, from_side, page_height - from_side - wanted_height)
        return (from_top + wanted_height), caption

    def __init__(self, input_folder, widget=None):
        self.widget = widget

        # If used as command line (GUI = False), the input folder is sys.argv[1]
        if self.widget is None:
            self.input_folder = str(input_folder[0])
        else:
            self.input_folder = input_folder

        # If it's a file instead of a folder, just take the folder containing the file
        if isfile(self.input_folder):
            self.input_folder = dirname(abspath(self.input_folder))

        # Initialize variables
        self.obj = None
        self.abs_output_filename = None
        self.H = 0
        self.W = 0
        if USE_FPDF:
            self.pdf = None
        if USE_RL:
            self.c = None
        self.images = []

    def inizialize_pdf(self):
        # Lettura JSON
        try:
            with open(join(self.input_folder, 'settings.json'), 'r') as myjson:
                data = myjson.read()
            self.obj = json.loads(data)
        except:
            if self.widget is None:
                print("Cannot find settings.json in folder.")
            else:
                self.widget.setText("Cannot find settings.json in folder.")
            return False

        # Creazione file e impostazioni generali
        if self.obj["document"]["a4"]:
            self.W, self.H = landscape(A4)
        else:
            self.H = self.obj["document"]["height"]
            self.W = self.obj["document"]["width"]
        # if self.widget is None:
        #     print("Slide format: {:f}x{:f}pt.".format(self.H, self.W))
        # else:
        #     self.widget.append("Slide format: {:f}x{:f}pt.".format(self.H, self.W))

        output_filename = clean_html(self.obj['document']['title']) + ', ' + clean_html(self.obj['document']['author'])
        if len(self.obj['document']['suffix']) > 0:
            output_filename = output_filename + ', ' + clean_html(self.obj['document']['suffix']) + ".pdf"
        self.abs_output_filename = join(self.input_folder, output_filename)

        if USE_FPDF:
            # Constructor
            self.pdf = FPDF(orientation='L', unit='pt', format=(self.H, self.W))
            self.pdf.set_compression(True)
            self.pdf.set_margins(0, 0, 0)
            self.pdf.set_auto_page_break(False)
            self.pdf.set_fill_color(255, 255, 255)
            self.pdf.set_text_color(0, 0, 0)
            self.pdf.set_title(self.obj["document"]["title"])
            self.pdf.set_author(self.obj["document"]["author"])

            # Use user-defined True Type Font (TTF)
            self.pdf.add_font('font_title', '', self.obj["fonts"]["title"], uni=True)
            self.pdf.add_font('font_author', '', self.obj["fonts"]["author"], uni=True)
            self.pdf.add_font('font_text', '', self.obj["fonts"]["text"], uni=True)

        if USE_RL:
            # Constructor
            self.c = canvas.Canvas(self.abs_output_filename, enforceColorSpace='RGB')
            self.c.setPageSize((self.W, self.H))
            self.c.setTitle(self.obj["document"]["title"])
            self.c.setAuthor(self.obj["document"]["author"])

            # Use user-defined True Type Font (TTF)
            pdfmetrics.registerFont(TTFont('font_title', self.obj["fonts"]["title"]))
            pdfmetrics.registerFont(TTFont('font_author', self.obj["fonts"]["author"]))
            pdfmetrics.registerFont(TTFont('font_text', self.obj["fonts"]["text"]))
            self.c.setFont('font_text', 16)

        # Ricerca immagini
        self.images = [f for f in listdir(self.input_folder) if f.endswith(".jpg")]
        self.images.sort(key=natural_keys)
        if len(self.images) == 0:
            if self.widget is None:
                print("No image found in folder.")
            else:
                self.widget.setText("No image found in folder.")
            return False

        if self.widget is None:
            print("Creating PDF with images in {}".format(self.input_folder))
        else:
            self.widget.setText("Creating PDF with images in {}".format(self.input_folder))

        return True

    def cover_page(self):
        if USE_FPDF:
            self.pdf.add_page()
            if self.obj["cover"]["use_image"] >= 0:
                self.pdf.image(join(self.input_folder, self.images[self.obj["cover"]["use_image"] - 1]), x=-10, y=0,
                               w=0,
                               h=self.H,
                               type="JPEG")
            self.fpdf_centered_text(self.obj['document']['title'], 'myfont',
                                    int(self.obj['cover']['title']['size']),
                                    int(self.obj['cover']['title']['from_top']),
                                    self.obj["cover"]["title"]["black_text"])
            self.fpdf_centered_text(self.obj["document"]["author"], 'myfont',
                                    int(self.obj['cover']['author']['size']),
                                    int(self.obj['cover']['author']['from_top']),
                                    self.obj["cover"]["author"]["black_text"])
        if USE_RL:
            original_image_size = PIL.Image.open(
                join(self.input_folder, self.images[self.obj["cover"]["use_image"] - 1])).size
            self.c.drawImage(join(self.input_folder, self.images[self.obj["cover"]["use_image"] - 1]),
                             (self.W - original_image_size[0]) / 2,
                             0,
                             width=None, height=self.H, preserveAspectRatio=True)
            self.rl_text(self.obj['document']['title'], 'font_title', 1, int(self.obj['cover']['title']['size']),
                         int(self.obj['cover']['title']['interline']), int(self.obj['cover']['title']['from_side']),
                         int(self.obj['cover']['title']['from_top']),
                         black=self.obj["cover"]["title"]["black_text"])
            self.rl_single_line_centered_text(self.obj["document"]["author"], 'font_author',
                                              int(self.obj['cover']['author']['size']),
                                              int(self.obj['cover']['author']['from_top']),
                                              self.obj["cover"]["author"]["black_text"])
            self.c.showPage()

    def description_page(self):
        if USE_FPDF:
            self.pdf.add_page()
            self.pdf.set_y(int(self.obj['description']['from_top']))
            self.pdf.set_x(int(self.obj['description']['from_side']))
            self.pdf.set_font_size(int(self.obj['description']['size']))
            self.pdf.multi_cell(w=self.W - int(self.obj['description']['from_side']) * 2,
                                h=int(self.obj['description']['interline']),
                                txt=self.obj['description']['string'], border=0, align="L", fill=False)

        if USE_RL:
            text = self.obj['description']['string']
            text = text.replace("\n", "<br/>")
            self.rl_text(text, 'font_text', 0, self.obj['description']['size'],
                         self.obj['description']['interline'], self.obj['description']['from_side'],
                         self.obj['description']['from_top'])
            self.c.showPage()

    def image_pages(self):
        if USE_FPDF:
            self.pdf.set_font_size(int(self.obj['photos']['size']))
            for i, image in enumerate(self.images):
                self.pdf.add_page()
                self.pdf.image(join(self.input_folder, image), x=12, y=10, w=self.W - 24, h=0, type="JPEG")
                self.pdf.set_y(self.H - 16)
                self.pdf.set_x(int(self.obj['photos']['from_side']))
                self.pdf.multi_cell(w=self.W - int(self.obj['photos']['from_side']) * 2,
                                    h=int(self.obj['photos']['interline']),
                                    txt=str(self.obj['photos']['captions'][i]['caption']), border=0, align="L",
                                    fill=False)

        if USE_RL:
            for i, image in enumerate(self.images):
                text_x, caption = self.rl_centered_image(join(self.input_folder, image),
                                                         int(self.obj['photos']['from_side']),
                                                         int(self.obj['photos']['from_top']))
                self.rl_text(caption, 'font_text', 0, self.obj['photos']['size'],
                             self.obj['photos']['interline'], self.obj['photos']['from_side'],
                             (text_x + self.obj['photos']['interline'] / 1.))
                self.c.showPage()

    def grid_page(self):
        r = int(self.obj['contactsheet']['rows'])
        c = int(self.obj['contactsheet']['columns'])
        m_oriz = self.obj["contactsheet"]["horizontal_margin"]
        m_vert = self.obj["contactsheet"]["vertical_margin"]
        m_lat = self.obj["contactsheet"]["lateral_margin"]

        # Parto dalle colonne e vedo se l'altezza sta nei margini
        w = (self.W - 2 * m_lat - (c - 1) * m_oriz) / c
        h = w / 3. * 2.
        total_h = r * h + (r - 1) * m_vert + m_lat
        # E' troppo alta, devo ripartire dalle righe e calcolare le colonne di conseguenza
        if total_h > self.H:
            h = (self.H - 2 * m_lat - (r - 1) * m_vert) / r
            w = h * 3. / 2.
            total_w = c * w + (c - 1) * m_oriz + m_lat
            if total_w > self.W:
                print("Non può essere.")

        if USE_FPDF:
            self.pdf.add_page()
            if bool(self.obj['contactsheet']['black_background']):
                self.pdf.set_fill_color(0, 0, 0)
                self.pdf.cell(0, self.H, "", 0, 1, align="C", fill=True)
            for i, image in enumerate(self.images):
                self.pdf.image(join(self.input_folder, image),
                               x=(self.W - (c * w + (c - 1) * m_oriz)) / 2 + (i % c) * (w + m_oriz),
                               y=(self.H - (r * h + (r - 1) * m_vert)) / 2 + int(i / c) * (h + m_vert),
                               w=w, h=0)
        if USE_RL:
            if bool(self.obj['contactsheet']['black_background']):
                self.c.setFillColorRGB(0, 0, 0)
                self.c.rect(0, 0, self.W, self.H, fill=1)
            for i, image in enumerate(self.images):
                self.c.drawImage(join(self.input_folder, image),
                                 x=(self.W - (c * w + (c - 1) * m_oriz)) / 2 + (i % c) * (w + m_oriz),
                                 y=self.H - h - ((self.H - (r * h + (r - 1) * m_vert)) / 2 + int(i / c) * (h + m_vert)),
                                 width=w,
                                 height=h,
                                 mask=None)
            self.c.showPage()

    def final_page(self):
        if USE_FPDF:
            self.pdf.add_page()

        if bool(self.obj['final']['author']['show']):
            if USE_FPDF:
                self.fpdf_centered_text(self.obj['document']['author'],
                                        'font_text',
                                        self.obj['final']['author']['size'],
                                        self.obj['final']['author']['from_top'], black=True)
            if USE_RL:
                self.rl_single_line_centered_text(self.obj['document']['author'],
                                                  'font_text',
                                                  self.obj['final']['author']['size'],
                                                  self.obj['final']['author']['from_top'],
                                                  True)

        if bool(self.obj['final']['website']['show']):
            if USE_FPDF:
                self.fpdf_centered_text(self.obj['final']['website']['string'],
                                        'font_text',
                                        self.obj['final']['website']['size'],
                                        self.obj['final']['website']['from_top'], black=True)
            if USE_RL:
                self.rl_single_line_centered_text(self.obj['final']['website']['string'],
                                                  'font_text',
                                                  self.obj['final']['website']['size'],
                                                  self.obj['final']['website']['from_top'],
                                                  True)

        if bool(self.obj['final']['email']['show']):
            if USE_FPDF:
                self.fpdf_centered_text(self.obj['final']['email']['string'],
                                        'font_text',
                                        self.obj['final']['email']['size'],
                                        self.obj['final']['email']['from_top'], black=True)
            if USE_RL:
                self.rl_single_line_centered_text(self.obj['final']['email']['string'],
                                                  'font_text',
                                                  self.obj['final']['email']['size'],
                                                  self.obj['final']['email']['from_top'],
                                                  True)

        if bool(self.obj['final']['phone']['show']):
            if USE_FPDF:
                self.fpdf_centered_text(self.obj['final']['phone']['string'],
                                        'font_text',
                                        self.obj['final']['phone']['size'],
                                        self.obj['final']['phone']['from_top'], black=True)
            if USE_RL:
                self.rl_single_line_centered_text(self.obj['final']['phone']['string'],
                                                  'font_text',
                                                  self.obj['final']['phone']['size'],
                                                  self.obj['final']['phone']['from_top'],
                                                  True)

        if bool(self.obj['final']['disclaimer']['show']):
            if USE_FPDF:
                self.fpdf_centered_text(self.obj['final']['disclaimer']['string'],
                                        'font_text',
                                        self.obj['final']['disclaimer']['size'],
                                        self.obj['final']['disclaimer']['from_top'], black=True)
            if USE_RL:
                self.rl_single_line_centered_text(self.obj['final']['disclaimer']['string'],
                                                  'font_text',
                                                  self.obj['final']['disclaimer']['size'],
                                                  self.obj['final']['disclaimer']['from_top'],
                                                  True)

        if USE_RL:
            self.c.showPage()

    def save_pdf(self):
        # Salva
        if USE_FPDF:
            self.pdf.output(self.abs_output_filename, "F")
        if USE_RL:
            self.c.save()
        if self.widget is None:
            print("PDF created ({:.1f}MB), check in your folder!".format(getsize(self.abs_output_filename) / 1000000.))
            print("Drag another folder or file to create a new one.")
        else:
            self.widget.append(
                "PDF created ({:.1f}MB), check in your folder!".format(getsize(self.abs_output_filename) / 1000000.))
            self.widget.append("Drag another folder or file to create a new one.")

    def create_pdf(self):
        if self.inizialize_pdf():
            if bool(self.obj['cover']['show']):
                self.cover_page()
            if bool(self.obj['description']['show']):
                self.description_page()
            self.image_pages()
            self.grid_page()
            if self.obj['final']['show']:
                self.final_page()
            self.save_pdf()


class FileEdit(QTextEdit):
    def __init__(self, parent):
        super(FileEdit, self).__init__(parent)
        # Si usa solo nel caso del QLineEdit
        # self.setDragEnabled(True)
        self.setText("Drag a folder with images (or one of the images) and a settings.json to create a pdf.")

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
                pdf = FotoPDF(draggedpath, self)
                pdf.create_pdf()
            else:
                self.setText("Invalid file or folder.")


def main_gui():
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setGeometry(200, 200, 400, 200)
    win.setFixedSize(400, 200)
    win.setWindowTitle("FotoPDF")
    app.setWindowIcon(QIcon('FotoPDF.png'))

    # Create widget to accept drag&drop
    widget = FileEdit(win)
    widget.setReadOnly(True)
    widget.setText("Drag folder or one of the images here")
    widget.setGeometry(0, 0, 400, 200)
    # widget.setStyleSheet("background-image: url(drophere.png);")
    # widget.setAlignment(Qt.AlignHCenter)
    # widget.setAlignment(Qt.AlignVCenter)

    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    if GUI:
        main_gui()
    else:
        mypdf = FotoPDF(sys.argv[1:], None)
        mypdf.create_pdf()

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
