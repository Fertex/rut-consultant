import io
import fitz
from PIL import Image
from pyzbar import pyzbar


def process_vaccine_pdf(pdf_file, web_instance):
    # Initializing variables to store output data
    qr_data = None
    pdf_text = None
    output = {}

    # Reading document data from file and starting main loop by page found in document
    pdf = fitz.Document(stream=pdf_file.read(), filetype='pdf')
    for page_index in range(len(pdf)):
        # Searching for images in page content and obtaining raw text
        page = pdf[page_index]
        image_list = page.getImageList()
        pdf_text = page.getText()

        for image in image_list:
            # Search for QR image over the images found in the page, continue when detected
            if image[2] == image[3] and image[8] == 'FlateDecode':
                # Process raw data from QR
                image_data = pdf.extractImage(image[0])
                image_bytes = io.BytesIO(image_data['image'])
                image_file = Image.open(image_bytes)
                qr_codes = pyzbar.decode(image_file)

                # If it is a valid QR, decode inner data
                if len(qr_codes) > 0:
                    qr_data = qr_codes[0].data.decode('utf-8')

    # If raw text detected, process it
    if pdf_text is not None:
        # reading text line by line and initialize data dictionary
        pdf_lines = pdf_text.split('\n')
        pdf_data = {'documento': pdf_lines[0]}
        for index, line in enumerate(pdf_lines):
            # Main "switch-case" logic to obtain requested data
            if 'Estado:' in line:
                pdf_data['estado'] = line.split(':')[-1].strip()

            elif 'Fecha de nacimiento:' in line:
                pdf_data['fechaNacimiento'] = pdf_lines[index + 1]

            elif 'Sexo:' in line:
                pdf_data['genero'] = pdf_lines[index + 1]

            elif 'Esquema:' in line:
                pdf_data['esquema'] = line.split(':')[-1].strip()

            elif '1 Dosis' in line:
                pdf_data['dosis1'] = pdf_lines[index + 1]

            elif '2 Dosis' in line:
                pdf_data['dosis2'] = pdf_lines[index + 1]

        # Push all data found into output
        output['pdfInfo'] = pdf_data

    # If QR data is valid open the browser window to search for more data
    if qr_data is not None:
        output['qrInfo'] = web_instance.get_qr_page(qr_data)

    return output  # Sending back the output data for JSON formatting
