# Copyright Stefano Salati 2021

# Docs
# https://www.reportlab.com/docs/reportlab-userguide.pdf
# https://python-utilities.readthedocs.io/en/latest/dll.html
# https://www.techwithtim.net/tutorials/pyqt5-tutorial/basic-gui-application/
# https://www.reddit.com/r/learnpython/comments/97z5dq/pyqt5_drag_and_drop_file_option/
# https://blog.aaronhktan.com/posts/2018/05/14/pyqt5-pyinstaller-executable
# https://github.com/pyinstaller/pyinstaller/issues/5107
# http://www.marinamele.com/from-a-python-script-to-a-portable-mac-application-with-py2app
# https://py2app.readthedocs.io/_/downloads/en/stable/pdf/


import os
import shutil
from os import listdir
from os.path import join, getsize, isfile, dirname, abspath, isdir
# from fpdf import FPDF
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
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QLineEdit  # QLabel, QMessageBox, QLineEdit
from PyQt5.QtGui import QIcon, QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt5.QtCore import Qt
from pikepdf import Pdf, Page, PdfImage, Name, Dictionary, Stream

# import PyPDF2
# from pathlib import Path

# from pdfrw import PdfReader, PdfWriter

os.environ['QT_MAC_WANTS_LAYER'] = '1'
os.environ['QT_DEBUG_PLUGINS'] = '1'
reportlab.rl_config.warnOnMissingFontGlyphs = 0

# Constants
DEBUG = True
GUI = True
# USE_FPDF = False
# USE_RL = True
MACOSRED = (236, 95, 93)
MACOSORANGE = (232, 135, 58)
MACOSYELLOW = (255, 200, 60)
MACOSGREEN = (120, 183, 86)
MACOSCYAN = (84, 153, 166)
MACOSBLUE = (48, 123, 246)
MACOSMAGENTA = (154, 86, 163)
MACOSDARK = (46, 46, 46)


# Translate asset paths to useable format for PyInstaller
# def resource_path(relative_path):
#     if hasattr(sys, '_MEIPASS'):
#         return os.path.join(sys._MEIPASS, relative_path)
#     return os.path.join(os.path.abspath('.'), relative_path)


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    return [atoi(c) for c in re.split(r'(\d+)', text)]


def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


