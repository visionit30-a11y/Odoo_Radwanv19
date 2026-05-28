# -*- coding: utf-8 -*-

from odoo import fields, models


class RadwanHrAiInsight(models.Model):
    _name = "radwan.hr.ai.insight"
    _description = "HR AI Insight"
    _order = "severity desc, create_date desc, id desc"

    name = fields.Char(required=True)
    insight_type = fields.Selection(
        [
            ("attendance", "Attendance"),
            ("leave", "Leaves"),
            ("payroll", "Payroll"),
            ("loan", "Loans"),
            ("document", "Documents"),
            ("ticket", "Tickets"),
            ("development", "Development"),
            ("general", "General"),
        ],
        default="general",
        required=True,
    )
    severity = fields.Selection(
        [
            ("0", "Info"),
            ("1", "Low"),
            ("2", "Medium"),
            ("3", "High"),
        ],
        default="0",
        required=True,
    )
    employee_id = fields.Many2one("hr.employee")
    department_id = fields.Many2one("hr.department")
    summary = fields.Text(required=True)
    recommendation = fields.Text()
    source_model = fields.Char()
    source_count = fields.Integer()
    state = fields.Selection(
        [("new", "New"), ("reviewed", "Reviewed"), ("dismissed", "Dismissed")],
        default="new",
        required=True,
    )

    def action_mark_reviewed(self):
        self.write({"state": "reviewed"})

    def action_dismiss(self):
        self.write({"state": "dismissed"})
