import json
import logging
import requests
from time import sleep
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver import Chrome, ChromeOptions
from selenium.common.exceptions import NoSuchElementException, UnexpectedAlertPresentException

from .resources.db import SOLUTIONS as DB  # Local database filled with solutions for captchas


class WebActions:

    def __init__(self, driver_exe, agent):
        web_options = ChromeOptions()
        web_options.add_argument("--headless")
        web_options.add_argument('--disable-gpu')
        web_options.add_argument('--no-sandbox')
        web_options.add_argument('disable-blink-features=AutomationControlled')
        web_options.add_argument(f'user-agent={agent}')

        if driver_exe == '':
            self.session = Chrome(options=web_options)

        else:
            self.session = Chrome(driver_exe, options=web_options)

    def get_taxpayer_data(self, input_data: list):
        # Format used to define the output response JSON
        output_struct = {
            'RUT': {  # It defines JSON node name
                'as': 'str',  # It defines variable type
                'by': By.XPATH,  # It defines the method used to select the browser element
                'query': '//div[strong[contains(text(), "Nombre")]]/following-sibling::div[1]'  # It defines the element
            },

            'RazonSocial': {
                'as': 'str',
                'by': By.XPATH,
                'query': '//div[b[contains(text(), "RUT")]]/following-sibling::div[1]'
            },

            'InicioActividades': {
                'as': 'bool',
                'by': By.XPATH,
                'query': '//span[contains(text(), "presenta Inicio")]'
            },

            'FechaInicioActividades': {
                'as': 'str',
                'by': By.XPATH,
                'query': '//span[contains(text(), "Fecha de Inicio")]'
            },

            'AutorizadoMonedaExtranjera': {
                'as': 'bool',
                'by': By.XPATH,
                'query': '//span[contains(text(), "extranjera")]'
            },

            'ProPyme': {
                'as': 'bool',
                'by': By.XPATH,
                'query': '//span[contains(text(), "PRO-PYME")]'
            }

        }

        # Constants used by the web session
        main_url = 'https://zeus.sii.cl/cvc/stc/stc.html'
        data_url = 'https://zeus.sii.cl/cvc_cgi/stc/getstc'
        table_template = '//table[1]/tbody/tr[{}]/td[{}]/font'

        # Opening web portal with the session and filling the input form
        self.session.get(main_url)
        self.session.find_element_by_id('RUT').send_keys(input_data[0])
        self.session.find_element_by_id('DV').send_keys(input_data[1])

        # Starting to try solutions for captcha, it don't stops until a solution is found or when RUT is not valid
        captcha_solved = False
        while not captcha_solved:
            # Selecting web element which contains the captcha image and obtaining the unique code for solution
            captcha_txt = str(self.session.find_element_by_id('imgcapt').get_attribute('src')).split('txtCaptcha=')[1]
            code = captcha_txt[89:110]

            # Searching code in local DB
            if code in DB.keys():
                # If found, writes the solution and click continue
                self.session.find_element_by_id('txt_code').send_keys(DB[code])
                self.session.find_element_by_xpath('//div/input[@name="ACEPTAR"]').click()
                sleep(1)

                try:
                    if self.session.current_url == data_url:  # It verifies if the rut was correct
                        logging.info(f'Captcha solved by code: "{code}"')
                        captcha_solved = True

                    else:
                        # If rut is incorrect the process stops
                        return None

                except UnexpectedAlertPresentException:
                    # It triggers whenever an unexpected alert pop up in the portal
                    return None

            else:
                # If the solution was not found, it refresh the captcha and tries again
                self.session.find_element_by_xpath('//div/input[@value="Refrescar"]').click()
                sleep(1)

        # After solving, it starts to formatting the JSON
        output = {}
        table_data = []
        # It defines the columns from the "Actividades Economicas" table
        table_structure = ['Actividad', 'Codigo', 'Categoría', 'AfectaIva', 'Fecha']
        for key, item in output_struct.items():  # Start to process web elements related to the output JSON structure
            value = ''
            element_txt = ''

            try:
                # Trying to get the text from every needed web element
                element_txt = self.session.find_element(item['by'], item['query']).text

            except NoSuchElementException:
                logging.warning(f'Web element "{key}" was not found by "{item["query"]}".')

            # Using the type defined in the structure it creates the correct format for the JSON value
            if element_txt != '':
                if ':' in element_txt:
                    element_txt = (element_txt.split(':'))[1]

                if item['as'] == 'bool':
                    value = True if 'SI' in element_txt else False

                else:
                    value = element_txt

            # It stores the value from the web element
            output[key] = value

        # Starting formatting for "actividades economicas" table
        row_available = True
        row_num = 2  # Starting from the second row, because the firsts it just the columns names
        while row_available:  # Iterates over every possible row detected
            table_row = {}

            # Iterates over every column in the actual row searching for the cell value
            try:
                for i in range(1, len(table_structure)+1):
                    cell_value = self.session.find_element_by_xpath(table_template.format(row_num, i)).text

                    # If the cell value is a boolean element the output value has to match it
                    if cell_value == 'Si':
                        table_row[table_structure[i - 1]] = True

                    elif cell_value == 'No':
                        table_row[table_structure[i - 1]] = False

                    else:
                        table_row[table_structure[i-1]] = cell_value

                table_data.append(table_row)  # It stores all the table data by row
                row_num += 1

            except NoSuchElementException:
                # If no more rows detected, table iteration stops
                row_available = False

        output['ActividadesEconomicas'] = table_data  # It stores the table in the JSON output variable
        return output

    @staticmethod
    def get_certificates_by_run(input_data: list):
        # Initialization fo the process, constants, structures and variables
        profile_struct = {  # It defines the structure of the profile cells
            'codigo': {  # JSON key used in the output
                'as': 'str'  # Native python type for the value
            },

            'nombre': {
                'as': 'str'
            },

            'anhoCertificación': {
                'as': 'int'
            }

        }

        capabilities_struct = {  # It defines the structure of the capabilities cells
            'codigo': {  # JSON key used in the output
                'as': 'str',  # Native python type for the value
                'get': 'text',  # HTML property which allocates the value
                'from': 'base'  # HTML tag needed
            },

            'nombre': {
                'as': 'str',
                'get': 'text',
                'from': 'base'
            },

            'fechaAcreditacion': {
                'as': 'date;%d/%m/%Y;%Y%m%dT00:00:00',
                'get': 'text',
                'from': 'div'
            },

            'competencia': {
                'as': 'bool',
                'trueif': 'COMPETENTE',
                'get': 'title',
                'from': 'img'
            }

        }
        # urls and headers needed to obtain data from the web portal
        id_url = 'https://certificacion.chilevalora.cl/ChileValora-publica/candidatosPublicListTable.html?' \
                 'iDisplayStart=0&iDisplayLength=10&sSearch={}&sSortDir_0=asc'
        id_headers = {'Accept-Encoding': 'gzip, deflate, br',
                      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
        main_url = 'https://certificacion.chilevalora.cl/ChileValora-publica/candidatosEdit.html?paramRequest={}'
        pdf_url = 'https://certificacion.chilevalora.cl/ChileValora-publica/candidatosExportarPDF.html?paramRequest={}'
        output = None

        # Starting request process to obtain data
        run = input_data[0] + '-' + input_data[1]
        id_response = requests.get(id_url.format(run), headers=id_headers)  # Obtaining local id from RUN
        if id_response.status_code == 200:
            id_data = json.loads(id_response.text)['aaData']

            if len(id_data) > 0:  # If the response was ok and a person was detected, the process continues
                main_response = requests.get(main_url.format(id_data[0][0]))

                # Starting to search the data from the local id given from the web portal
                if main_response.status_code == 200:
                    output = {}
                    html = BeautifulSoup(main_response.text, "html.parser")
                    output['run'] = run  # Adding RUN to output JSON
                    output['nombreCompleto'] = html.find_all(
                        'table', class_='TablaDoc')[0].find('td', class_='col-xs-8').text  # Adding name to output JSON
                    output['pdf'] = pdf_url.format(id_data[0][0])
                    table_rows = html.find('table', id='resultados').select('thead td')  # Selecting rows of info table

                    # Starting formatting of profiles data
                    profile_data = []
                    row = {}
                    i = 0
                    for cell in table_rows:
                        # Giving native type to the value
                        if profile_struct[list(profile_struct.keys())[i]].get('as') == 'int':
                            value = int(cell.text.replace('\r', '').replace('\n', '').replace('\t', '').strip())

                        else:
                            value = cell.text.replace('\r', '').replace('\n', '').replace('\t', '').strip()

                        if i == 0 and 'U-' in value:
                            break  # It triggers when the row is not from the profile section

                        row[list(profile_struct.keys())[i]] = value  # Adding value in a row for JSON array
                        i += 1

                        if i > 0 and i % len(profile_struct.keys()) == 0:  # Resetting row when many profiles detected
                            profile_data.append(row)  # Adding row in an array
                            i = 0
                            row = {}

                    output['perfiles'] = profile_data  # Adding profiles array to JSON output

                    # Starting formatting of capabilities data
                    cell_count = 0
                    capabilities_data = []
                    for j in range(len(profile_data)*len(profile_struct.keys()), len(table_rows)):
                        cell_struct = capabilities_struct[list(capabilities_struct.keys())[cell_count]]

                        # Searching for the HTML element which allocates required data
                        if cell_struct.get('from') == 'base':
                            element = table_rows[j]

                        else:
                            element = table_rows[j].find(cell_struct.get('from'))

                        # Obtaining text from the particular HTML attribute
                        if element is None:
                            text = ''

                        elif cell_struct.get('get') == 'text':
                            text = element.text.replace('\r', '').replace('\n', '').replace('\t', '').strip()

                        else:
                            text = element.attrs[cell_struct.get('get')]

                        # Giving native type to the value
                        if cell_struct.get('as') == 'bool':
                            if text == '':
                                value = False
                            else:
                                value = True if cell_struct.get('trueif') in text else False

                        elif 'date' in cell_struct.get('as'):
                            if text == '':
                                value = ''
                            else:
                                value = datetime.strptime(text, cell_struct.get('as').split(';')[1]).date().strftime(
                                    cell_struct.get('as').split(';')[2])

                        else:
                            value = text

                        # Adding value in a row for JSON array
                        row[list(capabilities_struct.keys())[cell_count]] = value
                        cell_count += 1

                        # Resetting row when many capabilities detected
                        if cell_count > 0 and cell_count % len(capabilities_struct.keys()) == 0:
                            capabilities_data.append(row)  # Adding row in an array
                            row = {}
                            cell_count = 0

                    output['competencias'] = capabilities_data  # Adding capabilities array to JSON output

            else:
                # It triggers when no id was detected meaning that the RUN is wrong or the data is not in the portal
                logging.info('RUN response was empty.')
                return 'NORUN'

        return output

    @staticmethod
    def get_certificates_by_rut(input_data: list):
        # urls and headers needed to obtain data from the web portal
        main_url = 'https://www.registrodeempresasysociedades.cl/ObtenerCertificadosHome.aspx'
        data_url_template = \
            'https://www.registrodeempresasysociedades.cl/Certificados/Generar.aspx?certRut={}&certTipo={}'
        data_headers = {'Accept-Encoding': 'gzip, deflate, br'}

        # Initializing data variables and output
        rut = input_data[0]
        option_data = {}
        output = None

        # Obtaining data from the main portal in order to map the output array
        main_response = requests.get(main_url)
        if main_response.status_code == 200:
            main_page = BeautifulSoup(main_response.text, "html.parser")
            options = main_page.find_all('option')  # Getting number of available certificates and theirs names

            for i in range(1, len(options)):
                option_data[i] = options[i].text

        # Obtaining the certificate document (PDF) of every available type
        certificates = []
        for certificate in option_data.items():
            certificate_data = {'Tipo': certificate[1]}  # Formatting the output JSON
            data_url = data_url_template.format(rut, certificate[0])
            try:
                # Obtaining the HTTP response with the document
                data_response = requests.get(data_url, headers=data_headers)

            except Exception as response_ex:
                logging.debug(response_ex)
                return output

            if data_response.status_code == 200:
                html = BeautifulSoup(data_response.text, "html.parser")

                if 'PDF' in html.text:
                    # When PDF data available on the response, add this url to the JSON object
                    certificate_data['Url'] = data_url

                elif 'no es válido' in html.find('span', id='boxer_content_lblBajada').text:
                    # When the web portal response with no dta of the RUT, notify it
                    output = 'NORUT'
                    break

                else:
                    # When PDF NO data available on the response, add a notification to the JSON object
                    certificate_data['Url'] = 'No disponible'

                # Add the certificate data to the output array
                certificates.append(certificate_data)

            # Validating that the output still free and no wrong status occurred
            if output is None:
                output = {'Rut': rut, 'Certificados': certificates}

        return output

    def get_qr_page(self, web_page):
        # Initializing output variable and main url
        web_data = {}
        main_url = 'https://scanmevacuno.gob.cl/'

        # Opening web page obtained from QR
        self.session.get(web_page)

        # Wait for page to be fully loaded
        page_loaded = False
        while not page_loaded:
            if self.session.current_url == main_url:
                page_loaded = True
            sleep(1)

        # Search for web elements that contained required data
        web_data['habilitado'] = True if self.session.find_element_by_xpath('//h1').text == 'HABILITADO' else False
        person_info = self.session.find_elements_by_xpath('//div[contains(@class, "identidad")]/div')

        # Reading info from web page
        if len(person_info) > 0:
            web_data['nombre'] = person_info[-1].text + ' ' + person_info[1].text
            web_data['documento'] = person_info[0].text

            # If no data found return a valid format but eith null values
            if web_data['nombre'] == ' ' and web_data['documento'] == '':
                web_data['nombre'] = None
                web_data['documento'] = None
                web_data['detalle'] = 'Error interno del portal, no se pudo obtener información'

            else:
                web_data['detalle'] = self.session.find_element_by_xpath('//div[contains(@class, "explica")]').text

        return web_data

    def get_covid_insurance(self, input_data: list):
        # Defining main url for the process
        main_url = 'https://covid.aach.cl/'

        # Initializing data variables and output
        run = input_data[0]
        output = {}
        data_fields = {  # This dict contains as keys the id from the field in portal and as name the JSON output field
            "Rut": {
                'name': 'rut',
                'value': ''
            },
            "Nombre": {
                'name': 'nombre',
                'value': ''
            },
            "Poliza": {
                'name': 'poliza',
                'value': ''
            },
            "CiaAseguradora": {
                'name': 'aseguradora',
                'value': ''
            },
            "FechaIni": {
                'name': 'fechaInicio',
                'value': ''
            },
            "FechaFin": {
                'name': 'fechaFinal',
                'value': ''
            },
        }

        # Opening the web page and filling up the RUN field
        self.session.get(main_url)
        self.session.find_element_by_xpath('//input[contains(@id, "Run")]').send_keys(run)

        # Searching for alerts form portal, if not detected continue
        alerts = self.session.find_elements_by_xpath(
            '//div[contains(@id, "master")]//div[contains(@style, "block")]/div/small')
        if len(alerts) > 0:
            # If invalid run then stop process and send back an alert
            if 'incorrecto' in alerts[0].text:
                return 'NORUN'

        # Wait before consulting then click the button
        sleep(2.5)
        self.session.find_element_by_xpath('//a[contains(@id, "consultar")]').click()

        # Search for portal errors, if not detected continue
        portal_errors = self.session.find_elements_by_xpath('//div[contains(@id, "Error")]')
        if len(portal_errors) > 0:
            error_txt = self.session.find_element_by_xpath('//div[contains(@id, "Error")]//h2').text

            # If RUN info was not found then send back an alert
            if 'NO SE ENCONTRÓ' in error_txt:
                output = 'NOTFOUND'

            return output

        # Search the requested data from portal response as ana array of web elements
        insurance_fields = self.session.find_elements_by_xpath(
            '//div[contains(@id, "Certificado")]//span[contains(@id, "masterContenido_lbl")]')
        # Detect field name one by one
        for field in insurance_fields:
            field_name = field.get_attribute('id').split('Contenido_lbl')[-1]
            # If field id is required for the answer, then add it to the data dict
            if field_name in data_fields.keys():
                data_fields[field_name]['value'] = field.text

        # Check data obtained from portal that was appended to data dict
        for index, field in data_fields.items():
            # If valid data then add it to the output JSON
            if field.get('value') != '':

                if field.get('name') == 'rut':
                    output[field.get('name')] = field.get('value').replace('.', '')

                else:
                    output[field.get('name')] = field.get('value')

        return output
