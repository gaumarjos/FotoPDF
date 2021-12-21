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
# https://github.com/tvdsluijs/pdfc/blob/master/pdf_compressor.py
# https://www.ghostscript.com/doc/current/Use.htm#Parameter_switches


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
# from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QLineEdit
# from PyQt5.QtGui import QIcon, QSyntaxHighlighter, QTextCharFormat, QColor
# from PyQt5.QtCore import Qt
from PySide2.QtWidgets import QApplication, QMainWindow, QTextEdit, QLineEdit
from PySide2.QtGui import QIcon, QSyntaxHighlighter, QTextCharFormat, QColor
from PySide2.QtCore import Qt
# import subprocess
import ghostscript
import locale

# os.environ['QT_MAC_WANTS_LAYER'] = '1'
# os.environ['QT_DEBUG_PLUGINS'] = '1'
reportlab.rl_config.warnOnMissingFontGlyphs = 0

# Constants
VERSION = '2021-08-03'
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
LANGUAGES = ['it', 'en', 'de', 'fr', 'es']


# Translate asset paths to usable format for PyInstaller
# if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
#     print("Running in a Pyinstaller bundle.")
# else:
#     print("Running in a normal Python process.")
def resource_path(path):
    # Needed only is the path is relative
    if not os.path.isabs(path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, path)
        return os.path.join(os.path.abspath('.'), path)
    else:
        return path


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    return [atoi(c) for c in re.split(r'(\d+)', text)]


