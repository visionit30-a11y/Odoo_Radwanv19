from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RadwanEmployeeDocumentDate(models.Model):
    _name = "radwan.employee.document.date"
    _description = "Employee Document Date"
    _order = "document_end, document_name, id"

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        ondelete="cascade",
        index=True,
    )
    document_name = fields.Char(string="Document Name", required=True)
    document_no = fields.Char(string="Document No.")
    document_start = fields.Date(string="Document Start")
    document_end = fields.Date(string="Document End")
    document_source = fields.Char(string="Document Source")
    renewal_by = fields.Char(string="Renewal By")
    notification_days = fields.Integer(string="Notifications Days")
    notes = fields.Text(string="Nots")

    @api.constrains("document_start", "document_end", "notification_days")
    def _check_document_dates(self):
        for document in self:
            if (
                document.document_start
                and document.document_end
                and document.document_end < document.document_start
            ):
                raise ValidationError(self.env._(
                    "Document End must be on or after Document Start."
                ))
            if document.notification_days < 0:
                raise ValidationError(self.env._(
                    "Notifications Days cannot be negative."
                ))
