# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    appraisal_count = fields.Integer(
        string="Appraisals",
        compute="_compute_appraisal_count",
    )

    def _compute_appraisal_count(self):
        grouped = self.env["radwan.appraisal"].read_group(
            [("employee_id", "in", self.ids)],
            ["employee_id"],
            ["employee_id"],
        )
        counts = {
            row["employee_id"][0]: row.get("employee_id_count", row.get("__count", 0))
            for row in grouped
            if row.get("employee_id")
        }
        for employee in self:
            employee.appraisal_count = counts.get(employee.id, 0)

    def action_view_radwan_appraisals(self):
        self.ensure_one()
        action = self.env.ref("radwan_performance_appraisal.action_appraisal_all").read()[0]
        action.update({
            "name": "Employee Appraisals",
            "domain": [("employee_id", "=", self.id)],
            "context": {
                "default_employee_id": self.id,
                "search_default_group_period": 1,
            },
        })
        return action
