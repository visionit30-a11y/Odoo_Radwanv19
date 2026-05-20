from odoo import fields, models


class RadwanEmployeeReligion(models.Model):
    _name = "radwan.employee.religion"
    _description = "Employee Religion"
    _order = "sequence, name, id"

    name = fields.Char(string="Religion Name", required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _name_uniq = models.Constraint(
        "unique (name)",
        "Religion name already exists.",
    )
