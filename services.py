from __future__ import unicode_literals

import hashlib
import json

import requests

from .utils import Encoder
from .models import Payment
from .settings import get_config


class PaymentHTTPException(Exception):
    pass


class MerchantAPI(object):
    _terminal_key = None
    _secret_key = None

    def __init__(self, terminal_key=None, secret_key=None):
        self._terminal_key = terminal_key
        self._secret_key = secret_key

    @property
    def secret_key(self):
        if not self._secret_key:
            self._secret_key = get_config()['SECRET_KEY']
        return self._secret_key

    @property
    def terminal_key(self):
        if not self._terminal_key:
            self._terminal_key = get_config()['TERMINAL_KEY']
        return self._terminal_key

    def _request(self, url, method, data):
        url = get_config()['URLS'][url]

        data.update({
            'TerminalKey': self.terminal_key,
            'Token': self._token(data),
        })

        pay_request = method(url, data=json.dumps(data, cls=Encoder), headers={'Content-Type': 'application/json'})

        if pay_request.status_code != 200:
            raise PaymentHTTPException('bad status code')

        return pay_request

    def _token(self, data):
        base = [
            ['Password', self.secret_key],
        ]

        if 'TerminalKey' not in data:
            base.append(['TerminalKey', self.terminal_key])

        for name_token, value_token in data.items():
            if name_token == 'Token':
                continue
            if isinstance(value_token, bool):
                base.append([name_token, str(value_token).lower()])
            elif not isinstance(value_token, list) or not isinstance(value_token, dict):
                base.append([name_token, value_token])

        base.sort(key=lambda i: i[0])
        values = ''.join(map(lambda i: str(i[1]), base))

        m = hashlib.sha256()
        m.update(values.encode())
        return m.hexdigest()

    @staticmethod
    def update_payment_from_response(payment, response):
        for resp_field, model_field in Payment.RESPONSE_FIELDS.items():
            if resp_field in response:
                setattr(payment, model_field, response.get(resp_field))

        return payment

    def token_correct(self, token, data):
        return token == self._token(data)

    def init(self, payment):
        response = self._request('INIT', requests.post, payment.to_json()).json()
        return self.update_payment_from_response(payment, response)

    def status(self, payment):
        response = self._request('GET_STATE', requests.post, {'PaymentId': payment.payment_id}).json()
        return self.update_payment_from_response(payment, response)

    def cancel(self, payment):
        response = self._request('CANCEL', requests.post, {'PaymentId': payment.payment_id}).json()
        return self.update_payment_from_response(payment, response)
