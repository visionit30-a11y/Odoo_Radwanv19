# -*- coding: utf-8 -*-

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

    def _portal_sign(self, signature_data, signer_name=False, signer_email=False, ip=False, user_agent=False):
        self.ensure_one()
        if self.state in ("signed", "cancelled"):
            raise UserError(_("This signature request is no longer open."))
        if not signature_data or "," not in signature_data:
            raise UserError(_("Please draw your signature before submitting."))
        mime, payload = signature_data.split(",", 1)
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
