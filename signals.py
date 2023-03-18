from __future__ import unicode_literals

import django.dispatch

payment_update = django.dispatch.Signal(providing_args=['payment'])
