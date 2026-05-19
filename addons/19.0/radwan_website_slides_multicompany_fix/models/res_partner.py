from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _radwan_normalize_elearning_contacts(self):
        return self.env["slide.channel"]._radwan_normalize_learning_partner_companies(self)
