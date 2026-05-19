from odoo import api, models


class SlideChannelPartner(models.Model):
    _inherit = "slide.channel.partner"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.mapped("partner_id")._radwan_normalize_elearning_contacts()
        return records

    def write(self, vals):
        result = super().write(vals)
        if "partner_id" in vals:
            self.mapped("partner_id")._radwan_normalize_elearning_contacts()
        return result
