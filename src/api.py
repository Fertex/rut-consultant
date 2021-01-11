import logging
from json import dumps
from random import choice
from flask import Flask, request
from itsdangerous import BadSignature
from flask_httpauth import HTTPTokenAuth
from string import ascii_letters, digits
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

import config as conf
from vendor.BrowserModule import WebActions


class Api:

    # Basic configuration for the app
    api = Flask(conf.APP_NAME)
    auth = HTTPTokenAuth('Bearer')

    def __init__(self):
        self.web = WebActions(conf.DRIVER_PATH)
        logging.info('Web service initialized')
        self.token_gen = Serializer(conf.APP_SECRET, conf.TTE)
        logging.info('Token generator initialized')

    def serve(self):
        # Route for login (needed for authentication)
        @self.api.route('/api/sign-in', methods=['POST'])
        def login():
            input_data = request.get_json()

            try:
                assert 'user' in input_data.keys()

                if input_data['user'] in conf.USERS:
                    token = self.token_gen.dumps({'username': input_data['user']}).decode('utf-8')

                else:
                    chars = ascii_letters + digits
                    token = ''.join((choice(chars + str(i))) for i in range(190))

                response = self.api.response_class(response=dumps({'success': True, 'token': token}),
                                                   status=200, mimetype='application/json')

            except AssertionError:
                response = self.api.response_class(response=dumps({'success': False, 'message': 'Invalid input'}),
                                                   status=406, mimetype='application/json')

            return response

        # Method used to verify authentication token
        @self.auth.verify_token
        def auth_verify(token):
            try:
                data = self.token_gen.loads(token)

                if 'username' in data:
                    return data['username']

                return True

            except BadSignature:
                return False

        # Route used to process a rut consult in the web portal
        @self.api.route('/api/consult-rut', methods=['POST'])
        @self.auth.login_required()
        def taxpayer():
            logging.info(f'App invoked. data = [user: "{self.auth.current_user()}", route: "/consult-rut"]')
            input_data = request.get_json()

            try:
                # Verification of correct input for the request
                assert 'rut' in input_data.keys() and 'validationDigit' in input_data.keys()
                # Main function for the process
                data = self.web.get_taxpayer_data([input_data['rut'], input_data['validationDigit']])

                if data is not None:
                    response = self.api.response_class(response=dumps(data), status=200, mimetype='application/json')

                else:
                    # This trigger when the RUT is not valid
                    logging.info('Data input not valid.')
                    response = self.api.response_class(response=dumps({'success': False, 'message': 'Invalid rut'}),
                                                       status=406, mimetype='application/json')

            except AssertionError:
                logging.info('Data input not valid.')
                response = self.api.response_class(response=dumps({'success': False, 'message': 'Invalid input'}),
                                                   status=406, mimetype='application/json')

            return response  # Sending result to the client

        # Route used to process a run consult in the web portal
        @self.api.route('/api/certificates', methods=['POST'])
        @self.auth.login_required()
        def certificates():
            logging.info(f'App invoked. data = [user: "{self.auth.current_user()}", route: "/certificates-consult"]')
            input_data = request.get_json()

            try:
                # Verification of correct input for the request
                assert 'run' in input_data.keys() and 'validationDigit' in input_data.keys()
                # Main function for the process
                data = self.web.get_certificates_by_run([input_data['run'], input_data['validationDigit']])

                if data is not None:
                    if data == 'NORUN':
                        # This trigger when invalid RUN given or no result obtained from portal
                        logging.info('Data input not valid.')
                        response = self.api.response_class(response=dumps({'success': False, 'message': 'Invalid RUN'}),
                                                           status=406, mimetype='application/json')

                    else:
                        response = self.api.response_class(response=dumps(data), status=200,
                                                           mimetype='application/json')

                else:
                    # This trigger when something went wrong in the process
                    logging.error('Something happened and aborted /certificates process.')
                    response = self.api.response_class(response=dumps({'success': False,
                                                                       'message': 'Something went wrong'}),
                                                       status=406, mimetype='application/json')

            except AssertionError:
                logging.info('Data input not valid.')
                response = self.api.response_class(response=dumps({'success': False, 'message': 'Invalid input'}),
                                                   status=406, mimetype='application/json')

            return response  # Sending result to the client

        # Route used to process a rut download of certificates on the web portal
        @self.api.route('/api/download-certificates', methods=['POST'])
        @self.auth.login_required()
        def business_certificates():
            logging.info(
                f'App invoked. data = [user: "{self.auth.current_user()}", route: "/download-certificates"]')
            input_data = request.get_json()

            try:
                # Verification of correct input for the request
                assert 'rut' in input_data.keys()
                # Main function for the process
                data = self.web.get_certificates_by_rut([input_data['rut']])

                if data is not None:
                    if data == 'NORUT':
                        # This trigger when invalid RUN given or no result obtained from portal
                        logging.info('Data input not valid.')
                        response = self.api.response_class(
                            response=dumps({'success': False, 'message': 'Invalid RUT'}),
                            status=406, mimetype='application/json')

                    else:
                        response = self.api.response_class(response=dumps(data), status=200,
                                                           mimetype='application/json')

                else:
                    # This trigger when something went wrong in the process
                    logging.error('Something happened and aborted /download-certificates process.')
                    response = self.api.response_class(response=dumps({'success': False,
                                                                       'message': 'Something went wrong'}),
                                                       status=406, mimetype='application/json')

            except AssertionError:
                logging.info('Data input not valid.')
                response = self.api.response_class(response=dumps({'success': False, 'message': 'Invalid input'}),
                                                   status=406, mimetype='application/json')

            return response  # Sending result to the client

        logging.info('Application served.')
        self.api.run(host='0.0.0.0', port=conf.SERVING_PORT)
