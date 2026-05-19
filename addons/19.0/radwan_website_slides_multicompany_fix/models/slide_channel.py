import logging

from odoo import api, models


_logger = logging.getLogger(__name__)


class SlideChannel(models.Model):
    _inherit = "slide.channel"

    @api.model
    def _radwan_normalize_learning_partner_companies(self, partners=None):
        """Share external eLearning contacts so multi-company rules stay valid."""
        partners = partners or self._radwan_get_learning_partners()
        partners = partners.sudo().filtered(
            lambda partner: partner.company_id
            and partner.partner_share
            and not partner.user_ids
        )
        if not partners:
            return partners

        partner_names = ", ".join(partners.mapped("display_name"))
        partners.write({"company_id": False})
        _logger.info(
            "Shared %s eLearning contact(s) for multi-company access: %s",
            len(partners),
            partner_names,
        )
        return partners

    @api.model
    def _radwan_get_learning_partners(self):
        partners = self.env["res.partner"].sudo().browse()

        attendees = self.env["slide.channel.partner"].sudo().search([])
        partners |= attendees.mapped("partner_id")

        followers = self.env["mail.followers"].sudo().search([
            ("res_model", "in", ["slide.channel", "slide.slide"]),
            ("partner_id", "!=", False),
        ])
        partners |= followers.mapped("partner_id")

        messages = self.env["mail.message"].sudo().search([
            ("model", "in", ["slide.channel", "slide.slide"]),
            ("author_id", "!=", False),
        ])
        partners |= messages.mapped("author_id")

        return partners
