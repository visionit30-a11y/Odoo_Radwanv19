# -*- coding: utf-8 -*-

import json
import secrets

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class RadwanDocumentSignRequest(models.Model):
    _name = "radwan.document.sign.request"
    _description = "Document Electronic Signature Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(default="New", readonly=True, copy=False, tracking=True)
    document_id = fields.Many2one(
        "document.document",
        required=True,
        ondelete="cascade",
        tracking=True,
        index=True,
    )
    partner_id = fields.Many2one("res.partner", string="Signer", required=True, tracking=True)
    employee_id = fields.Many2one("hr.employee", tracking=True)
    requester_id = fields.Many2one(
        "res.users",
        default=lambda self: self.env.user,
        readonly=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    token = fields.Char(readonly=True, copy=False, index=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("sent", "Sent"),
            ("signed", "Signed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    subject = fields.Char(default=lambda self: _("Please sign this document"))
    message = fields.Text()
    sent_date = fields.Datetime(readonly=True, copy=False)
    signed_date = fields.Datetime(readonly=True, copy=False)
    signer_name = fields.Char(readonly=True, copy=False)
    signer_email = fields.Char(readonly=True, copy=False)
    signature_image = fields.Binary(string="Signature", attachment=True, readonly=True, copy=False)
    signature_filename = fields.Char(default="signature.png", readonly=True, copy=False)
    signer_ip = fields.Char(readonly=True, copy=False)
    signer_user_agent = fields.Char(readonly=True, copy=False)
    access_url = fields.Char(compute="_compute_access_url")
    item_ids = fields.One2many(
        "radwan.document.sign.item",
        "request_id",
        string="Signing Fields",
    )
    item_count = fields.Integer(compute="_compute_item_count")

    _token_unique = models.Constraint(
        "unique(token)",
        "Signature access token must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"].sudo()
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = sequence.next_by_code("radwan.document.sign.request") or "New"
            vals.setdefault("token", secrets.token_urlsafe(32))
        return super().create(vals_list)

    @api.depends("token")
    def _compute_access_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
        for request in self:
            request.access_url = (
                "%s/radwan/sign/%s" % (base_url.rstrip("/"), request.token)
                if request.token
                else False
            )

    def _compute_item_count(self):
        for request in self:
            request.item_count = len(request.item_ids)

    def action_send(self):
        for request in self:
            if not request.partner_id.email:
                raise UserError(_("The signer must have an email address."))
            request.write({
                "state": "sent",
                "sent_date": fields.Datetime.now(),
            })
            request._send_signature_email()

    def action_cancel(self):
        self.filtered(lambda item: item.state not in ("signed", "cancelled")).write({
            "state": "cancelled",
        })

    def action_open_portal(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "name": _("Signature Page"),
            "target": "new",
            "url": self.access_url,
        }

    def action_prepare_fields(self):
        self.ensure_one()
        self._ensure_default_items()
        return {
            "type": "ir.actions.act_url",
            "name": _("Prepare Signing Fields"),
            "target": "new",
            "url": "/radwan/sign/request/%s/prepare" % self.id,
        }

    def action_reset_to_draft(self):
        self.filtered(lambda item: item.state != "signed").write({"state": "draft"})

    def _send_signature_email(self):
        self.ensure_one()
        body = self.env["ir.qweb"]._render(
            "radwan_document_sign.mail_signature_request_body",
            {"request": self},
            minimal_qcontext=True,
        )
        self.env["mail.mail"].sudo().create({
            "subject": self.subject or _("Please sign this document"),
            "body_html": body,
            "email_to": self.partner_id.email,
            "auto_delete": True,
        }).send()

    def _ensure_default_items(self):
        for request in self:
            if request.item_ids:
                continue
            self.env["radwan.document.sign.item"].create({
                "request_id": request.id,
                "field_type": "signature",
                "label": _("Signature"),
                "required": True,
                "page": 1,
                "pos_x": 8.0,
                "pos_y": 70.0,
                "width": 28.0,
                "height": 8.0,
            })

    def _portal_sign(
        self,
        signature_data=False,
        signer_name=False,
        signer_email=False,
        ip=False,
        user_agent=False,
        item_payload=False,
    ):
        self.ensure_one()
        if self.state in ("signed", "cancelled"):
            raise UserError(_("This signature request is no longer open."))
        item_values = self._parse_item_payload(item_payload)
        first_signature = signature_data
        if self.item_ids:
            self._apply_item_payload(item_values)
            first_signature = first_signature or self._get_first_signature_data(item_values)
        if not first_signature or "," not in first_signature:
            raise UserError(_("Please draw your signature before submitting."))
        mime, payload = first_signature.split(",", 1)
        if "image/png" not in mime:
            raise UserError(_("Only PNG signatures are supported."))
        self.write({
            "state": "signed",
            "signature_image": payload,
            "signature_filename": "%s-signature.png" % (self.name or "document"),
            "signed_date": fields.Datetime.now(),
            "signer_name": signer_name or self.partner_id.name,
            "signer_email": signer_email or self.partner_id.email,
            "signer_ip": ip,
            "signer_user_agent": user_agent,
        })
        if hasattr(self.document_id, "message_post"):
            self.document_id.message_post(
                body=_("Document signed by %s.") % (self.signer_name or self.partner_id.name)
            )
        return True

    def _parse_item_payload(self, item_payload):
        if not item_payload:
            return {}
        if isinstance(item_payload, dict):
            return item_payload
        try:
            return json.loads(item_payload)
        except (TypeError, ValueError):
            return {}

    def _get_first_signature_data(self, item_values):
        for value in item_values.values():
            if isinstance(value, dict) and value.get("signature_data"):
                return value["signature_data"]
        return False

    def _apply_item_payload(self, item_values):
        missing = []
        now = fields.Datetime.now()
        for item in self.item_ids:
            value = item_values.get(str(item.id)) or {}
            if item.field_type in ("signature", "initial"):
                signature_data = value.get("signature_data")
                if item.required and not signature_data:
                    missing.append(item.label or item.field_type)
                    continue
                if signature_data and "," in signature_data:
                    mime, payload = signature_data.split(",", 1)
                    if "image/png" not in mime:
                        raise UserError(_("Only PNG signatures are supported."))
                    item.write({
                        "signature_image": payload,
                        "signature_filename": "%s-%s.png" % (self.name or "sign", item.id),
                        "signed_date": now,
                    })
            else:
                text_value = value.get("value")
                if item.required and not text_value:
                    missing.append(item.label or item.field_type)
                    continue
                item.write({
                    "value_text": text_value,
                    "signed_date": now,
                })
        if missing:
            raise UserError(_("Please complete required fields: %s") % ", ".join(missing))
