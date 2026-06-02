# -*- coding: utf-8 -*-

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request
from werkzeug.exceptions import NotFound


class RadwanDocumentSignPortal(http.Controller):
    @http.route("/radwan/sign/<string:token>", type="http", auth="public")
    def sign_document(self, token, **kwargs):
        sign_request = self._get_request(token)
        sign_request.sudo()._ensure_default_items()
        return request.render(
            "radwan_document_sign.portal_sign_page",
            {
                "sign_request": sign_request,
                "preview_url": sign_request.document_id.attachment_preview_url,
                "error": kwargs.get("error"),
                "csrf_token": request.csrf_token(),
            },
        )

    @http.route("/radwan/sign/request/<int:request_id>/prepare", type="http", auth="user")
    def prepare_fields(self, request_id, **kwargs):
        sign_request = request.env["radwan.document.sign.request"].browse(request_id).exists()
        if not sign_request:
            raise NotFound()
        sign_request._ensure_default_items()
        return request.render(
            "radwan_document_sign.prepare_sign_fields_page",
            {
                "sign_request": sign_request,
                "preview_url": sign_request.document_id.attachment_preview_url,
                "csrf_token": request.csrf_token(),
            },
        )

    @http.route(
        "/radwan/sign/request/<int:request_id>/items/save",
        type="json",
        auth="user",
    )
    def save_fields(self, request_id, items=None, **kwargs):
        sign_request = request.env["radwan.document.sign.request"].browse(request_id).exists()
        if not sign_request:
            raise NotFound()
        Item = request.env["radwan.document.sign.item"]
        seen_ids = []
        for sequence, values in enumerate(items or [], start=1):
            item_id = values.get("id")
            vals = {
                "request_id": sign_request.id,
                "sequence": sequence * 10,
                "field_type": values.get("field_type") or "signature",
                "label": values.get("label") or "Signature",
                "required": bool(values.get("required", True)),
                "page": int(values.get("page") or 1),
                "pos_x": float(values.get("pos_x") or 0),
                "pos_y": float(values.get("pos_y") or 0),
                "width": float(values.get("width") or 20),
                "height": float(values.get("height") or 8),
            }
            if item_id:
                item = Item.browse(int(item_id)).exists()
                if item and item.request_id == sign_request:
                    item.write(vals)
                    seen_ids.append(item.id)
                    continue
            item = Item.create(vals)
            seen_ids.append(item.id)
        sign_request.item_ids.filtered(lambda item: item.id not in seen_ids).unlink()
        return {"ok": True, "count": len(seen_ids)}

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
                item_payload=post.get("item_payload"),
            )
        except UserError as error:
            return request.render(
                "radwan_document_sign.portal_sign_page",
                {
                    "sign_request": sign_request,
                    "preview_url": sign_request.document_id.attachment_preview_url,
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
