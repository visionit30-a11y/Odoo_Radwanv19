from odoo import api, fields, models


class UserAuditLog(models.Model):
    _inherit = "user.audit.log"

    @api.model
    def _radwan_prepare_audit_sequence(self):
        sequence = self.env["ir.sequence"].sudo().search([
            ("code", "=", "user.audit.log"),
        ], limit=1)
        if sequence and sequence.company_id:
            sequence.company_id = False

    @api.model_create_multi
    def create(self, vals_list):
        self._radwan_prepare_audit_sequence()
        for vals in vals_list:
            if vals.get("name") in (None, False, "New"):
                vals["name"] = self.env["ir.sequence"].sudo().next_by_code(
                    "user.audit.log"
                ) or self._radwan_fallback_name()
        return models.Model.create(self, vals_list)

    @api.model
    def _radwan_fallback_name(self):
        return "AUDIT-%s" % fields.Datetime.now().strftime("%Y%m%d%H%M%S")
