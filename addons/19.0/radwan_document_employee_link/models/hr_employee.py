# -*- coding: utf-8 -*-

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    document_count = fields.Integer(
        string="Documents",
        compute="_compute_document_count",
    )

    def _compute_document_count(self):
        Document = self.env["document.document"]
        groups = Document._read_group(
            [
                ("related_to", "=", "employee"),
                ("employee_id", "in", self.ids),
            ],
            ["employee_id"],
            ["__count"],
        )
        counts = {employee.id: count for employee, count in groups}
        for employee in self:
            employee.document_count = counts.get(employee.id, 0)

    def action_view_radwan_documents(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Documents",
            "res_model": "document.document",
            "view_mode": "kanban,list,form",
            "domain": [
                ("related_to", "=", "employee"),
                ("employee_id", "=", self.id),
            ],
            "context": {
                "default_related_to": "employee",
                "default_employee_id": self.id,
            },
        }
