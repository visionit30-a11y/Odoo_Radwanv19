from datetime import timedelta

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    radwan_sponser = fields.Selection(
        selection=[
            ("company", "Company"),
            ("employee", "Employee"),
            ("other", "Other"),
        ],
        string="Sponser (Legacy)",
    )
    radwan_sponser_id = fields.Many2one(
        comodel_name="radwan.employee.sponser",
        string="Sponser",
    )

    radwan_document_date_ids = fields.One2many(
        comodel_name="radwan.employee.document.date",
        inverse_name="employee_id",
        string="Documents Date",
    )

    radwan_family_detail_ids = fields.One2many(
        comodel_name="radwan.employee.family.detail",
        inverse_name="employee_id",
        string="Family Details",
    )
    radwan_passport_issue_date = fields.Date(
        string="Passport Issue Date",
    )
    radwan_passport_issue_place = fields.Char(
        string="Passport Issue Place",
    )
    radwan_passport_profession = fields.Char(
        string="Profession in Passport",
    )

    radwan_document_expiry_name = fields.Char(
        string="Document Expiry",
        compute="_compute_radwan_document_expiry",
        store=True,
    )
    radwan_document_expiry_date = fields.Date(
        string="Document Expiry Date",
        compute="_compute_radwan_document_expiry",
        store=True,
    )
    radwan_document_expiry_status = fields.Selection(
        selection=[
            ("not_set", "Not Set"),
            ("valid", "Valid"),
            ("expiring_soon", "Expiring Soon"),
            ("expired", "Expired"),
        ],
        string="Document Status",
        compute="_compute_radwan_document_expiry",
        store=True,
    )

    @api.depends(
        "radwan_document_date_ids.document_name",
        "radwan_document_date_ids.document_end",
        "radwan_document_date_ids.notification_days",
    )
    def _compute_radwan_document_expiry(self):
        today = fields.Date.context_today(self)
        for employee in self:
            documents = employee.radwan_document_date_ids.filtered("document_end")
            if not documents:
                employee.radwan_document_expiry_name = False
                employee.radwan_document_expiry_date = False
                employee.radwan_document_expiry_status = "not_set"
                continue

            document = documents.sorted(
                key=lambda document: (
                    employee._get_radwan_document_status_priority(document, today),
                    document.document_end,
                    document.id,
                )
            )[:1]
            employee.radwan_document_expiry_name = document.document_name
            employee.radwan_document_expiry_date = document.document_end
            employee.radwan_document_expiry_status = (
                employee._get_radwan_document_status(document, today)
            )

    def _get_radwan_document_status_priority(self, document, today):
        priorities = {
            "expired": 0,
            "expiring_soon": 1,
            "valid": 2,
            "not_set": 3,
        }
        return priorities[self._get_radwan_document_status(document, today)]

    def _get_radwan_document_status(self, document, today):
        if not document.document_end:
            return "not_set"
        if document.document_end < today:
            return "expired"
        warning_date = today + timedelta(days=document.notification_days or 0)
        if document.document_end <= warning_date:
            return "expiring_soon"
        return "valid"

    def radwan_cron_refresh_expiry_statuses(self):
        parent = getattr(super(), "radwan_cron_refresh_expiry_statuses", None)
        result = parent() if parent else None
        employees = self.with_context(active_test=False).search([])
        employees._compute_radwan_document_expiry()
        return result
