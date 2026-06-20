# -*- coding: utf-8 -*-

import base64
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request
from markupsafe import Markup
from werkzeug.exceptions import NotFound


class RadwanDocumentSignPortal(http.Controller):
    @http.route("/radwan/sign/<string:token>", type="http", auth="public")
    def sign_document(self, token, **kwargs):
        sign_request = self._get_request(token)
        sign_request.sudo()._ensure_document_attachment()
        sign_request.sudo()._ensure_default_items()
        return request.render(
            "radwan_document_sign.portal_sign_page",
            {
                "sign_request": sign_request,
                "preview_url": self._get_request_document_url(sign_request, public=True),
                "document_html": self._get_document_html(sign_request.document_id),
                "error": kwargs.get("error"),
                "csrf_token": request.csrf_token(),
            },
        )

    @http.route("/radwan/sign/request/<int:request_id>/prepare", type="http", auth="user")
    def prepare_fields(self, request_id, **kwargs):
        sign_request = request.env["radwan.document.sign.request"].sudo().browse(request_id).exists()
        if not sign_request:
            raise NotFound()
        sign_request._ensure_document_attachment()
        sign_request._ensure_default_items()
        return request.render(
            "radwan_document_sign.prepare_sign_fields_page",
            {
                "sign_request": sign_request,
                "preview_url": self._get_request_document_url(sign_request),
                "document_html": self._get_document_html(sign_request.document_id),
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
        sign_request._ensure_document_attachment()
        attachment = self._get_request_attachment(sign_request)
        if not attachment:
            raise NotFound()
        return self._make_attachment_preview_response(attachment)

    @http.route(
        "/radwan/sign/request/<int:request_id>/signed",
        type="http",
        auth="user",
    )
    def preview_signed_document(self, request_id, **kwargs):
        sign_request = request.env["radwan.document.sign.request"].sudo().browse(request_id).exists()
        if not sign_request:
            raise NotFound()
        attachment = sign_request._get_signed_attachment()
        if not attachment:
            raise NotFound()
        return self._make_attachment_preview_response(attachment, download=self._is_download(kwargs))

    @http.route(
        "/radwan/sign/<string:token>/document",
        type="http",
        auth="public",
    )
    def public_preview_document(self, token, **kwargs):
        sign_request = self._get_request(token)
        sign_request.sudo()._ensure_document_attachment()
        attachment = self._get_request_attachment(sign_request)
        if not attachment:
            raise NotFound()
        return self._make_attachment_preview_response(attachment)

    @http.route(
        "/radwan/sign/<string:token>/signed",
        type="http",
        auth="public",
    )
    def public_preview_signed_document(self, token, **kwargs):
        sign_request = self._get_request(token)
        if sign_request.state != "signed":
            raise NotFound()
        attachment = sign_request._get_signed_attachment()
        if not attachment:
            raise NotFound()
        return self._make_attachment_preview_response(attachment, download=self._is_download(kwargs))

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
                    "document_html": self._get_document_html(sign_request.document_id),
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

    def _get_document_html(self, document):
        if not document or "content" not in document._fields or not document.content:
            return False
        return Markup(document.sudo().content)

    def _get_request_document_url(self, sign_request, public=False):
        attachment = self._get_request_attachment(sign_request)
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
        preview_url = self._get_content_preview_url(document)
        if preview_url:
            return preview_url
        attachment = self._get_document_attachment(document)
        if attachment:
            return "/web/content/%s?download=false" % attachment.id
        return False

    def _get_request_attachment(self, sign_request):
        sign_request.sudo()._ensure_document_attachment()
        if "attachment_id" in sign_request._fields and sign_request.attachment_id:
            return sign_request.attachment_id.sudo()
        return self._get_document_attachment(sign_request.document_id)

    def _get_document_attachment(self, document, visited=None):
        document = document.sudo()
        if not document:
            return False
        visited = visited or set()
        if document.id in visited:
            return False
        visited.add(document.id)

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
            url = self._get_content_preview_url(document)
            attachment = self._get_attachment_from_url(url)
            if attachment:
                return attachment
        for child in self._get_document_children(document):
            attachment = self._get_document_attachment(child, visited)
            if attachment:
                return attachment
        return False

    def _get_document_children(self, document):
        Document = request.env["document.document"].sudo()
        children = Document.browse()
        for field_name in ("child_ids", "children_ids", "document_child_ids", "document_ids"):
            if field_name not in document._fields:
                continue
            value = document.sudo()[field_name]
            if hasattr(value, "_name") and value._name == "document.document":
                children |= value.sudo()
        if "parent_id" in document._fields:
            children |= Document.search([("parent_id", "=", document.id)], order="id desc")
        return children.exists()

    def _make_attachment_preview_response(self, attachment, download=False):
        attachment = attachment.sudo()
        raw = attachment.raw
        if not raw and attachment.datas:
            raw = base64.b64decode(attachment.datas)
        if not raw:
            raise NotFound()
        filename = (attachment.name or "document").replace('"', "")
        disposition = "attachment" if download else "inline"
        headers = [
            ("Content-Type", attachment.mimetype or "application/octet-stream"),
            ("Content-Disposition", '%s; filename="%s"' % (disposition, filename)),
        ]
        return request.make_response(raw, headers=headers)

    def _is_download(self, kwargs):
        return str(kwargs.get("download") or "").lower() in ("1", "true", "yes")

    def _get_attachment_from_url(self, url):
        if not url:
            return False
        match = re.search(r"/web/(?:content|image)/(?:ir\.attachment/)?(\d+)", url)
        if not match:
            match = re.search(r"[?&]id=(\d+)", url)
        if not match:
            return False
        return request.env["ir.attachment"].sudo().browse(int(match.group(1))).exists()

    def _get_content_preview_url(self, document):
        if not document or "content" not in document._fields or not document.content:
            return False
        if hasattr(document, "_get_first_attachment_url"):
            preview_url = document.sudo()._get_first_attachment_url()
            if preview_url:
                return preview_url
        for url in self._extract_preview_urls(document.content):
            if self._is_previewable_url(url):
                return self._normalize_preview_url(url)
        return False

    def _extract_preview_urls(self, content):
        content = content or ""
        urls = []
        urls.extend(
            re.findall(
                r"""(?:href|src|data)=["']([^"']+)["']""",
                content,
                flags=re.IGNORECASE,
            )
        )
        urls.extend(
            re.findall(
                r"""(/web/(?:content|image)[^"' <>\)]*)""",
                content,
                flags=re.IGNORECASE,
            )
        )
        return [url for url in urls if url]

    def _is_previewable_url(self, url):
        return bool(url and ("/web/content" in url or "/web/image" in url))

    def _normalize_preview_url(self, url):
        split_url = urlsplit(url)
        query = [
            (key, value)
            for key, value in parse_qsl(split_url.query, keep_blank_values=True)
            if key != "download"
        ]
        return urlunsplit(
            (
                split_url.scheme,
                split_url.netloc,
                split_url.path,
                urlencode(query),
                split_url.fragment,
            )
        )
