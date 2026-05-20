from odoo import _
from odoo.addons.om_account_followup.models.partner import (
    ResPartner as FollowupResPartner,
)


def _radwan_followup_write(self, vals):
    if vals.get("payment_responsible_id"):
        new_responsible = self.env["res.users"].browse(vals["payment_responsible_id"])
        for partner in self:
            if partner.payment_responsible_id != new_responsible:
                responsible_partner = new_responsible.partner_id
                if responsible_partner:
                    partner.message_post(
                        body=_(
                            "You became responsible to do the next action "
                            "for the payment follow-up of"
                        )
                        + " <b><a href='#id=%s&view_type=form&model=res.partner'> "
                        "%s </a></b>" % (partner.id, partner.name),
                        message_type="comment",
                        subtype_xmlid="mail.mt_comment",
                        partner_ids=responsible_partner.ids,
                    )
    return super(FollowupResPartner, self).write(vals)


FollowupResPartner.write = _radwan_followup_write
