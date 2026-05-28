# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class RadwanHrAiProviderConfig(models.Model):
    _name = "radwan.hr.ai.provider.config"
    _description = "HR AI Provider Connection"
    _order = "active desc, id desc"

    PROVIDER_PRESETS = {
        "gemini": {
            "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            "model_name": "gemini-2.5-flash",
            "timeout": 90,
        },
        "deepseek": {
            "endpoint": "https://api.deepseek.com/chat/completions",
            "model_name": "deepseek-v4-flash",
            "timeout": 90,
        },
        "qwen3": {
            "endpoint": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
            "model_name": "qwen3-plus",
            "timeout": 90,
        },
        "groq": {
            "endpoint": "https://api.groq.com/openai/v1/chat/completions",
            "model_name": "llama-3.3-70b-versatile",
            "timeout": 90,
        },
        "openrouter": {
            "endpoint": "https://openrouter.ai/api/v1/chat/completions",
            "model_name": "qwen/qwen3-235b-a22b",
            "timeout": 90,
        },
    }

    name = fields.Char(default="Default HR AI Connection", required=True)
    active = fields.Boolean(default=True)
    provider = fields.Selection(
        [
            ("disabled", "Disabled - Secure Rule Based"),
            ("ollama", "Ollama"),
            ("openai_compatible", "OpenAI Compatible API"),
            ("gemini", "Gemini 2.5 Flash"),
            ("deepseek", "DeepSeek"),
            ("qwen3", "Qwen3"),
            ("groq", "Groq (Llama/Qwen)"),
            ("openrouter", "OpenRouter"),
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

    @api.onchange("provider")
    def _onchange_provider(self):
        for record in self:
            preset = self.PROVIDER_PRESETS.get(record.provider)
            if not preset:
                continue
            record.endpoint = preset["endpoint"]
            record.model_name = preset["model_name"]
            record.timeout = preset["timeout"]

    def action_set_active_connection(self):
        for record in self:
            self.search([("id", "!=", record.id)]).write({"active": False})
            record.active = True
        return True

    def action_test_connection(self):
        for record in self:
            error_key = "radwan_hr_ai.last_test_error.%s" % record.id
            self.env["ir.config_parameter"].sudo().set_param(error_key, "")
            answer = self.env["radwan.hr.ai.llm.gateway"].with_context(
                radwan_hr_ai_config_id=record.id,
                radwan_hr_ai_testing=True,
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
                test_error = self.env["ir.config_parameter"].sudo().get_param(error_key, "")
                record.write(
                    {
                        "last_test_state": "failed",
                        "last_test_message": test_error
                        or _("Connection failed. Check provider, endpoint, model name, API key, and network access."),
                        "last_test_date": fields.Datetime.now(),
                    }
                )
        return True
