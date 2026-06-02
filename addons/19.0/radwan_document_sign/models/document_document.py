# -*- coding: utf-8 -*-

from odoo import _, fields, models
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
        if not partner and employee:
            for field_name in ("work_contact_id", "address_home_id", "user_partner_id"):
                if field_name in employee._fields and employee[field_name]:
                    partner = employee[field_name]
                    break
            if not partner and employee.user_id:
                partner = employee.user_id.partner_id
        if not partner:
            raise UserError(_("Select a related partner or employee before requesting a signature."))
        request = self.env["radwan.document.sign.request"].create({
            "document_id": self.id,
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
