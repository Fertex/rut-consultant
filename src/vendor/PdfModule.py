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
        dose = []
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
                _date = pdf_lines[index + 1].strip().split('/')
                pdf_data['fechaNacimiento'] = _date[-1] + '-' + _date[1] + '-' + _date[0]

            elif 'Documento /' in line:
                pdf_data['run'] = pdf_lines[index + 1].split('RUN')[-1].strip().replace('.', '')

            elif 'Esquema:' in line:
                pdf_data['esquema'] = line.split(':')[-1].strip()

            elif 'dosis' in line:
                dose.append(get_dose_data(index, pdf_lines))

            elif 'Refuerzo:' in line:
                pdf_data['refuerzo'] = [get_dose_data(index + 1, pdf_lines)]

        # Push all data found into output
        pdf_data['dosis'] = dose
        pdf_data['nombre'] = name
        output = pdf_data

    return output  # Sending back the output data for JSON formatting


def get_dose_data(dose_row_index, lines):
    valid_data = False
    serial_no = ''
    vaccination_center_data = []

    for i in range(dose_row_index, len(lines) + 1):
        if 'Vacunatorio /' in lines[i]:
            valid_data = True
            continue

        elif 'serie /' in lines[i]:
            serial_no = lines[i + 1].strip()
            break

        if valid_data:
            vaccination_center_data.append(lines[i].strip())

    _date = lines[dose_row_index + 4].strip().split(' ')

    return {
        'laboratorioFabricante': lines[dose_row_index + 2],
        'vacunaAdministrada': lines[dose_row_index + 6],
        'lote': serial_no,
        'fechaVacunacion': date_formatting(_date[1], _date[-1], _date[0]),
        'vacunatorio': ' '.join(vaccination_center_data)
    }


def date_formatting(month, year, day):
    months = {
        'Enero': '01',
        'Febrero': '02',
        'Marzo': '03',
        'Abril': '04',
        'Mayo': '05',
        'Junio': '06',
        'Julio': '07',
        'Agosto': '08',
        'Septiembre': '09',
        'Octubre': '10',
        'Noviembre': '11',
        'Diciembre': '12'

    }

    return year + '-' + months[month] + '-' + day
