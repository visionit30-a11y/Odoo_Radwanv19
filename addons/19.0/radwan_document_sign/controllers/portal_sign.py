# -*- coding: utf-8 -*-

import base64
import re

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
                "preview_url": self._get_request_document_url(sign_request, public=True),
                "error": kwargs.get("error"),
                "csrf_token": request.csrf_token(),
            },
        )

    @http.route("/radwan/sign/request/<int:request_id>/prepare", type="http", auth="user")
    def prepare_fields(self, request_id, **kwargs):
        sign_request = request.env["radwan.document.sign.request"].sudo().browse(request_id).exists()
        if not sign_request:
            raise NotFound()
        sign_request._ensure_default_items()
        return request.render(
            "radwan_document_sign.prepare_sign_fields_page",
            {
                "sign_request": sign_request,
                "preview_url": self._get_request_document_url(sign_request),
                "csrf_token": request.csrf_token(),
            },
        )

    @http.route(
        "/radwan/sign/request/<int:request_id>/items/save",
        type="json",
        auth="user",
    )
    def save_fields(self, request_id, items=None, **kwargs):
        sign_request = request.env["radwan.document.sign.request"].sudo().browse(request_id).exists()
        if not sign_request:
            raise NotFound()
        Item = request.env["radwan.document.sign.item"].sudo()
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
        "/radwan/sign/request/<int:request_id>/document",
        type="http",
        auth="user",
    )
    def preview_document(self, request_id, **kwargs):
        sign_request = request.env["radwan.document.sign.request"].sudo().browse(request_id).exists()
        if not sign_request:
            raise NotFound()
        attachment = self._get_document_attachment(sign_request.document_id)
        if not attachment:
            raise NotFound()
        return self._make_attachment_preview_response(attachment)

    @http.route(
        "/radwan/sign/<string:token>/document",
        type="http",
        auth="public",
    )
    def public_preview_document(self, token, **kwargs):
        sign_request = self._get_request(token)
        attachment = self._get_document_attachment(sign_request.document_id)
        if not attachment:
            raise NotFound()
        return self._make_attachment_preview_response(attachment)

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
                    "preview_url": self._get_request_document_url(sign_request, public=True),
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

    def _get_request_document_url(self, sign_request, public=False):
        attachment = self._get_document_attachment(sign_request.document_id)
        if attachment and public:
            return "/radwan/sign/%s/document" % sign_request.token
        if attachment:
            return "/radwan/sign/request/%s/document" % sign_request.id
        if not public:
            return self._get_document_preview_url(sign_request.document_id)
        return False

    def _get_document_preview_url(self, document):
        document = document.sudo()
        if not document:
            return False
        if "attachment_preview_url" in document._fields:
            preview_url = document.attachment_preview_url
            if preview_url:
                return preview_url
        attachment = self._get_document_attachment(document)
        if attachment:
            return "/web/content/%s?download=false" % attachment.id
        return False

    def _get_document_attachment(self, document):
        document = document.sudo()
        if not document:
            return False
        if "attachment_id" in document._fields and document.attachment_id:
            return document.attachment_id.sudo()
        if "attachment_ids" in document._fields and document.attachment_ids:
            binary_attachments = document.attachment_ids.sudo().filtered(lambda attachment: attachment.type == "binary")
            if binary_attachments:
                return binary_attachments[-1]
        Attachment = request.env["ir.attachment"].sudo()
        attachment = Attachment.search(
            [
                ("res_model", "=", "document.document"),
                ("res_id", "=", document.id),
                ("type", "=", "binary"),
            ],
            order="id desc",
            limit=1,
        )
        if attachment:
            return attachment
        if "content" in document._fields and document.content:
            urls = document.sudo()._get_first_attachment_url() if hasattr(document, "_get_first_attachment_url") else False
            attachment = self._get_attachment_from_url(urls)
            if attachment:
                return attachment
        return False

    def _make_attachment_preview_response(self, attachment):
        attachment = attachment.sudo()
        raw = attachment.raw
        if not raw and attachment.datas:
            raw = base64.b64decode(attachment.datas)
        if not raw:
            raise NotFound()
        filename = (attachment.name or "document").replace('"', "")
        headers = [
            ("Content-Type", attachment.mimetype or "application/octet-stream"),
            ("Content-Disposition", 'inline; filename="%s"' % filename),
        ]
        return request.make_response(raw, headers=headers)

    def _get_attachment_from_url(self, url):
        if not url:
            return False
        match = re.search(r"/web/(?:content|image)/(?:ir\.attachment/)?(\d+)", url)
        if not match:
            match = re.search(r"[?&]id=(\d+)", url)
        if not match:
            return False
        return request.env["ir.attachment"].sudo().browse(int(match.group(1))).exists()
