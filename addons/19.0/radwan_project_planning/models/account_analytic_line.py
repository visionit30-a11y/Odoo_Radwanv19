from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    radwan_planning_slot_id = fields.Many2one(
        'radwan.planning.slot',
        string='Planning Shift',
        index=True,
        copy=False,
        ondelete='set null',
    )
