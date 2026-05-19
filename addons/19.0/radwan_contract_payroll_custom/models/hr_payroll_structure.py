# -*- coding: utf-8 -*-

from odoo import fields, models


class HrPayrollStructure(models.Model):
    _inherit = "hr.payroll.structure"

    radwan_structure_type_id = fields.Many2one(
        "hr.payroll.structure.type",
        string="Radwan Salary Structure Type",
        index=True,
        ondelete="set null",
    )
