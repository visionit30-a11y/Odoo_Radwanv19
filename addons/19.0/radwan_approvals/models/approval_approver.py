from odoo import fields, models


class RadwanApprover(models.Model):
    _name = "radwan.approver"
    _description = "Approval Approver"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    request_id = fields.Many2one(
        "radwan.approval.request",
        required=True,
        ondelete="cascade",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Approver",
        required=True,
        domain="[('share', '=', False)]",
    )
    required = fields.Boolean(default=True)
    status = fields.Selection(
        [
            ("new", "New"),
            ("approved", "Approved"),
            ("refused", "Refused"),
        ],
        default="new",
        required=True,
    )
    date = fields.Datetime()
    company_id = fields.Many2one(related="request_id.company_id", store=True)
