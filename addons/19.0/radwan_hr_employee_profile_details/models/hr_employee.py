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
    radwan_religion_id = fields.Many2one(
        comodel_name="radwan.employee.religion",
        string="Religion",
    )
    radwan_family_status = fields.Selection(
        selection=[
            ("family", "Family"),
            ("single", "Single"),
        ],
        string="Family Status",
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
    radwan_travel_ticket_ids = fields.One2many(
        comodel_name="radwan.employee.travel.ticket",
        inverse_name="employee_id",
        string="Travel Tickets",
    )
    radwan_travel_ticket_count = fields.Integer(
        string="Travel Ticket Count",
        compute="_compute_radwan_travel_ticket_count",
    )
    radwan_visa_ids = fields.One2many(
        comodel_name="radwan.employee.visa",
        inverse_name="employee_id",
        string="Visas",
    )
    radwan_visa_count = fields.Integer(
        string="Visa Count",
        compute="_compute_radwan_visa_count",
    )
    radwan_work_injury_ids = fields.One2many(
        comodel_name="radwan.work.injury",
        inverse_name="employee_id",
        string="Work Injuries",
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
    radwan_social_insurance_join_date = fields.Date(
        string="Social Insurance Join Date",
    )
    radwan_social_insurance_exit_date = fields.Date(
        string="Social Insurance Exit Date",
    )
    radwan_social_insurance_wage = fields.Monetary(
        string="Contribution Wage",
        currency_field="currency_id",
    )
    radwan_social_insurance_employee_rate = fields.Float(
        string="Employee Monthly Deduction %",
    )
    radwan_social_insurance_company_rate = fields.Float(
        string="Company Contribution %",
    )
    radwan_social_insurance_profession = fields.Char(
        string="Registered Profession",
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

    def _compute_radwan_travel_ticket_count(self):
        groups = self.env["radwan.employee.travel.ticket"]._read_group(
            [("employee_id", "in", self.ids)],
            ["employee_id"],
            ["__count"],
        )
        counts = {employee.id: count for employee, count in groups}
        for employee in self:
            employee.radwan_travel_ticket_count = counts.get(employee.id, 0)

    def _compute_radwan_visa_count(self):
        groups = self.env["radwan.employee.visa"]._read_group(
            [("employee_id", "in", self.ids)],
            ["employee_id"],
            ["__count"],
        )
        counts = {employee.id: count for employee, count in groups}
        for employee in self:
            employee.radwan_visa_count = counts.get(employee.id, 0)

    def action_radwan_travel_tickets(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Travel Tickets"),
            "res_model": "radwan.employee.travel.ticket",
            "view_mode": "list,form",
            "domain": [("employee_id", "=", self.id)],
            "context": {
                "default_employee_id": self.id,
                "default_company_id": self.company_id.id,
            },
        }

    def action_radwan_visas(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Visas"),
            "res_model": "radwan.employee.visa",
            "view_mode": "list,form",
            "domain": [("employee_id", "=", self.id)],
            "context": {
                "default_employee_id": self.id,
                "default_company_id": self.company_id.id,
            },
        }
