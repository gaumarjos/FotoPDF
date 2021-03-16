# Stefano Salati 2021-03-16
# Untested, have fun!

from os import listdir
from os.path import isfile, join
from fpdf import FPDF
import re
import getopt
import sys
import json

def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    return [atoi(c) for c in re.split(r'(\d+)', text)]


def main(argv):

    # Valori default
    input_folder = "."
    output_filename = "presentation"

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

    # Dimensioni foglio A4 in mm
    H = obj["document"]["height"]
    W = obj["document"]["width"]

    # Creazione file e impostazioni generali
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_compression(False)
    pdf.set_margins(0, 0, 0)
    pdf.set_auto_page_break(False)
    pdf.set_fill_color(255, 255, 255)
    pdf.set_text_color(0, 0, 0)
    pdf.set_title(obj["document"]["title"])
    pdf.set_author(obj["document"]["author"])

    if bool(obj["font"]["usemyfont"]):
        try:
            pdf.add_font('myfont', '', obj["font"]["myfont"], uni=True)
            pdf.set_font('myfont', '', 48)
        except:
            pdf.set_font(obj["font"]["family"], '', 48)
    else:
        pdf.set_font(obj["font"]["family"], '', 48)

    # Ricerca immagini
    images = [f for f in listdir(input_folder) if f.endswith(".jpg")]
    images.sort(key=natural_keys)

    # Copertina
    if bool(obj['cover']['show']):
        pdf.add_page()
        pdf.set_y(H * float(obj['cover']['title']['from_top']) / 10.)
        pdf.set_font_size(int(obj['cover']['title']['size']))
        pdf.cell(0, 0, obj['cover']['title']['string'], 0, 1, align="C", fill=False)

        pdf.set_y(H * float(obj['cover']['author']['from_top']) / 10.)
        pdf.set_font_size(int(obj['cover']['author']['size']))
        pdf.cell(0, 0, obj["document"]["author"], 0, 1, align="C", fill=False)

    # Pagina testo
    if bool(obj['description']['show']):
        pdf.add_page()
        pdf.set_y(H * float(obj['description']['from_top']) / 10.)
        pdf.set_x(int(obj['description']['from_side']))
        pdf.set_font_size(int(obj['description']['size']))
        pdf.multi_cell(w=W-int(obj['description']['from_side'])*2, h=int(obj['description']['interline']), txt=obj['description']['string'], border=0, align="L", fill=False)

    # Aggiungi immagini
    pdf.set_font_size(int(obj['photos']['size']))
    for i, image in enumerate(images):
        pdf.add_page()
        pdf.image(join(input_folder, image), x=12, y=10, w=W-24, h=0)
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
    else:
        pdf.set_fill_color(255, 255, 255)
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
            pdf.set_y(H * float(obj['final']['author']['from_top']) / 10.)
            pdf.set_font_size(int(obj['final']['author']['size']))
            pdf.cell(0, 0, obj["document"]["author"], 0, 1, align="C", fill=False)

        if bool(obj['final']['website']['show']):
            pdf.set_y(H * float(obj['final']['website']['from_top']) / 10.)
            pdf.set_font_size(int(obj['final']['website']['size']))
            pdf.cell(0, 0, obj['final']['website']['string'], 0, 1, align="C", fill=False)

        if bool(obj['final']['email']['show']):
            pdf.set_y(H * float(obj['final']['email']['from_top']) / 10.)
            pdf.set_font_size(int(obj['final']['email']['size']))
            pdf.cell(0, 0, obj['final']['email']['string'], 0, 1, align="C", fill=False)

        if bool(obj['final']['phone']['show']):
            pdf.set_y(H * float(obj['final']['phone']['from_top']) / 10.)
            pdf.set_font_size(int(obj['final']['phone']['size']))
            pdf.cell(0, 0, obj['final']['phone']['string'], 0, 1, align="C", fill=False)

        if bool(obj['final']['disclaimer']['show']):
            pdf.set_y(H * float(obj['final']['disclaimer']['from_top']) / 10.)
            pdf.set_font_size(int(obj['final']['disclaimer']['size']))
            pdf.cell(0, 0, obj['final']['disclaimer']['string'], 0, 1, align="C", fill=False)

    # Salva
    pdf.output(join(input_folder, output_filename + ".pdf"), "F")


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