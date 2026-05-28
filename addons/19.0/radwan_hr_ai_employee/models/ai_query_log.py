# -*- coding: utf-8 -*-

from odoo import fields, models


class RadwanHrAiQueryLog(models.Model):
    _name = "radwan.hr.ai.query.log"
    _description = "HR AI Query Log"
    _order = "create_date desc, id desc"
    _inherit = ["mail.thread"]

    name = fields.Char(default="HR AI Query", readonly=True)
    user_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user, readonly=True)
    employee_id = fields.Many2one("hr.employee", readonly=True)
    audience = fields.Selection(
        [
            ("employee", "Employee"),
            ("manager", "Manager"),
            ("hr", "HR"),
        ],
        default="employee",
        required=True,
        readonly=True,
    )
    question = fields.Text(required=True, readonly=True)
    answer = fields.Text(readonly=True)
    allowed_model_names = fields.Char(readonly=True)
    visible_employee_count = fields.Integer(readonly=True)
    is_blocked = fields.Boolean(readonly=True)
    blocked_reason = fields.Char(readonly=True)
