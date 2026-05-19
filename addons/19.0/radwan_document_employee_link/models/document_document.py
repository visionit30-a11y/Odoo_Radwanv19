# -*- coding: utf-8 -*-

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from lxml import html
from lxml.etree import ParserError

from odoo import api, fields, models
from odoo.exceptions import UserError


class DocumentDocument(models.Model):
    _inherit = "document.document"

    related_to = fields.Selection(
        selection=[
            ("employee", "Employee"),
            ("partner", "Partner"),
        ],
        string="Related To Employee/Partner",
        tracking=True,
    )
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        tracking=True,
        index=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        tracking=True,
        index=True,
    )
    attachment_preview_url = fields.Char(
        string="Attachment Preview URL",
        compute="_compute_attachment_preview_url",
    )

    @api.depends("content")
    def _compute_attachment_preview_url(self):
        for document in self:
            document.attachment_preview_url = document._get_first_attachment_url()

    @api.onchange("related_to")
    def _onchange_related_to(self):
        if self.related_to == "employee":
            self.partner_id = False
        elif self.related_to == "partner":
            self.employee_id = False
        else:
            self.employee_id = False
            self.partner_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._prepare_related_values(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._prepare_related_values(vals)
        return super().write(vals)

    def action_preview_attachment(self):
        self.ensure_one()
        url = self._get_first_attachment_url()
        if not url:
            raise UserError(self.env._("No previewable attachment was found."))
        return {
            "type": "ir.actions.act_url",
            "name": self.env._("Attachment Preview"),
            "target": "new",
            "url": url,
        }

    @api.model
    def _prepare_related_values(self, vals):
        if vals.get("related_to") == "employee":
            vals["partner_id"] = False
        elif vals.get("related_to") == "partner":
            vals["employee_id"] = False
        elif vals.get("related_to") is False:
            vals["employee_id"] = False
            vals["partner_id"] = False

    def _get_first_attachment_url(self):
        self.ensure_one()
        if not self.content:
            return False

        try:
            document = html.fragment_fromstring(self.content, create_parent=True)
        except (ParserError, TypeError, ValueError):
            return False

        for link in document.xpath(".//a[@href]"):
            href = link.get("href")
            if self._is_previewable_attachment_url(href):
                return self._normalize_preview_url(href)
        return False

    @api.model
    def _is_previewable_attachment_url(self, url):
        if not url:
            return False
        return "/web/content" in url or "/web/image" in url

    @api.model
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