class FotoPDF:

    def __init__(self, input_folder, header_widget=None, detail_widget=None):
        self.header_widget = header_widget
        self.detail_widget = detail_widget

        # If used as command line (GUI = False), the input folder is sys.argv[1]
        if self.header_widget is None:
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
        # if USE_FPDF:
        #     self.pdf = None
        self.c = None
        self.images = []

    def message_on_header_widget(self, text):
        if self.header_widget is None:
            print(text)
        else:
            self.header_widget.setText(text)

    def message_on_detail_widget(self, text, append=True):
        if self.detail_widget is None:
            print(text)
        else:
            if append:
                self.detail_widget.append(text)
            else:
                self.detail_widget.setText(text)

    @staticmethod
    def fit_image(rect_x, rect_y, rect_w, rect_h, image_w, image_h):
        # Determine whether the limiting factor will be the width or the height
        w_ratio = rect_w / image_w
        if w_ratio * image_h <= rect_h:
            # The width is the limiting factor
            scaled_image_w = rect_w
            scaled_image_h = image_h * w_ratio
            scaled_image_x = (rect_w - scaled_image_w) / 2. + rect_x
            scaled_image_y = (rect_h - scaled_image_h) / 2. + rect_y
        else:
            # The height is the limiting factor
            h_ratio = rect_h / image_h
            scaled_image_w = image_w * h_ratio
            scaled_image_h = rect_h
            scaled_image_x = (rect_w - scaled_image_w) / 2. + rect_x
            scaled_image_y = (rect_h - scaled_image_h) / 2. + rect_y
        return scaled_image_x, scaled_image_y, scaled_image_w, scaled_image_h

    # def fpdf_centered_text(self, text, font, size, y, black=True):
    #     self.pdf.set_y(y)
    #     self.pdf.set_font(font, '', size)
    #     if black:
    #         self.pdf.set_text_color(0, 0, 0)
    #     else:
    #         self.pdf.set_text_color(255, 255, 255)
    #     self.pdf.cell(0, 0, text, 0, 1, align="C", fill=False)
    #     self.pdf.set_text_color(0, 0, 0)

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
            self.message_on_detail_widget("Warning: text cell too small for text.")

    def rl_centered_image(self, image, from_side, from_top):
        # Read ImageDescription field from JPG. Exifread is the only library that works.
        # Exif doesn't have this tag and Pillow corrupts the accented characters.
        tags = exifread.process_file(open(image, 'rb'))
        try:
            caption = str(tags['Image ImageDescription'])
        except:
            caption = ""
            self.message_on_detail_widget("Warning: \"{}\" does not have a caption.".format(os.path.basename(image)))

        original_image_size = PIL.Image.open(image).size
        scaled_image_x, scaled_image_y, scaled_image_w, scaled_image_h = self.fit_image(from_side,
                                                                                        50,
                                                                                        self.W - from_side * 2,
                                                                                        self.H - from_top - 50,
                                                                                        original_image_size[0],
                                                                                        original_image_size[1])
        self.c.drawImage(image,
                         x=scaled_image_x,
                         y=scaled_image_y,
                         width=scaled_image_w,
                         height=scaled_image_h,
                         mask=None)
        return (from_top + scaled_image_h), caption

    def inizialize_pdf(self):
        # In any case, write to drag folder here
        self.message_on_header_widget("Drag folder here")
        self.message_on_detail_widget("", append=False)

        # Lettura JSON
        try:
            with open(join(self.input_folder, 'settings.json'), 'r', encoding="utf8") as myjson:
                data = myjson.read()
        except:
            self.message_on_detail_widget(
                "Warning: Cannot find settings.json in folder. Creating a default one that will need to be customized.")
            shutil.copyfile('settings.json', join(self.input_folder, 'settings.json'))
            with open(join(self.input_folder, 'settings.json'), 'r', encoding="utf8") as myjson:
                data = myjson.read()
        self.obj = json.loads(data)

        # Creazione file e impostazioni generali
        if self.obj["document"]["a4"]:
            self.W, self.H = landscape(A4)
        else:
            self.H = self.obj["document"]["height"]
            self.W = self.obj["document"]["width"]

        output_filename = clean_html(self.obj['document']['title']) + ', ' + clean_html(self.obj['document']['author'])
        if len(self.obj['document']['suffix']) > 0:
            output_filename = output_filename + ', ' + clean_html(self.obj['document']['suffix']) + ".pdf"
        self.abs_output_filename = join(self.input_folder, output_filename)

        # if USE_FPDF:
        #     # Constructor
        #     self.pdf = FPDF(orientation='L', unit='pt', format=(self.H, self.W))
        #     self.pdf.set_compression(True)
        #     self.pdf.set_margins(0, 0, 0)
        #     self.pdf.set_auto_page_break(False)
        #     self.pdf.set_fill_color(255, 255, 255)
        #     self.pdf.set_text_color(0, 0, 0)
        #     self.pdf.set_title(self.obj["document"]["title"])
        #     self.pdf.set_author(self.obj["document"]["author"])
        #
        #     # Use user-defined True Type Font (TTF)
        #     self.pdf.add_font('font_title', '', self.obj["fonts"]["title"], uni=True)
        #     self.pdf.add_font('font_author', '', self.obj["fonts"]["author"], uni=True)
        #     self.pdf.add_font('font_text', '', self.obj["fonts"]["text"], uni=True)

        # Constructor
        self.c = canvas.Canvas(self.abs_output_filename, enforceColorSpace='RGB')
        self.c.setPageSize((self.W, self.H))
        self.c.setTitle(self.obj["document"]["title"])
        self.c.setAuthor(self.obj["document"]["author"])

        # Use user-defined True Type Font (TTF)
        try:
            pdfmetrics.registerFont(TTFont('font_title', self.obj["fonts"]["title"]))
        except:
            self.message_on_detail_widget(
                "Error: Cannot find font_title, looking in {}".format(self.obj["fonts"]["title"]))
            return False

        try:
            pdfmetrics.registerFont(TTFont('font_author', self.obj["fonts"]["author"]))
        except:
            self.message_on_detail_widget("Error: Cannot find font_author, looking in {}".format(
                self.obj["fonts"]["author"]))
            return False

        try:
            pdfmetrics.registerFont(TTFont('font_text', self.obj["fonts"]["text"]))
        except:
            self.message_on_detail_widget("Error: Cannot find font_text, looking in {}".format(
                self.obj["fonts"]["text"]))
            return False

        self.c.setFont('font_text', 16)

        # Ricerca immagini
        self.images = [f for f in listdir(self.input_folder) if f.endswith(".jpg")]
        self.images.sort(key=natural_keys)
        if len(self.images) == 0:
            self.message_on_detail_widget("Error: No image found in folder.", append=False)
            return False
        self.message_on_detail_widget("Creating PDF with images in \"{}\".".format(self.input_folder))

        return True

    def cover_page(self):
        # if USE_FPDF:
        #     self.pdf.add_page()
        #     if self.obj["cover"]["use_image"] >= 0:
        #         self.pdf.image(join(self.input_folder, self.images[self.obj["cover"]["use_image"] - 1]), x=-10, y=0,
        #                        w=0,
        #                        h=self.H,
        #                        type="JPEG")
        #     self.fpdf_centered_text(self.obj['document']['title'], 'myfont',
        #                             int(self.obj['cover']['title']['size']),
        #                             int(self.obj['cover']['title']['from_top']),
        #                             self.obj["cover"]["title"]["black_text"])
        #     self.fpdf_centered_text(self.obj["document"]["author"], 'myfont',
        #                             int(self.obj['cover']['author']['size']),
        #                             int(self.obj['cover']['author']['from_top']),
        #                             self.obj["cover"]["author"]["black_text"])

        original_image_size = PIL.Image.open(
            join(self.input_folder, self.images[self.obj["cover"]["use_image"] - 1])).size
        self.c.drawImage(join(self.input_folder, self.images[self.obj["cover"]["use_image"] - 1]),
                         (self.W - original_image_size[0]) / 2,
                         0,
                         width=None, height=self.H, preserveAspectRatio=True)
        self.rl_text(self.obj['document']['title'],
                     'font_title',
                     1,
                     int(self.obj['cover']['title']['size']),
                     int(self.obj['cover']['title']['interline']),
                     int(self.obj['cover']['title']['from_side']),
                     int(self.obj['cover']['title']['from_top']),
                     black=self.obj["cover"]["title"]["black_text"])
        self.rl_single_line_centered_text(self.obj["document"]["author"],
                                          'font_author',
                                          int(self.obj['cover']['author']['size']),
                                          int(self.obj['cover']['author']['from_top']),
                                          self.obj["cover"]["author"]["black_text"])
        self.c.showPage()

    def description_page(self):
        # if USE_FPDF:
        #     self.pdf.add_page()
        #     self.pdf.set_y(int(self.obj['description']['from_top']))
        #     self.pdf.set_x(int(self.obj['description']['from_side']))
        #     self.pdf.set_font_size(int(self.obj['description']['size']))
        #     self.pdf.multi_cell(w=self.W - int(self.obj['description']['from_side']) * 2,
        #                         h=int(self.obj['description']['interline']),
        #                         txt=self.obj['description']['string'], border=0, align="L", fill=False)

        text = self.obj['description']['string']
        text = text.replace("\n", "<br/>")
        self.rl_text(text, 'font_text', 0, self.obj['description']['size'],
                     self.obj['description']['interline'], self.obj['description']['from_side'],
                     self.obj['description']['from_top'])
        self.c.showPage()

    def image_pages(self):
        # if USE_FPDF:
        #     self.pdf.set_font_size(int(self.obj['photos']['size']))
        #     for i, image in enumerate(self.images):
        #         self.pdf.add_page()
        #
        #         original_image_size = PIL.Image.open(image).size
        #         scaled_image_x, scaled_image_y, scaled_image_w, scaled_image_h = self.fit_image(12, 10,
        #                                                                                         self.W - 24,
        #                                                                                         self.H - 30,
        #                                                                                         original_image_size[0],
        #                                                                                         original_image_size[1])
        #         self.pdf.image(join(self.input_folder, image), x=scaled_image_x, y=scaled_image_y, w=scaled_image_w,
        #                        h=scaled_image_h, type="JPEG")
        #
        #         # self.pdf.image(join(self.input_folder, image), x=12, y=10, w=self.W - 24, h=0, type="JPEG")
        #         self.pdf.set_y(self.H - 16)
        #         self.pdf.set_x(int(self.obj['photos']['from_side']))
        #         self.pdf.multi_cell(w=self.W - int(self.obj['photos']['from_side']) * 2,
        #                             h=int(self.obj['photos']['interline']),
        #                             txt=str(self.obj['photos']['captions'][i]['caption']), border=0, align="L",
        #                             fill=False)

        for i, image in enumerate(self.images):
            text_x, caption = self.rl_centered_image(join(self.input_folder, image),
                                                     int(self.obj['photos']['from_side']),
                                                     int(self.obj['photos']['from_top']))
            self.rl_text(caption, 'font_text', 0, self.obj['photos']['size'],
                         self.obj['photos']['interline'], self.obj['photos']['from_side'],
                         (text_x + self.obj['photos']['interline'] / 1.))
            self.c.showPage()

    def grid_page(self):
        r = int(self.obj['grid']['rows'])
        c = int(self.obj['grid']['columns'])
        m_oriz = self.obj["grid"]["horizontal_margin"]
        m_vert = self.obj["grid"]["vertical_margin"]
        m_lat = self.obj["grid"]["lateral_margin"]
        image_ratio = self.obj["grid"]["image_ratio"]

        # Parto dalle colonne e vedo se l'altezza sta nei margini
        rect_w = (self.W - 2 * m_lat - (c - 1) * m_oriz) / c
        rect_h = rect_w / image_ratio
        total_h = r * rect_h + (r - 1) * m_vert + m_lat
        # E' troppo alta, devo ripartire dalle righe e calcolare le colonne di conseguenza
        if total_h > self.H:
            rect_h = (self.H - 2 * m_lat - (r - 1) * m_vert) / r
            rect_w = rect_h * image_ratio
            total_w = c * rect_w + (c - 1) * m_oriz + m_lat
            if total_w > self.W:
                print("Non può essere.")

        # if USE_FPDF:
        #     self.pdf.add_page()
        #     if bool(self.obj['grid']['black_background']):
        #         self.pdf.set_fill_color(0, 0, 0)
        #         self.pdf.cell(0, self.H, "", 0, 1, align="C", fill=True)
        #     for i, image in enumerate(self.images):
        #         self.pdf.image(join(self.input_folder, image),
        #                        x=(self.W - (c * w + (c - 1) * m_oriz)) / 2 + (i % c) * (w + m_oriz),
        #                        y=(self.H - (r * h + (r - 1) * m_vert)) / 2 + int(i / c) * (h + m_vert),
        #                        w=w, h=0)

        if bool(self.obj['grid']['black_background']):
            self.c.setFillColorRGB(0, 0, 0)
            self.c.rect(0, 0, self.W, self.H, fill=1)

        for i, image in enumerate(self.images):
            original_image_size = PIL.Image.open(join(self.input_folder, image)).size
            rect_x = (self.W - (c * rect_w + (c - 1) * m_oriz)) / 2 + (i % c) * (rect_w + m_oriz)
            rect_y = self.H - rect_h - ((self.H - (r * rect_h + (r - 1) * m_vert)) / 2 + int(i / c) * (rect_h + m_vert))
            scaled_image_x, scaled_image_y, scaled_image_w, scaled_image_h = self.fit_image(rect_x, rect_y,
                                                                                            rect_w, rect_h,
                                                                                            original_image_size[0],
                                                                                            original_image_size[1])
            self.c.drawImage(join(self.input_folder, image),
                             x=scaled_image_x,
                             y=scaled_image_y,
                             width=scaled_image_w,
                             height=scaled_image_h,
                             mask=None)
            # self.c.drawImage(join(self.input_folder, image),
            #                  x=(self.W - (c * w + (c - 1) * m_oriz)) / 2 + (i % c) * (w + m_oriz),
            #                  y=self.H - h - ((self.H - (r * h + (r - 1) * m_vert)) / 2 + int(i / c) * (h + m_vert)),
            #                  width=w,
            #                  height=h,
            #                  mask=None)
        self.c.showPage()

    def final_page(self):
        # if USE_FPDF:
        #     self.pdf.add_page()

        if bool(self.obj['final']['author']['show']):
            # if USE_FPDF:
            #     self.fpdf_centered_text(self.obj['document']['author'],
            #                             'font_text',
            #                             self.obj['final']['author']['size'],
            #                             self.obj['final']['author']['from_top'], black=True)
            self.rl_single_line_centered_text(self.obj['document']['author'],
                                              'font_text',
                                              self.obj['final']['author']['size'],
                                              self.obj['final']['author']['from_top'],
                                              True)

        if bool(self.obj['final']['website']['show']):
            # if USE_FPDF:
            #     self.fpdf_centered_text(self.obj['final']['website']['string'],
            #                             'font_text',
            #                             self.obj['final']['website']['size'],
            #                             self.obj['final']['website']['from_top'], black=True)
            self.rl_single_line_centered_text(self.obj['document']['website'],
                                              'font_text',
                                              self.obj['final']['website']['size'],
                                              self.obj['final']['website']['from_top'],
                                              True)

        if bool(self.obj['final']['email']['show']):
            # if USE_FPDF:
            #     self.fpdf_centered_text(self.obj['final']['email']['string'],
            #                             'font_text',
            #                             self.obj['final']['email']['size'],
            #                             self.obj['final']['email']['from_top'], black=True)
            self.rl_single_line_centered_text(self.obj['document']['email'],
                                              'font_text',
                                              self.obj['final']['email']['size'],
                                              self.obj['final']['email']['from_top'],
                                              True)

        if bool(self.obj['final']['phone']['show']):
            # if USE_FPDF:
            #     self.fpdf_centered_text(self.obj['final']['phone']['string'],
            #                             'font_text',
            #                             self.obj['final']['phone']['size'],
            #                             self.obj['final']['phone']['from_top'], black=True)
            self.rl_single_line_centered_text(self.obj['document']['phone'],
                                              'font_text',
                                              self.obj['final']['phone']['size'],
                                              self.obj['final']['phone']['from_top'],
                                              True)

        if bool(self.obj['final']['disclaimer']['show']):
            # if USE_FPDF:
            #     self.fpdf_centered_text(self.obj['final']['disclaimer']['string'],
            #                             'font_text',
            #                             self.obj['final']['disclaimer']['size'],
            #                             self.obj['final']['disclaimer']['from_top'], black=True)
            self.rl_single_line_centered_text(self.obj['document']['disclaimer'],
                                              'font_text',
                                              self.obj['final']['disclaimer']['size'],
                                              self.obj['final']['disclaimer']['from_top'],
                                              True)

        self.c.showPage()

    def save_pdf(self):
        # Salva
        # if USE_FPDF:
        #     self.pdf.output(self.abs_output_filename, "F")
        self.c.save()
        self.message_on_header_widget("Created ({:.1f}MB)!".format(
            getsize(self.abs_output_filename) / 1000000.))
        self.message_on_detail_widget("Drag another folder to create a new one.")

    def read_metadata(self):
        x = PyPDF2.PdfFileReader(self.abs_output_filename)
        info = x.getDocumentInfo()
        print(info)

    def resave_pdf(self):
        if 0:
            # Useless
            x = PdfReader(self.abs_output_filename)
            y = PdfWriter()
            for page in x.pages:
                y.addpage(page)
            y.write(self.abs_output_filename + '_resaved.pdf')
            print(len(x.pages))

        if 0:
            # Useless
            pdf_reader = PyPDF2.PdfFileReader(open(self.abs_output_filename, 'rb'))
            pdf_writer = PyPDF2.PdfFileWriter()
            for n in range(pdf_reader.numPages):
                page = pdf_reader.getPage(n)
                page.compressContentStreams()
                pdf_writer.addPage(page)
            with Path(self.abs_output_filename + '_resaved2.pdf').open(mode="wb") as output_file:
                pdf_writer.write(output_file)

        if 0:
            src = Pdf.open(self.abs_output_filename)

            pageobj = src.pages[2]
            s = Stream(Alternate=Name("/DeviceRGB"),
                       Filter=Name("/FlateDecode"),
                       Length=2612,
                       N=3)
            pageobj['/Resources']['/ColorSpace'] = Dictionary({'/Cs1': ["/ICCBased", s]})

            # l = list(src.pages[2].images.keys())
            # pdfimage = PdfImage(src.pages[2].images[l[0]])
            # print(pdfimage.colorspace)
            # rawimage = pdfimage.obj
            # pillowimage = pdfimage.as_pil_image()
            # pdfimage.extract_to(fileprefix='__cacca')
            # grayscale = pillowimage.convert('L')
            # grayscale = grayscale.resize((32, 32))
            # rawimage.write(zlib.compress(grayscale.tobytes()), filter = )
            # rawimage.ColorSpace = Name("/DeviceRGB")
            # rawimage.Filter = Name("/FlateDecode")

            # print(str(pageobj1))

            dst = Pdf.new()
            dst.pages.extend(src.pages)
            dst.save(self.abs_output_filename + '_resaved.pdf',
                     normalize_content=True,
                     linearize=False)

            # Da reportlab
            # "/XObject": {
            #     "/FormXob.8125de7e43ed46d9023f94eb7297f833": pikepdf.Stream(stream_dict={
            #         "/BitsPerComponent": 8,
            #         "/ColorSpace": "/DeviceRGB",
            #         "/Filter": ["/ASCII85Decode", "/DCTDecode"],
            #         "/Height": 1000,
            #         "/Length": 475040,
            #         "/Subtype": "/Image",
            #         "/Type": "/XObject",
            #         "/Width": 1500
            #     }, data= < ... >)
            # }

            # Corretto
            # "/Resources": {
            # "/ColorSpace": {
            #     "/Cs1": ["/ICCBased",
            #
            #              pikepdf.Stream(stream_dict={
            #                  "/Alternate": "/DeviceRGB",
            #                  "/Filter": "/FlateDecode",
            #                  "/Length": 2612,
            #                  "/N": 3
            #              },
            #                  data= < ... >)]
            # },
            # ...
            # "/XObject": {
            #     "/Im3": pikepdf.Stream(stream_dict={
            #     "/BitsPerComponent": 8,
            #     "/ColorSpace": <.get_object(6, 0) >,
            #     "/Filter": "/DCTDecode",
            #     "/Height": 1000,
            #     "/Interpolate": True,
            #     "/Length": 380302,
            #     "/Subtype": "/Image",
            #     "/Type": "/XObject",
            #     "/Width": 1500
            # }, data = < ... >)
            # }

        if 1:
            src = Pdf.open(self.abs_output_filename)
            seed = Pdf.open('seed.pdf')
            seed_page = seed.pages[0]
            dst = Pdf.new()
            for page in src.pages:
                page['/Resources']['/ColorSpace'] = seed_page.Resources.ColorSpace
            dst.pages.extend(src.pages)
            dst.save(self.abs_output_filename + '_resaved.pdf')

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
            # self.read_metadata()
            # self.resave_pdf()


