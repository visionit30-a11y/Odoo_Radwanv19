# -*- coding: utf-8 -*-

import base64
import json
import logging
import secrets
from io import BytesIO

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


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
    attachment_id = fields.Many2one(
        "ir.attachment",
        string="Document Attachment",
        readonly=True,
        copy=False,
        help="The actual PDF or binary attachment used for preview and signing.",
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
    signed_attachment_id = fields.Many2one(
        "ir.attachment",
        string="Signed File",
        readonly=True,
        copy=False,
        help="Signed document file generated after the signer completes the request.",
    )
    signed_document_id = fields.Many2one(
        "document.document",
        string="Signed Document Record",
        readonly=True,
        copy=False,
        help="Document Management record created for the signed file.",
    )
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
            if vals.get("document_id") and not vals.get("attachment_id"):
                vals["attachment_id"] = self._get_document_signature_attachment_id(vals["document_id"])
        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)
        if vals.get("document_id") and "attachment_id" not in vals:
            self._ensure_document_attachment()
        return result

    @api.onchange("document_id")
    def _onchange_document_id(self):
        for request in self:
            if request.document_id and not request.attachment_id:
                request.attachment_id = request.document_id._get_signature_attachment()

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
            request._ensure_document_attachment(required=True)
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
        self._ensure_document_attachment(required=True)
        return {
            "type": "ir.actions.act_url",
            "name": _("Signature Page"),
            "target": "new",
            "url": self.access_url,
        }

    def action_prepare_fields(self):
        self.ensure_one()
        self._ensure_document_attachment(required=True)
        self._ensure_default_items()
        return {
            "type": "ir.actions.act_url",
            "name": _("Prepare Signing Fields"),
            "target": "new",
            "url": "/radwan/sign/request/%s/prepare" % self.id,
        }

    def action_reset_to_draft(self):
        self.filtered(lambda item: item.state != "signed").write({"state": "draft"})

    def action_preview_signed_file(self):
        self.ensure_one()
        if not self._get_signed_attachment():
            raise UserError(_("No signed file is available yet."))
        return {
            "type": "ir.actions.act_url",
            "name": _("Signed File"),
            "target": "new",
            "url": "/radwan/sign/request/%s/signed" % self.id,
        }

    def action_download_signed_file(self):
        self.ensure_one()
        if not self._get_signed_attachment():
            raise UserError(_("No signed file is available yet."))
        return {
            "type": "ir.actions.act_url",
            "name": _("Download Signed File"),
            "target": "self",
            "url": "/radwan/sign/request/%s/signed?download=1" % self.id,
        }

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

    @api.model
    def _get_document_signature_attachment_id(self, document_id):
        document = self.env["document.document"].sudo().browse(document_id).exists()
        if not document:
            return False
        attachment = document._get_signature_attachment()
        return attachment.id if attachment else False

    def _ensure_document_attachment(self, required=False):
        for request in self:
            if request.attachment_id:
                continue
            attachment = request.document_id._get_signature_attachment() if request.document_id else False
            if attachment:
                request.sudo().write({"attachment_id": attachment.id})
            elif required:
                raise UserError(_(
                    "No previewable document attachment was found. Please attach a PDF or binary file to the document before preparing the signature fields."
                ))

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
        self._create_signed_file_records()
        return True

    def _get_signed_attachment(self):
        self.ensure_one()
        return self.signed_attachment_id

    def _create_signed_file_records(self):
        Attachment = self.env["ir.attachment"].sudo()
        Document = self.env["document.document"].sudo()
        for request in self:
            request._ensure_document_attachment()
            source = request.attachment_id or request.document_id._get_signature_attachment()
            if not source:
                continue
            raw = source.raw
            if not raw and source.datas:
                raw = base64.b64decode(source.datas)
            if not raw:
                continue

            if request.signed_attachment_id:
                request.signed_attachment_id.sudo().unlink()
            signed_raw = request._render_signed_pdf(raw, source)

            filename = source.name or request.document_id.display_name or request.name or _("Signed Document")
            if not filename.lower().startswith("signed - "):
                filename = _("Signed - %s") % filename
            attachment = Attachment.create({
                "name": filename,
                "type": "binary",
                "raw": signed_raw,
                "mimetype": source.mimetype or "application/pdf",
                "res_model": "radwan.document.sign.request",
                "res_id": request.id,
            })
            values = {"signed_attachment_id": attachment.id}

            if request.employee_id and "related_to" in Document._fields and "employee_id" in Document._fields:
                content = '<p><a href="/web/content/%s?download=false">%s</a></p>' % (
                    attachment.id,
                    filename,
                )
                document_values = {
                    "name": filename,
                    "content": content,
                    "related_to": "employee",
                    "employee_id": request.employee_id.id,
                }
                try:
                    with self.env.cr.savepoint():
                        signed_document = Document.create(document_values)
                        attachment.write({
                            "res_model": "document.document",
                            "res_id": signed_document.id,
                        })
                        values["signed_document_id"] = signed_document.id
                except Exception:
                    attachment.write({
                        "res_model": "radwan.document.sign.request",
                        "res_id": request.id,
                    })
            request.write(values)

    def _render_signed_pdf(self, raw, source):
        self.ensure_one()
        if not self._is_pdf_attachment(source):
            return raw
        signed_items = self.item_ids.filtered(
            lambda item: item.page and (
                item.signature_image
                or item.value_text
                or item.field_type == "date"
                or (item.field_type in ("signature", "initial") and self.signature_image)
            )
        )
        if not signed_items:
            return raw
        try:
            from odoo.tools.pdf import PdfFileReader, PdfFileWriter
            from reportlab.lib.utils import ImageReader
            from reportlab.pdfgen import canvas
        except Exception:
            _logger.exception("PDF signing libraries are not available.")
            return raw

        try:
            reader = self._pdf_reader(PdfFileReader, raw)
            writer = PdfFileWriter()
            page_count = self._pdf_page_count(reader)
            items_by_page = {}
            for item in signed_items:
                page_no = max(int(item.page or 1), 1)
                items_by_page.setdefault(page_no, self.env["radwan.document.sign.item"])
                items_by_page[page_no] |= item

            for page_index in range(page_count):
                page = self._pdf_get_page(reader, page_index)
                page_width, page_height = self._pdf_page_size(page)
                page_items = items_by_page.get(page_index + 1)
                if page_items:
                    overlay = self._build_signature_overlay(
                        canvas,
                        ImageReader,
                        page_width,
                        page_height,
                        page_items,
                    )
                    if overlay:
                        overlay_reader = self._pdf_reader(PdfFileReader, overlay)
                        overlay_page = self._pdf_get_page(overlay_reader, 0)
                        self._pdf_merge_page(page, overlay_page)
                self._pdf_add_page(writer, page)

            output = BytesIO()
            writer.write(output)
            return output.getvalue()
        except Exception:
            _logger.exception("Could not render signed PDF for request %s.", self.id)
            return raw

    def _is_pdf_attachment(self, attachment):
        self.ensure_one()
        mimetype = (attachment.mimetype or "").lower()
        filename = (attachment.name or "").lower()
        return mimetype == "application/pdf" or filename.endswith(".pdf")

    def _build_signature_overlay(self, canvas_class, image_reader_class, width, height, page_items):
        packet = BytesIO()
        pdf_canvas = canvas_class.Canvas(packet, pagesize=(width, height))
        has_content = False
        for item in page_items:
            box_width = max(18.0, width * max(float(item.width or 0.0), 1.0) / 100.0)
            box_height = max(10.0, height * max(float(item.height or 0.0), 1.0) / 100.0)
            x_pos = width * max(float(item.pos_x or 0.0), 0.0) / 100.0
            y_pos = height - (height * max(float(item.pos_y or 0.0), 0.0) / 100.0) - box_height
            x_pos = max(0.0, min(x_pos, width - box_width))
            y_pos = max(0.0, min(y_pos, height - box_height))

            if item.field_type in ("signature", "initial"):
                payload = item.signature_image or self.signature_image
                if not payload:
                    continue
                try:
                    image = image_reader_class(BytesIO(base64.b64decode(payload)))
                    pdf_canvas.drawImage(
                        image,
                        x_pos,
                        y_pos,
                        width=box_width,
                        height=box_height,
                        preserveAspectRatio=True,
                        mask="auto",
                        anchor="c",
                    )
                    has_content = True
                except Exception:
                    _logger.exception("Could not draw signature field %s.", item.id)
            else:
                text = item.value_text
                if item.field_type == "date":
                    text = fields.Date.to_string(fields.Date.context_today(self))
                if not text:
                    continue
                font_size = max(8.0, min(14.0, box_height * 0.45))
                pdf_canvas.setFillColorRGB(0.05, 0.12, 0.20)
                pdf_canvas.setFont("Helvetica", font_size)
                pdf_canvas.drawString(x_pos + 3.0, y_pos + (box_height - font_size) / 2.0, text)
                has_content = True
        pdf_canvas.save()
        if not has_content:
            return False
        packet.seek(0)
        return packet.getvalue()

    def _pdf_reader(self, reader_class, raw):
        try:
            return reader_class(BytesIO(raw), strict=False)
        except TypeError:
            return reader_class(BytesIO(raw))

    def _pdf_page_count(self, reader):
        if hasattr(reader, "getNumPages"):
            return reader.getNumPages()
        return len(reader.pages)

    def _pdf_get_page(self, reader, index):
        if hasattr(reader, "getPage"):
            return reader.getPage(index)
        return reader.pages[index]

    def _pdf_add_page(self, writer, page):
        if hasattr(writer, "addPage"):
            return writer.addPage(page)
        return writer.add_page(page)

    def _pdf_merge_page(self, page, overlay_page):
        if hasattr(page, "merge_page"):
            return page.merge_page(overlay_page)
        return page.mergePage(overlay_page)

    def _pdf_page_size(self, page):
        media_box = getattr(page, "mediabox", None) or getattr(page, "mediaBox")
        width = getattr(media_box, "width", None)
        height = getattr(media_box, "height", None)
        if width is None:
            width = media_box.getWidth()
        if height is None:
            height = media_box.getHeight()
        return float(width), float(height)

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
