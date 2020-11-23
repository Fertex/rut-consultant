import logging
from os import path
from time import sleep
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, UnexpectedAlertPresentException

from .libs.db_manager import DbDriver


class WebActions:

    def __init__(self, driver_exe, base_path):
        web_options = ChromeOptions()
        web_options.add_argument("--headless")
        web_options.add_argument('--disable-gpu')
        web_options.add_argument('--no-sandbox')
        self.base_path = base_path

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

        # Local database filled with solutions for captchas
        db = DbDriver('SQLite', path.join(self.base_path, r'/resources/capchas.db'))
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
            solutions = db.get_df_from_table('solutions', f"code='{code}'")  # Searching code in local DB

            if len(solutions['id']) > 0:
                # If found, writes the solution and click continue
                self.session.find_element_by_id('txt_code').send_keys(solutions['solution'])
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