class FileEdit(QLineEdit):
    def __init__(self, parent, detail_widget):
        super(FileEdit, self).__init__(parent)
        # Si usa solo nel caso del QLineEdit
        # self.setDragEnabled(True)
        self.detail_widget = detail_widget

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

                pdf = FotoPDF(draggedpath, self, self.detail_widget)
                pdf.create_pdf()
            else:
                self.setText("Invalid file or folder.")


class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super(Highlighter, self).__init__(parent)
        self.infoFormat = QTextCharFormat()
        self.infoFormat.setForeground(Qt.white)
        self.infoFormat.setBackground(Qt.green)
        self.warningFormat = QTextCharFormat()
        self.warningFormat.setForeground(Qt.black)
        # self.warningFormat.setBackground(Qt.yellow)
        self.warningFormat.setBackground(QColor(MACOSYELLOW[0], MACOSYELLOW[1], MACOSYELLOW[2]))
        self.errorFormat = QTextCharFormat()
        self.errorFormat.setForeground(Qt.white)
        self.errorFormat.setBackground(QColor(MACOSRED[0], MACOSRED[1], MACOSRED[2]))

    def highlightBlock(self, text):
        # uncomment this line for Python2
        # text = unicode(text)
        if text.startswith('Info'):
            self.setFormat(0, len(text), self.infoFormat)
        elif text.startswith('Warning'):
            self.setFormat(0, len(text), self.warningFormat)
        elif text.startswith('Error'):
            self.setFormat(0, len(text), self.errorFormat)


