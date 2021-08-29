import json
from urllib.parse import urlencode

from django.http import HttpResponse


class BluetoothPrint:
    def __init__(self):
        self._index = 0
        self._instructions = {}

    def _add_item(self, item):
        self._instructions[str(self._index)] = item
        self._index += 1

    def add_text(self, text):
        self._add_item(
            {
                "type": 0,
                "content": str(text),
                "bold": 0,
                "align": 1,
                "format": 0,
            }
        )

    def add_barcode(self, code):
        self._add_item(
            {
                "type": 1,
                "path": (
                    "https://www.scandit.com/wp-content/themes/scandit/barcode-generator.php?"
                    + urlencode(
                        {
                            "symbology": "itf",
                            "value": code,
                            "size": "200",
                            "ec": "L",
                        }
                    )
                ),
                "align": 1,
            }
        )

    def response(self):
        return HttpResponse(
            json.dumps(self._instructions),
            content_type="application/json",
        )
