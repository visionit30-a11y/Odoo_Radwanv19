from odoo import api, fields, models


class RadwanApprovalProductLine(models.Model):
    _name = "radwan.approval.product.line"
    _description = "Approval Product Line"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    request_id = fields.Many2one(
        "radwan.approval.request",
        required=True,
        ondelete="cascade",
    )
    product_id = fields.Many2one("product.product", required=True)
    name = fields.Char(string="Description")
    quantity = fields.Float(default=1.0)
    product_uom_id = fields.Many2one("uom.uom", string="Unit of Measure")
    price_unit = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one(related="request_id.currency_id", store=True)
    subtotal = fields.Monetary(
        compute="_compute_subtotal",
        currency_field="currency_id",
        store=True,
    )
    company_id = fields.Many2one(related="request_id.company_id", store=True)

    @api.depends("quantity", "price_unit")
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.name = line.product_id.display_name
                line.product_uom_id = line.product_id.uom_id
                line.price_unit = line.product_id.lst_price
