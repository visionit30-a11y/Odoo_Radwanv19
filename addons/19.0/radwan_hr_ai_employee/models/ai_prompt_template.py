# -*- coding: utf-8 -*-

from odoo import fields, models


class RadwanHrAiPromptTemplate(models.Model):
    _name = "radwan.hr.ai.prompt.template"
    _description = "HR AI Prompt Template"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    audience = fields.Selection(
        [
            ("employee", "Employee"),
            ("manager", "Manager"),
            ("hr", "HR"),
        ],
        default="employee",
        required=True,
    )
    system_prompt = fields.Text(required=True)
    instructions = fields.Text()
