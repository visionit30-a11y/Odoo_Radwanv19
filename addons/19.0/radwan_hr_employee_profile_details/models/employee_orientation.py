# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OrientationRequest(models.Model):
    _inherit = "orientation.request"

    completed_datetime = fields.Datetime(
        string="Completed On",
        readonly=True,
        copy=False,
        help="Date and time when this orientation line was marked as completed.",
    )
    email_sent = fields.Boolean(
        string="Email Sent",
        readonly=True,
        copy=False,
    )
    email_sent_date = fields.Datetime(
        string="Email Sent On",
        readonly=True,
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("state") == "complete" and not vals.get("completed_datetime"):
                vals["completed_datetime"] = fields.Datetime.now()
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("state") == "complete":
            vals = dict(vals)
            for record in self.filtered(lambda line: not line.completed_datetime):
                record.completed_datetime = fields.Datetime.now()
        return super().write(vals)

    def action_confirm_request(self):
        result = super().action_confirm_request()
        self.filtered(lambda line: not line.completed_datetime).write({
            "completed_datetime": fields.Datetime.now(),
        })
        return result

    def _get_orientation_email_to(self):
        self.ensure_one()
        partner = self.partner_id.partner_id
        if partner.email:
            return partner.email
        if self.employee_id.work_email:
            return self.employee_id.work_email
        if "private_email" in self.employee_id._fields and self.employee_id.private_email:
            return self.employee_id.private_email
        return False

    def _get_orientation_email_values(self):
        self.ensure_one()
        orientation = self.request_orientation_id
        employee = self.employee_id or orientation.employee_id
        company = self.company_id or self.employee_company_id or self.env.company
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
        record_url = ""
        if base_url and orientation:
            record_url = "%s/odoo/action-%s/%s" % (
                base_url,
                self.env.ref("employee_orientation.employee_orientation_action").id,
                orientation.id,
            )

        body = Markup("""
            <p>Dear %(responsible)s,</p>
            <p>Please follow up on the employee orientation item below:</p>
            <ul>
                <li><strong>Employee:</strong> %(employee)s</li>
                <li><strong>Checklist Item:</strong> %(item)s</li>
                <li><strong>Expected Date:</strong> %(expected)s</li>
                <li><strong>Status:</strong> %(status)s</li>
            </ul>
            %(link)s
            <p>Regards,<br/>%(company)s</p>
        """) % {
            "responsible": self.partner_id.name or _("Responsible User"),
            "employee": employee.name or "-",
            "item": self.request_name or "-",
            "expected": self.request_expected_date or "-",
            "status": dict(self._fields["state"].selection).get(self.state, self.state),
            "link": Markup('<p><a href="%s">Open Orientation Record</a></p>') % record_url if record_url else "",
            "company": company.name or "",
        }
        return {
            "subject": _("Employee Orientation: %s") % (self.request_name or employee.name or ""),
            "body_html": body,
            "email_to": self._get_orientation_email_to(),
            "auto_delete": False,
        }

    def action_send_orientation_email(self):
        sent_count = 0
        missing = []
        for request in self:
            email_to = request._get_orientation_email_to()
            if not email_to:
                missing.append(request.display_name)
                continue
            mail = self.env["mail.mail"].sudo().create(request._get_orientation_email_values())
            mail.send()
            request.write({
                "email_sent": True,
                "email_sent_date": fields.Datetime.now(),
            })
            sent_count += 1

        if not sent_count and missing:
            raise UserError(_("No email address was found for the selected orientation line(s)."))
        if missing:
            message = _("Emails were sent, but these lines have no recipient email: %s") % ", ".join(missing)
            (self[:1].request_orientation_id or self[:1]).message_post(body=message)
        return True


class EmployeeOrientation(models.Model):
    _inherit = "employee.orientation"

    def action_send_all_orientation_emails(self):
        for orientation in self:
            lines = orientation.orientation_request_ids.filtered(lambda line: line.state != "cancel")
            if not lines:
                raise UserError(_("There are no orientation checklist lines to email."))
            lines.action_send_orientation_email()
            orientation.message_post(body=_("Orientation checklist emails were sent."))
        return True