def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def longest_common_prefix(list_of_strings):
    if list_of_strings == []:
        return ''
    if len(list_of_strings) == 1:
        return list_of_strings[0]
    list_of_strings.sort()
    shortest = list_of_strings[0]
    prefix = ''
    for i in range(len(shortest)):
        if list_of_strings[len(list_of_strings) - 1][i] == shortest[i]:
            prefix += list_of_strings[len(list_of_strings) - 1][i]
        else:
            break
    return prefix


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
        self.abs_tmp_output_filename = None
        self.abs_output_filename = None
        self.H = 0
        self.W = 0
        # if USE_FPDF:
        #     self.pdf = None
        self.c = None
        self.images = []
        self.language = None

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

    def whichcaption(self, text):
        if len(text) > 0:
            captions = text.split("#")
            captions = list(filter(None, captions))

            # Multilanguage captions are not used
            if len(captions) == 1:
                caption = captions[0]
            # They are used, look for the right language
            else:
                caption = ""
                if self.language is None:
                    caption = captions[0][3:]
                else:
                    for candidate in captions:
                        # Ignore strings that are too short, probably formatting errors
                        if len(candidate) > 4:
                            if candidate[:2].lower() == self.language:
                                caption = candidate[3:]

            return caption
        else:
            return ""

    @staticmethod
    # It fits an (image_w x image_h) image in a (rect_w x rect_h) rectangle with top left corner at (rect_x, rect_y)
    # and returns the top left corner location (scaled_image_x, scaled_image_y) and size
    # (scaled_image_w, scaled_image_h) of the scaled image
    def fit_image(rect_x, rect_y, rect_w, rect_h, image_w, image_h, halign=1, valign=1):
        # Determine whether the limiting factor will be the width or the height
        w_ratio = rect_w / image_w
        if w_ratio * image_h <= rect_h:
            # The width is the limiting factor
            scaled_image_w = rect_w
            scaled_image_h = image_h * w_ratio
        else:
            # The height is the limiting factor
            h_ratio = rect_h / image_h
            scaled_image_w = image_w * h_ratio
            scaled_image_h = rect_h

        # Horizontal alignment
        if halign == 0:
            # Left
            scaled_image_x = rect_x * 1.
        elif halign == 1:
            # Center
            scaled_image_x = (rect_w - scaled_image_w) / 2. + rect_x

        # Vertical alignment
        if valign == 0:
            # Top
            scaled_image_y = rect_y * 1.
        elif valign == 1:
            # Center
            scaled_image_y = (rect_h - scaled_image_h) / 2. + rect_y

        return scaled_image_x, scaled_image_y, scaled_image_w, scaled_image_h

    def vrel2abs(self, x):
        if x > 1.0:
            return x
        else:
            return x * self.H

    # It converts the y coordinate from a top (easier for the author to understand) to a bottom (use by reportlab)
    # reference frame
    def top2bottom(self, top_y, element_h):
        return self.H - top_y - element_h

    # def fpdf_centered_text(self, text, font, size, y, black=True):
    #     self.pdf.set_y(y)
    #     self.pdf.set_font(font, '', size)
    #     if black:
    #         self.pdf.set_text_color(0, 0, 0)
    #     else:
    #         self.pdf.set_text_color(255, 255, 255)
    #     self.pdf.cell(0, 0, text, 0, 1, align="C", fill=False)
    #     self.pdf.set_text_color(0, 0, 0)

    def rl_single_line_centered_text(self, text, font, size, from_top, black=True):
        self.c.setFont(font, size)
        if black:
            self.c.setFillColorRGB(0, 0, 0)
        else:
            self.c.setFillColorRGB(1, 1, 1)
        text_width = self.c.stringWidth(text, font, size)
        # drawString requires the bottom left corner of the text to draw, converting the y coordinate. For a single-line
        # text, the height of the textbox is the size of the font.
        self.c.drawString((self.W - text_width) / 2.0, self.top2bottom(from_top, size), text)

    def rl_text(self, text, font, alignment, size, interline, from_side, from_top, black=True):
        stylesheet = getSampleStyleSheet()
        style = stylesheet['BodyText']
        style.fontSize = size
        style.fontName = font
        # 0 = left
        # 1 = center
        # 2 = right
        # 4 = justify
        style.alignment = alignment
        if black:
            style.textColor = colors.black
        else:
            style.textColor = colors.white
        style.leading = size + interline

        p = Paragraph(text, style)
        text_area_w = self.W - (from_side * 2)
        text_area_h = self.H - from_top
        text_w, text_h = p.wrap(text_area_w, text_area_h)
        if text_w <= text_area_w and text_h <= text_area_h:
            # If there's enough space, draw
            # drawOn requires the bottom left corner of the text to draw, converting the y coordinate
            p.drawOn(self.c,
                     from_side,
                     self.top2bottom(from_top, text_h) if (from_top > 0) else self.top2bottom((self.H - text_h) / 2.,
                                                                                              text_h))
        else:
            # Otherwise report a warning and suggest make more space for text or use a smaller font
            self.message_on_detail_widget(
                "Warning: text area too small for text. Try making the area larger or reducing the font size.")

    def rl_centered_image(self, image, from_side, from_top, from_bottom):
        # Read ImageDescription field from JPG. Exifread is the only library that works. Exif doesn't have this tag and
        # Pillow corrupts the accented characters.
        tags = exifread.process_file(open(image, 'rb'))
        try:
            caption = self.whichcaption(str(tags['Image ImageDescription']))
        except:
            caption = ""
            self.message_on_detail_widget("Warning: \"{}\" does not have a caption.".format(os.path.basename(image)))

        original_image_size = PIL.Image.open(image).size
        scaled_image_x, scaled_image_y, scaled_image_w, scaled_image_h = self.fit_image(from_side,
                                                                                        from_top,
                                                                                        self.W - from_side * 2,
                                                                                        self.H - from_top - from_bottom,
                                                                                        original_image_size[0],
                                                                                        original_image_size[1],
                                                                                        valign=0)

        # drawImage requires the bottom left corner of the image to draw, converting the y coordinate
        self.c.drawImage(image,
                         x=scaled_image_x,
                         y=self.top2bottom(scaled_image_y, scaled_image_h),
                         width=scaled_image_w,
                         height=scaled_image_h,
                         mask=None)

        self.message_on_detail_widget("Image rescaled to: {} x {}".format(scaled_image_w, scaled_image_h))

        bottom_of_the_image = scaled_image_y + scaled_image_h

        return bottom_of_the_image, caption

    def inizialize_pdf(self, setting_file, setting_file_suffix):
        # In any case, write to drag folder here
        self.message_on_header_widget("Drag folder here")
        self.message_on_detail_widget("Using setting file \"{}\".".format(setting_file), append=True)

        # Lettura JSON
        with open(join(self.input_folder, setting_file), 'r', encoding="utf8") as myjson:
            data = myjson.read()
        self.obj = json.loads(data)

        # Creazione file e impostazioni generali
        if self.obj["document"]["format"] == "A4":
            self.W, self.H = landscape(A4)
        elif self.obj["document"]["format"] == "custom":
            self.H = int(self.obj["document"]["height"])
            self.W = int(self.obj["document"]["width"])
        else:
            self.message_on_detail_widget("Error: Wrong slide format.")
            return False

        output_filename = clean_html(self.obj['document']['title']) + ', ' + clean_html(self.obj['document']['author'])
        if len(self.obj['document']['suffix']) > 0:
            output_filename = output_filename + ', ' + clean_html(self.obj['document']['suffix'])

        # If the setting file has a suffix (to have it, we must have at least 2 setting files)
        if len(setting_file_suffix) > 0:
            output_filename = output_filename + ' ' + setting_file_suffix
            if setting_file_suffix.lower() in LANGUAGES:
                self.language = setting_file_suffix.lower()
                self.message_on_detail_widget(
                    "Suffix \"{}\" looks like a language tag. I'll use captions starting with \"#{}\" if present.".format(
                        self.language, self.language))
        else:
            # If the setting file has no suffix (so, we have only one setting file), but that ends with something that
            # looks like a language, then process it as such. -5 is to remove .json.
            if setting_file[-7:-5] in LANGUAGES:
                self.language = setting_file[-7:-5].lower()
                self.message_on_detail_widget(
                    "Suffix \"{}\" looks like a language tag. I'll use captions starting with \"#{}\" if present.".format(
                        self.language, self.language))

        output_filename = output_filename + ".pdf"

        self.abs_tmp_output_filename = join(self.input_folder, 'tmp.pdf')
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
        self.c = canvas.Canvas(self.abs_tmp_output_filename, enforceColorSpace='RGB')
        self.c.setPageSize((self.W, self.H))
        self.c.setTitle(self.obj["document"]["title"])
        self.c.setAuthor(self.obj["document"]["author"])

        # Use user-defined True Type Font (TTF)
        try:
            pdfmetrics.registerFont(TTFont('font_title', resource_path(self.obj["fonts"]["title"])))
        except:
            self.message_on_detail_widget(
                "Error: Cannot find font_title, looking in {}".format(resource_path(self.obj["fonts"]["title"])))
            return False

        try:
            pdfmetrics.registerFont(TTFont('font_author', resource_path(self.obj["fonts"]["author"])))
        except:
            self.message_on_detail_widget("Error: Cannot find font_author, looking in {}".format(
                resource_path(self.obj["fonts"]["author"])))
            return False

        try:
            pdfmetrics.registerFont(TTFont('font_text', resource_path(self.obj["fonts"]["text"])))
        except:
            self.message_on_detail_widget("Error: Cannot find font_text, looking in {}".format(
                resource_path(self.obj["fonts"]["author"])))
            return False

        self.c.setFont('font_text', 16)

        # Ricerca immagini
        self.images = [f for f in listdir(self.input_folder) if f.lower().endswith(".jpg")]
        self.images.sort(key=natural_keys)
        if len(self.images) == 0:
            self.message_on_detail_widget("Error: No image found in folder.", append=True)
            return False
        self.message_on_detail_widget("Creating PDF...")

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

        # Draw the image horizontally center and scaled to occupy the whole frame. It expects an horizontal image.
        original_image_size = PIL.Image.open(
            join(self.input_folder, self.images[self.obj["cover"]["use_image"] - 1])).size
        zoom = float(self.obj['cover']['zoom'])
        scaled_image_x, scaled_image_y, scaled_image_w, scaled_image_h = self.fit_image(-self.W/2.0*(zoom-1.0),
                                                                                        -self.H/2.0*(zoom-1.0),
                                                                                        self.W*zoom, self.H*zoom,
                                                                                        original_image_size[0],
                                                                                        original_image_size[1])
        self.c.drawImage(join(self.input_folder, self.images[self.obj["cover"]["use_image"] - 1]),
                         x=scaled_image_x,
                         y=scaled_image_y,
                         width=scaled_image_w,
                         height=scaled_image_h,
                         preserveAspectRatio=True)

        # Draw the title horizontally centered
        self.rl_text(self.obj['document']['title'],
                     'font_title',
                     1,
                     int(self.obj['cover']['title']['size']),
                     int(self.obj['cover']['title']['interline']),
                     self.vrel2abs(float(self.obj['cover']['title']['from_side'])),
                     self.vrel2abs(float(self.obj['cover']['title']['from_top'])),
                     black=self.obj["cover"]["title"]["black_text"])

        # Draw the author
        self.rl_single_line_centered_text(self.obj["document"]["author"],
                                          'font_author',
                                          int(self.obj['cover']['author']['size']),
                                          self.vrel2abs(float(self.obj['cover']['author']['from_top'])),
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
        self.rl_text(text,
                     'font_text',
                     0,
                     int(self.obj['description']['size']),
                     int(self.obj['description']['interline']),
                     self.vrel2abs(float(self.obj['description']['from_side'])),
                     self.vrel2abs(float(self.obj['description']['from_top'])))
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
                                                     int(self.obj['photos']['from_top']),
                                                     int(self.obj['photos']['from_bottom']))
            self.rl_text(caption,
                         'font_text',
                         0,
                         int(self.obj['photos']['size']),
                         int(self.obj['photos']['interline']),
                         int(self.obj['photos']['from_side']),
                         (text_x + 1. * int(self.obj['photos']['size']) + 0. * int(self.obj['photos']['interline'])))
            self.c.showPage()

    def grid_page(self):
        r = int(self.obj['grid']['rows'])
        c = int(self.obj['grid']['columns'])
        m_oriz = int(self.obj["grid"]["horizontal_margin"])
        m_vert = int(self.obj["grid"]["vertical_margin"])
        m_lat = int(self.obj["grid"]["lateral_margin"])
        fitting_block_ratio = float(self.obj["grid"]["fitting_block_ratio"])

        # Starting from columns and checking if the total height is within the margins
        rect_w = (self.W - 2 * m_lat - (c - 1) * m_oriz) / c
        rect_h = rect_w / fitting_block_ratio
        total_h = r * rect_h + (r - 1) * m_vert + m_lat
        # Too high, restarting from rows and checking if the total width is within the margins
        if total_h > self.H:
            rect_h = (self.H - 2 * m_lat - (r - 1) * m_vert) / r
            rect_w = rect_h * fitting_block_ratio
            total_w = c * rect_w + (c - 1) * m_oriz + m_lat
            if total_w > self.W:
                print("It cannot be.")

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
                                              int(self.obj['final']['author']['size']),
                                              self.vrel2abs(float(self.obj['final']['author']['from_top'])),
                                              True)

        if bool(self.obj['final']['website']['show']):
            # if USE_FPDF:
            #     self.fpdf_centered_text(self.obj['final']['website']['string'],
            #                             'font_text',
            #                             self.obj['final']['website']['size'],
            #                             self.obj['final']['website']['from_top'], black=True)
            self.rl_single_line_centered_text(self.obj['document']['website'],
                                              'font_text',
                                              int(self.obj['final']['website']['size']),
                                              self.vrel2abs(float(self.obj['final']['website']['from_top'])),
                                              True)

        if bool(self.obj['final']['email']['show']):
            # if USE_FPDF:
            #     self.fpdf_centered_text(self.obj['final']['email']['string'],
            #                             'font_text',
            #                             self.obj['final']['email']['size'],
            #                             self.obj['final']['email']['from_top'], black=True)
            self.rl_single_line_centered_text(self.obj['document']['email'],
                                              'font_text',
                                              int(self.obj['final']['email']['size']),
                                              self.vrel2abs(float(self.obj['final']['email']['from_top'])),
                                              True)

        if bool(self.obj['final']['phone']['show']):
            # if USE_FPDF:
            #     self.fpdf_centered_text(self.obj['final']['phone']['string'],
            #                             'font_text',
            #                             self.obj['final']['phone']['size'],
            #                             self.obj['final']['phone']['from_top'], black=True)
            self.rl_single_line_centered_text(self.obj['document']['phone'],
                                              'font_text',
                                              int(self.obj['final']['phone']['size']),
                                              self.vrel2abs(float(self.obj['final']['phone']['from_top'])),
                                              True)

        if bool(self.obj['final']['disclaimer']['show']):
            # if USE_FPDF:
            #     self.fpdf_centered_text(self.obj['final']['disclaimer']['string'],
            #                             'font_text',
            #                             self.obj['final']['disclaimer']['size'],
            #                             self.obj['final']['disclaimer']['from_top'], black=True)
            self.rl_single_line_centered_text(self.obj['document']['disclaimer'],
                                              'font_text',
                                              int(self.obj['final']['disclaimer']['size']),
                                              self.vrel2abs(float(self.obj['final']['disclaimer']['from_top'])),
                                              True)

        self.c.showPage()

    def save_pdf(self):
        # Salva
        # if USE_FPDF:
        #     self.pdf.output(self.abs_tmp_output_filename, "F")
        self.c.save()

    def read_metadata(self):
        pass

    def resave_pdf(self):
        if 0:
            quality = {
                0: '/default',
                1: '/prepress',
                2: '/printer',
                3: '/ebook',
                4: '/screen'
            }
            args = ['gs', '-sDEVICE=pdfwrite',
                    '-dCompatibilityLevel=1.4',
                    '-dPDFSETTINGS={}'.format(quality[0]),
                    '-dNOPAUSE',
                    '-dQUIET',
                    '-dBATCH',
                    '-dColorAccuracy=2',
                    '-dProcessColorModel=/DeviceRGB',
                    '-sOutputFile={}'.format(self.abs_output_filename),
                    self.abs_tmp_output_filename]

            # '-sDefaultRGBProfile=sRGB_v4_ICC_preference.icc',
            # '-sOutputICCProfile=sRGB_v4_ICC_preference.icc',
            # '-sImageICCProfile=sRGB_v4_ICC_preference.icc',

            # Using python ghostscript module
            encoding = locale.getpreferredencoding()
            args = [a.encode(encoding) for a in args]
            ghostscript.Ghostscript(*args)

            # Calling ghoscript directly
            # subprocess.call(args)

            # Remove original file, called tmp.pdf
            if os.path.exists(self.abs_tmp_output_filename):
                os.remove(self.abs_tmp_output_filename)
        else:
            os.rename(self.abs_tmp_output_filename, self.abs_output_filename)

        self.message_on_header_widget("Created ({:.1f}MB)!".format(
            getsize(self.abs_output_filename) / 1000000.))
        self.message_on_detail_widget("Created ({:.1f}MB)!\n".format(
            getsize(self.abs_output_filename) / 1000000.))

    def create_pdf(self):
        # Manage the case when more than one json exists

        # Ricerca json
        setting_files = [f for f in listdir(self.input_folder) if f.endswith(".json")]
        setting_files.sort(key=natural_keys)
        prefix = longest_common_prefix(setting_files)

        self.message_on_detail_widget("Dragged folder \"{}\".\n".format(self.input_folder), append=False)

        # If no JSON is found, a default one will be created from a template
        if len(setting_files) == 0:
            self.message_on_detail_widget(
                "Warning: Cannot find settings.json in folder. Creating a default one that will need to be customized.")
            shutil.copyfile('settings.json', join(self.input_folder, 'settings.json'))
        else:
            # Create one PDF for each JSON file found
            for setting_file in setting_files:
                # A suffix is useful in case of multiple JSON files to distinguish between the multiple documents that
                # are generated.
                setting_file_suffix = setting_file[len(prefix):-len(".json")]
                # Create the document
                if self.inizialize_pdf(setting_file, setting_file_suffix):
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
                    self.resave_pdf()
            self.message_on_detail_widget("Drag another folder to create a new one.")


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
    win.setGeometry(200, 200, 300, 600)
    win.setFixedSize(300, 600)
    win.setWindowTitle("FotoPDF" + " " + VERSION)
    app.setWindowIcon(QIcon(resource_path('FotoPDF.png')))

    detail_widget = QTextEdit(win)
    detail_widget.setAlignment(Qt.AlignCenter)
    highlighter = Highlighter(detail_widget.document())
    detail_widget.setReadOnly(True)
    detail_widget.setText("Tip: it works with "
                          "both a folder or any file in that folder.")
    detail_widget.setGeometry(0, 300, 300, 300)
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
    if GUI:
        MainGUI()
    else:
        mypdf = FotoPDF(sys.argv[1:], None)
        mypdf.create_pdf()
