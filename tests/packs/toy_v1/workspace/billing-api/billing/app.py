"""Minimal HTTP API: POST /invoices, GET /invoices/<number>."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, HTTPServer

from billing.invoices import Invoice, LineItem, total
from billing.validation import ValidationError, require_fields

INVOICES: dict[str, Invoice] = {}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        if self.path != "/invoices":
            return self._send(404, {"error": "not found"})
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        try:
            require_fields(payload, "number", "customer_email", "currency", "items")
        except ValidationError as e:
            return self._send(422, {"error": str(e)})
        inv = Invoice(
            number=payload["number"], customer_email=payload["customer_email"],
            currency=payload["currency"], issued=date.today(), due=date.today(),
            items=[LineItem(i["description"], int(i["quantity"]), Decimal(str(i["unit_price"])))
                   for i in payload["items"]],
        )
        INVOICES[inv.number] = inv
        self._send(201, {"number": inv.number, "total": str(total(inv))})

    def do_GET(self) -> None:
        inv = INVOICES.get(self.path.removeprefix("/invoices/"))
        if inv is None:
            return self._send(404, {"error": "not found"})
        self._send(200, {"number": inv.number, "total": str(total(inv))})


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
