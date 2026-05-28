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
        ondelete="cascade",
        domain="[('transient', '=', False)]",
        help="Legacy single-table selector. You can leave it empty when using Allowed Tables.",
    )
    model_ids = fields.Many2many(
        "ir.model",
        "radwan_hr_ai_access_model_rel",
        "access_id",
        "model_id",
        string="Allowed Tables",
        domain="[('transient', '=', False)]",
        help="Select one or more Odoo tables/models that this rule allows AI to use.",
    )
    model_name = fields.Char(related="model_id.model", store=True, readonly=True)
    model_description = fields.Char(related="model_id.name", readonly=True)
    model_names = fields.Char(compute="_compute_model_names", store=True)
    model_descriptions = fields.Text(compute="_compute_model_names", store=True)
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

    @api.onchange("model_id")
    def _onchange_model_id(self):
        for record in self:
            if record.model_id and not record.name:
                record.name = record.model_id.name or record.model_id.model
            if record.model_id and record.model_id not in record.model_ids:
                record.model_ids = [(4, record.model_id.id)]

    @api.depends("model_id", "model_ids")
    def _compute_model_names(self):
        for record in self:
            models = record.model_ids | record.model_id
            record.model_names = ", ".join(models.mapped("model"))
            record.model_descriptions = "\n".join(
                "%s - %s" % (model.model, model.name or model.model)
                for model in models
            )

    def covered_model_names(self):
        self.ensure_one()
        models = self.model_ids | self.model_id
        return set(models.mapped("model"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("model_id") and not vals.get("model_ids"):
                vals["model_ids"] = [(6, 0, [vals["model_id"]])]
        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)
        if "model_id" in vals and vals.get("model_id") and "model_ids" not in vals:
            for record in self:
                if record.model_id and record.model_id.id not in record.model_ids.ids:
                    record.model_ids = [(4, record.model_id.id)]
        return result

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
                    "model_ids": [(6, 0, [model.id])],
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
