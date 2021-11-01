import fitz


def process_vaccine_pdf(pdf_file):
    # Initializing variables to store output data
    pdf_text = None
    output = {}

    # Reading document data from file and starting main loop by page found in document
    pdf = fitz.Document(stream=pdf_file.read(), filetype='pdf')
    for page_index in range(len(pdf)):
        # Searching for images in page content and obtaining raw text
        page = pdf[page_index]
        pdf_text = page.getText()

    # If raw text detected, process it
    if pdf_text is not None:
        # reading text line by line and initialize data dictionary
        pdf_lines = pdf_text.split('\n')
        pdf_data = {'documento': pdf_lines[0]}
        name = ''

        for index, line in enumerate(pdf_lines):
            # Main "switch-case" logic to obtain requested data
            if index == 0 and line != 'PASE DIGITAL DE VACUNACIÓN DE CHILE':
                return 'INVALID'

            elif 'Nombres /' in line:
                name += ' ' + pdf_lines[index + 1]

            elif 'Apellidos /' in line:
                name += pdf_lines[index + 1]

            elif 'Fecha de Nacimiento /' in line:
                pdf_data['fechaNacimiento'] = pdf_lines[index + 1]

            elif 'Documento /' in line:
                pdf_data['run'] = pdf_lines[index + 1].split('RUN')[-1].strip()

            elif 'Esquema:' in line:
                pdf_data['esquema'] = line.split(':')[-1].strip()

            elif '1° dosis' in line:
                pdf_data['dosis1'] = pdf_lines[index + 4]

            elif '2° dosis' in line:
                pdf_data['dosis2'] = pdf_lines[index + 4]

            elif 'Refuerzo:' in line:
                pdf_data['refuerzo'] = pdf_lines[index + 5]

        # Push all data found into output
        pdf_data['nombre'] = name
        output['pdfInfo'] = pdf_data

    return output  # Sending back the output data for JSON formatting
