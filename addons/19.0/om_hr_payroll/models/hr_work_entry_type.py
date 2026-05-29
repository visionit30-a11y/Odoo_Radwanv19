from odoo import fields, models


class HrWorkEntryType(models.Model):
    _inherit = "hr.work.entry.type"

    radwan_display_in_payslip = fields.Boolean(
        string="Display in Payslip",
        default=True,
        help="Show this work entry type in payroll reports and payslip summaries.",
    )
    radwan_rounding = fields.Selection(
        [
            ("no_rounding", "No Rounding"),
            ("half_day", "Half Day"),
            ("full_day", "Full Day"),
        ],
        string="Rounding",
        default="no_rounding",
        required=True,
        help="Controls how this work entry type is rounded for payroll display.",
    )
    radwan_unpaid_structure_type_ids = fields.Many2many(
        "hr.payroll.structure.type",
        "radwan_work_entry_type_unpaid_structure_rel",
        "work_entry_type_id",
        "structure_type_id",
        string="Unpaid in Structure Types",
        help="Salary structure types where this work entry type should be treated as unpaid.",
    )
    radwan_unforeseen_absence = fields.Boolean(
        string="Unforeseen Absence",
        help="Mark this work entry type as an unexpected absence for payroll reporting.",
    )
