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

if 0:
    src = Pdf.open(self.abs_output_filename)
    seed = Pdf.open('seed.pdf')
    seed_page = seed.pages[0]
    dst = Pdf.new()
    for page in src.pages:
        page['/Resources']['/ColorSpace'] = seed_page.Resources.ColorSpace
        print(page['/Resources'])
    dst.pages.extend(src.pages)
    dst.save(self.abs_output_filename + '_resaved.pdf')

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
