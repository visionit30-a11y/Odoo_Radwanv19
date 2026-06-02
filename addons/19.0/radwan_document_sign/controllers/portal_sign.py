# -*- coding: utf-8 -*-

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request
from werkzeug.exceptions import NotFound


class RadwanDocumentSignPortal(http.Controller):
    @http.route("/radwan/sign/<string:token>", type="http", auth="public")
    def sign_document(self, token, **kwargs):
        sign_request = self._get_request(token)
        return request.render(
            "radwan_document_sign.portal_sign_page",
            {
                "sign_request": sign_request,
                "error": kwargs.get("error"),
                "csrf_token": request.csrf_token(),
            },
        )

    @http.route(
        "/radwan/sign/<string:token>/submit",
        type="http",
        auth="public",
        methods=["POST"],
    )
    def submit_signature(self, token, **post):
        sign_request = self._get_request(token)
        try:
            sign_request._portal_sign(
                post.get("signature_data"),
                signer_name=post.get("signer_name"),
                signer_email=post.get("signer_email"),
                ip=request.httprequest.remote_addr,
                user_agent=request.httprequest.user_agent.string,
            )
        except UserError as error:
            return request.render(
                "radwan_document_sign.portal_sign_page",
                {
                    "sign_request": sign_request,
                    "error": error.args[0],
                    "csrf_token": request.csrf_token(),
                },
            )
        return request.render(
            "radwan_document_sign.portal_sign_success",
            {"sign_request": sign_request},
        )

    def _get_request(self, token):
        sign_request = request.env["radwan.document.sign.request"].sudo().search(
            [("token", "=", token)],
            limit=1,
        )
        if not sign_request:
            raise NotFound()
        return sign_request
