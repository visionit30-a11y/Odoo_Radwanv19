# -*- coding: utf-8 -*-

from odoo import _, fields, models


class RadwanHrAiProviderConfig(models.Model):
    _name = "radwan.hr.ai.provider.config"
    _description = "HR AI Provider Connection"
    _order = "active desc, id desc"

    name = fields.Char(default="Default HR AI Connection", required=True)
    active = fields.Boolean(default=True)
    provider = fields.Selection(
        [
            ("disabled", "Disabled - Secure Rule Based"),
            ("ollama", "Ollama"),
            ("openai_compatible", "OpenAI Compatible API"),
        ],
        default="disabled",
        required=True,
    )
    endpoint = fields.Char(default="http://127.0.0.1:11434", required=True)
    model_name = fields.Char(default="qwen2.5:7b-instruct", required=True)
    api_key = fields.Char()
    timeout = fields.Integer(default=45, required=True)
    last_test_state = fields.Selection(
        [
            ("not_tested", "Not Tested"),
            ("success", "Success"),
            ("failed", "Failed"),
        ],
        default="not_tested",
        readonly=True,
    )
    last_test_message = fields.Text(readonly=True)
    last_test_date = fields.Datetime(readonly=True)

    def action_set_active_connection(self):
        for record in self:
            self.search([("id", "!=", record.id)]).write({"active": False})
            record.active = True
        return True

    def action_test_connection(self):
        for record in self:
            answer = self.env["radwan.hr.ai.llm.gateway"].with_context(
                radwan_hr_ai_config_id=record.id
            ).generate(
                _("Reply with a short confirmation that the HR AI connection works."),
                _("Connection test only. No employee data is included."),
                _("Test executed by %s") % self.env.user.name,
            )
            if answer:
                record.write(
                    {
                        "last_test_state": "success",
                        "last_test_message": answer,
                        "last_test_date": fields.Datetime.now(),
                    }
                )
            else:
                record.write(
                    {
                        "last_test_state": "failed",
                        "last_test_message": _(
                            "Connection failed. Check provider, endpoint, model name, API key, and network access."
                        ),
                        "last_test_date": fields.Datetime.now(),
                    }
                )
        return True
