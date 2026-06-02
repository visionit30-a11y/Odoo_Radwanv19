# -*- coding: utf-8 -*-

from odoo import fields, models


class RadwanDocumentSignItem(models.Model):
    _name = "radwan.document.sign.item"
    _description = "Document Signature Field"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    request_id = fields.Many2one(
        "radwan.document.sign.request",
        required=True,
        ondelete="cascade",
        index=True,
    )
    document_id = fields.Many2one(related="request_id.document_id", store=True, readonly=True)
    partner_id = fields.Many2one(related="request_id.partner_id", store=True, readonly=True)
    field_type = fields.Selection(
        [
            ("signature", "Signature"),
            ("initial", "Initials"),
            ("date", "Date"),
            ("text", "Text"),
        ],
        default="signature",
        required=True,
    )
    label = fields.Char(default="Signature")
    required = fields.Boolean(default=True)
    page = fields.Integer(default=1, required=True)
    pos_x = fields.Float(default=8.0, string="X (%)", required=True)
    pos_y = fields.Float(default=70.0, string="Y (%)", required=True)
    width = fields.Float(default=28.0, string="Width (%)", required=True)
    height = fields.Float(default=8.0, string="Height (%)", required=True)
    value_text = fields.Char(readonly=True, copy=False)
    signature_image = fields.Binary(attachment=True, readonly=True, copy=False)
    signature_filename = fields.Char(default="signature.png", readonly=True, copy=False)
    signed_date = fields.Datetime(readonly=True, copy=False)
