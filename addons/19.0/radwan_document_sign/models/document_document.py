# -*- coding: utf-8 -*-

import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DocumentDocument(models.Model):
    _inherit = "document.document"

    sign_request_ids = fields.One2many(
        "radwan.document.sign.request",
        "document_id",
        string="Signature Requests",
    )
    sign_request_count = fields.Integer(compute="_compute_sign_request_count")
    sign_state = fields.Selection(
        [
            ("none", "No Signature"),
            ("sent", "Waiting Signature"),
            ("signed", "Signed"),
        ],
        compute="_compute_sign_state",
        store=True,
        string="Signature Status",
    )

    def _compute_sign_request_count(self):
        groups = self.env["radwan.document.sign.request"].read_group(
            [("document_id", "in", self.ids)],
            ["document_id"],
            ["document_id"],
        )
        counts = {}
        for group in groups:
            document_value = group.get("document_id")
            if not document_value:
                continue
            document_id = document_value[0] if isinstance(document_value, tuple) else document_value
            counts[document_id] = group.get("document_id_count", 0)
        for document in self:
            document.sign_request_count = counts.get(document.id, 0)

    @api.depends("sign_request_ids.state")
    def _compute_sign_state(self):
        for document in self:
            requests = document.sign_request_ids
            if any(request.state == "signed" for request in requests):
                document.sign_state = "signed"
            elif any(request.state == "sent" for request in requests):
                document.sign_state = "sent"
            else:
                document.sign_state = "none"

    def action_create_signature_request(self):
        self.ensure_one()
        partner = self.partner_id
        employee = self.employee_id
        attachment = self._get_signature_attachment()
        if not partner and employee:
            for field_name in ("work_contact_id", "address_home_id", "user_partner_id"):
                if field_name in employee._fields and employee[field_name]:
                    partner = employee[field_name]
                    break
            if not partner and employee.user_id:
                partner = employee.user_id.partner_id
        if not partner:
            raise UserError(_("Select a related partner or employee before requesting a signature."))
        if not attachment:
            raise UserError(_("Attach a PDF or binary document before requesting a signature."))
        request = self.env["radwan.document.sign.request"].create({
            "document_id": self.id,
            "attachment_id": attachment.id if attachment else False,
            "partner_id": partner.id,
            "employee_id": employee.id if employee else False,
            "subject": _("Please sign: %s") % (self.display_name,),
        })
        return {
            "type": "ir.actions.act_window",
            "name": _("Signature Request"),
            "res_model": "radwan.document.sign.request",
            "view_mode": "form",
            "res_id": request.id,
            "target": "current",
        }

    def action_view_signature_requests(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Signature Requests"),
            "res_model": "radwan.document.sign.request",
            "view_mode": "list,form",
            "domain": [("document_id", "=", self.id)],
            "context": {"default_document_id": self.id},
        }

    def action_view_signed_signature_files(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Signed Files"),
            "res_model": "radwan.document.sign.request",
            "view_mode": "list,form",
            "domain": [
                ("document_id", "=", self.id),
                ("signed_attachment_id", "!=", False),
            ],
            "context": {"default_document_id": self.id},
        }

    def _get_signature_attachment(self):
        self.ensure_one()
        return self._find_signature_attachment(set())

    def _find_signature_attachment(self, visited):
        self.ensure_one()
        if self.id in visited:
            return self.env["ir.attachment"]
        visited.add(self.id)

        attachment = self._get_direct_signature_attachment()
        if attachment:
            return attachment

        for child in self._get_signature_child_documents():
            attachment = child._find_signature_attachment(visited)
            if attachment:
                return attachment
        return self.env["ir.attachment"]

    def _get_direct_signature_attachment(self):
        self.ensure_one()
        if "attachment_id" in self._fields and self.attachment_id:
            return self.attachment_id.sudo()

        if "attachment_ids" in self._fields and self.attachment_ids:
            binary_attachments = self.attachment_ids.sudo().filtered(
                lambda attachment: attachment.type == "binary"
            )
            if binary_attachments:
                return binary_attachments[-1]

        Attachment = self.env["ir.attachment"].sudo()
        attachment = Attachment.search(
            [
                ("res_model", "=", "document.document"),
                ("res_id", "=", self.id),
                ("type", "=", "binary"),
            ],
            order="id desc",
            limit=1,
        )
        if attachment:
            return attachment

        url = False
        if hasattr(self, "_get_first_attachment_url"):
            url = self.sudo()._get_first_attachment_url()
        elif "content" in self._fields and self.content:
            url = self._extract_signature_attachment_url(self.content)
        return self._get_signature_attachment_from_url(url)

    def _get_signature_child_documents(self):
        self.ensure_one()
        Document = self.env["document.document"].sudo()
        children = Document.browse()

        for field_name in ("child_ids", "children_ids", "document_child_ids", "document_ids"):
            if field_name not in self._fields:
                continue
            value = self.sudo()[field_name]
            if hasattr(value, "_name") and value._name == "document.document":
                children |= value.sudo()

        if "parent_id" in self._fields:
            children |= Document.search([("parent_id", "=", self.id)], order="id desc")

        return children.exists()

    def _extract_signature_attachment_url(self, content):
        urls = re.findall(
            r"""(?:href|src|data)=["']([^"']+)["']""",
            content or "",
            flags=re.IGNORECASE,
        )
        urls.extend(
            re.findall(
                r"""(/web/(?:content|image)[^"' <>\)]*)""",
                content or "",
                flags=re.IGNORECASE,
            )
        )
        for url in urls:
            if "/web/content" in url or "/web/image" in url:
                return url
        return False

    def _get_signature_attachment_from_url(self, url):
        if not url:
            return self.env["ir.attachment"]
        match = re.search(r"/web/(?:content|image)/(?:ir\.attachment/)?(\d+)", url)
        if not match:
            match = re.search(r"[?&]id=(\d+)", url)
        if not match:
            return self.env["ir.attachment"]
        return self.env["ir.attachment"].sudo().browse(int(match.group(1))).exists()
