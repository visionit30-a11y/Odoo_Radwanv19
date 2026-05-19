from odoo import api, fields, models


class UserAudit(models.Model):
    _inherit = "user.audit"

    @api.model
    def create_audit_log(self, res_model, res_id=False, operation_type="create"):
        if operation_type not in {"create", "read", "write", "delete"}:
            return False
        if operation_type in {"read", "write", "delete"} and not res_id:
            return False

        model = self.env["ir.model"].sudo().search([
            ("model", "=", res_model),
        ], limit=1)
        if not model:
            return False

        audits = self.sudo().search([("model_ids", "in", model.id)]).filtered(
            lambda audit: self._is_operation_tracked(operation_type, audit)
            and self._is_user_tracked(audit)
        )
        if not audits:
            return False

        record_ids = res_id if isinstance(res_id, list) else [res_id]
        current_time = fields.Datetime.now()
        log_vals = [
            {
                "user_id": self.env.uid,
                "model_id": model.id,
                "record": record_id or 0,
                "operation_type": operation_type,
                "date": current_time,
            }
            for record_id in record_ids
        ]
        return self.env["user.audit.log"].sudo().create(log_vals)
