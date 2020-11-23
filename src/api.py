import os
import logging
from json import dumps
from random import choice
from flask import Flask, request
from flask_httpauth import HTTPTokenAuth
from string import ascii_letters, digits
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature

import config as conf
from vendor.BrowserModule import WebActions


class Api:

    # Basic configuration for the app
    api = Flask(conf.APP_NAME)
    auth = HTTPTokenAuth('Bearer')

    def __init__(self):
        self.web = WebActions(conf.DRIVER_PATH, os.getcwd())
        logging.info('Web service initialized')
        self.token_gen = Serializer(conf.APP_SECRET, conf.TTE)
        logging.info('Token generator initialized')

    def serve(self):
        # Route for login (needed for authentication)
        @self.api.route('/api/sing-in', methods=['POST'])
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
        def consult():
            logging.info(f'App invoked. data = [user: "{self.auth.current_user()}", route: "/consult-rut"]')
            input_data = request.get_json()

            try:
                # Verification of correct input for the request
                assert 'rut' in input_data.keys() and 'validationDigit' in input_data.keys()
                # Main function for the process
                data = None
                try:
                    data = self.web.get_taxpayer_data([input_data['rut'], input_data['validationDigit']])

                    if data is not None:
                        # This trigger when the RUT is not valid
                        logging.info('Data input not valid.')
                        response = self.api.response_class(response=dumps(data), status=200, mimetype='application/json')

                    else:
                        response = self.api.response_class(response=dumps({'success': False, 'message': 'Invalid rut'}),
                                                        status=406, mimetype='application/json')

                except Exception as ex:
                    response = self.api.response_class(response=dumps({'success': False, 'message': str(ex)}),
                                                       status=406, mimetype='application/json')

            except AssertionError:
                logging.info('Data input not valid.')
                response = self.api.response_class(response=dumps({'success': False, 'message': 'Invalid input'}),
                                                   status=406, mimetype='application/json')

            return response  # Sending result to the client

        logging.info('Application served.')
        self.api.run(host='0.0.0.0', port=conf.SERVING_PORT)
