from __future__ import unicode_literals

import json

import mock
from django.test import Client
from django.test import TestCase
from django.core.urlresolvers import reverse

from .models import Payment, Receipt, ReceiptItem
from .services import MerchantAPI

TEST_TERMINAL_KEY = 'test_key'
TEST_SECRET_KEY = 'test_s_key'
TEST_CHECK_TOKEN = 'test_token'


def get_test_merchant_api():
    return MerchantAPI(terminal_key='test_key', secret_key='test_s_key')


class PaymentsTestCase(TestCase):
    def test_get_token(self):
        api = MerchantAPI(terminal_key=TEST_TERMINAL_KEY, secret_key=TEST_SECRET_KEY)
        self.assertEqual(api._token(dict(Amount=100000, Description='test', OrderId='TokenExample')), TEST_CHECK_TOKEN)

    def test_init_success(self):
        payment = MerchantAPI().init(Payment(amount=100000, description='test', order_id='TokenExample'))

        self.assertTrue(payment.success)
        self.assertEqual(payment.error_code, '0')
        self.assertEqual(payment.status, 'NEW')
        self.assertNotEqual(payment.payment_url, '')
        self.assertNotEqual(payment.payment_id, '')

        self.assertTrue(payment.can_redirect())

    def test_status(self):
        payment = MerchantAPI().init(Payment(amount=100000, description='test', order_id='TokenExample'))

        self.assertTrue(payment.success)

        payment = MerchantAPI().status(payment)

        self.assertEqual(payment.status, 'NEW')

    @mock.patch('tinkoff_payment.views.Notification._merchant_api', get_test_merchant_api())
    def test_notification(self):
        payment = Payment.objects.create(order_id='12', amount=35000, payment_id='22461408')

        notification = {
            'Success': True,
            'TerminalKey': 'test_key',
            'Status': 'CONFIRMED',
            'ExpDate': '',
            'CardId': 'number',
            'Pan': 'num',
            'Amount': 0,
            'PaymentId': 22461408,
            'OrderId': 'id',
            'Token': 'test_token',
            'ErrorCode': '0',
        }

        resp = Client().post(
            reverse('tinkoff_payment:notification'), json.dumps(notification), content_type='application/json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b'OK')

        payment.refresh_from_db()

        self.assertEqual(payment.status, 'CONFIRMED')
        self.assertTrue(payment.success)

    def test_with_receipt(self):
        items = [
            {'name': 'Product1', 'price': 5000, 'quantity': 1},
            {'name': 'Product2', 'price': 7500, 'quantity': 2},
            {'name': 'Product3', 'price': 20000, 'quantity': 1},
        ]

        payment = Payment(order_id='1', amount=40000) \
            .with_receipt(email='user@email.com') \
            .with_items(items)

        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(Receipt.objects.count(), 1)
        self.assertEqual(ReceiptItem.objects.count(), 3)

        MerchantAPI().init(payment)

        print(payment.message)

        self.assertTrue(payment.success)
