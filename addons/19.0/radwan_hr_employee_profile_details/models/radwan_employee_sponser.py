from odoo import fields, models


class RadwanEmployeeSponser(models.Model):
    _name = "radwan.employee.sponser"
    _description = "Employee Sponser"
    _order = "sequence, name, id"

    name = fields.Char(string="Name", required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _name_uniq = models.Constraint(
        "unique (name)",
        "Sponser name already exists.",
    )
