# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class RadwanHrAiDataAccess(models.Model):
    _name = "radwan.hr.ai.data.access"
    _description = "HR AI Data Access Configuration"
    _order = "sequence, name"

    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    model_id = fields.Many2one(
        "ir.model",
        string="Table / Model",
        required=True,
        ondelete="cascade",
        domain="[('transient', '=', False)]",
    )
    model_name = fields.Char(related="model_id.model", store=True, readonly=True)
    model_description = fields.Char(related="model_id.name", readonly=True)
    description = fields.Text(
        help="Short business description shown to HR AI administrators and sent as a source label."
    )
    allow_all_ai_users = fields.Boolean(
        string="Available to all AI users",
        help="If enabled, every user who can use HR AI may query this table, still limited by Odoo access rules.",
    )
    employee_ids = fields.Many2many(
        "hr.employee",
        "radwan_hr_ai_access_employee_rel",
        "access_id",
        "employee_id",
        string="Allowed Employees",
    )
    department_ids = fields.Many2many(
        "hr.department",
        "radwan_hr_ai_access_department_rel",
        "access_id",
        "department_id",
        string="Allowed Departments",
    )
    group_ids = fields.Many2many(
        "res.groups",
        "radwan_hr_ai_access_group_rel",
        "access_id",
        "group_id",
        string="Allowed Odoo Groups",
    )

    _sql_constraints = [
        ("model_unique", "unique(model_id)", "Each model can only have one HR AI data access configuration."),
    ]

    @api.onchange("model_id")
    def _onchange_model_id(self):
        for record in self:
            if record.model_id and not record.name:
                record.name = record.model_id.name or record.model_id.model

    def action_sync_hr_models(self):
        model_domain = [
            ("transient", "=", False),
            "|",
            "|",
            "|",
            ("model", "=like", "hr.%"),
            ("model", "=like", "radwan.hr%"),
            ("model", "=like", "radwan.attendance%"),
            ("model", "in", ["project.task", "helpdesk.ticket", "approval.request", "survey.user_input", "ir.attachment"]),
        ]
        existing_model_ids = set(self.search([]).mapped("model_id").ids)
        vals_list = []
        for model in self.env["ir.model"].sudo().search(model_domain, order="model"):
            if model.id in existing_model_ids:
                continue
            vals_list.append(
                {
                    "name": model.name or model.model,
                    "model_id": model.id,
                    "description": _("Odoo model: %s") % model.model,
                    "active": False,
                }
            )
        if vals_list:
            self.create(vals_list)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("HR AI Data Access"),
                "message": _("%s model(s) synchronized.") % len(vals_list),
                "type": "success",
                "sticky": False,
            },
        }

    def applies_to_user(self, user, employee=False, is_hr_power_user=False):
        self.ensure_one()
        if is_hr_power_user:
            return True
        if self.allow_all_ai_users:
            return True
        if self.group_ids and user.groups_id & self.group_ids:
            return True
        if employee:
            if self.employee_ids and employee.id in self.employee_ids.ids:
                return True
            if self.department_ids and employee.department_id.id in self.department_ids.ids:
                return True
        return False
