from __future__ import unicode_literals

import decimal
import json


class Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(Encoder, self).default(o)