def MainGUI():
    # app = QApplication(sys.argv)
    app = QApplication([])
    win = QMainWindow()
    win.setGeometry(200, 200, 300, 450)
    win.setFixedSize(300, 450)
    win.setWindowTitle("FotoPDF")
    app.setWindowIcon(QIcon('FotoPDF.png'))

    detail_widget = QTextEdit(win)
    detail_widget.setAlignment(Qt.AlignCenter)
    highlighter = Highlighter(detail_widget.document())
    detail_widget.setReadOnly(True)
    detail_widget.setText("Tip: it works with both a folder or any file in that folder.")
    detail_widget.setGeometry(0, 300, 300, 150)
    detail_widget.setStyleSheet("background-color: rgb{}; color: rgb(255,255,255);".format(str(MACOSDARK)))

    # Create widget to accept drag&drop
    header_widget = FileEdit(win, detail_widget)
    header_widget.setAlignment(Qt.AlignCenter)
    header_widget.setReadOnly(True)
    header_widget.setText("Drag folder here")
    header_widget.setGeometry(0, 0, 300, 300)
    font = header_widget.font()
    font.setPointSize(32)
    header_widget.setFont(font)
    header_widget.setStyleSheet(
        "background-color: rgb{}; color: rgb(255,255,255);border : 5px solid rgb{};".format(str(MACOSYELLOW),
                                                                                            str(MACOSDARK)))
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    if DEBUG:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            print("Running in a Pyinstaller bundle.")
        else:
            print("Running in a normal Python process.")

        for a in sys.argv:
            print("sys.argv[]: {}".format(a))
        print(sys.executable)
        print(os.getcwd())

    if GUI:
        MainGUI()
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
#
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
