# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    radwan_hr_ai_provider = fields.Selection(
        [
            ("disabled", "Disabled - Secure Rule Based"),
            ("ollama", "Ollama"),
            ("openai_compatible", "OpenAI Compatible API"),
        ],
        string="HR AI Provider",
        default="disabled",
        config_parameter="radwan_hr_ai.provider",
    )
    radwan_hr_ai_endpoint = fields.Char(
        string="HR AI Endpoint",
        default="http://127.0.0.1:11434",
        config_parameter="radwan_hr_ai.endpoint",
    )
    radwan_hr_ai_model = fields.Char(
        string="HR AI Model",
        default="qwen2.5:7b-instruct",
        config_parameter="radwan_hr_ai.model",
    )
    radwan_hr_ai_api_key = fields.Char(
        string="HR AI API Key",
        config_parameter="radwan_hr_ai.api_key",
    )
    radwan_hr_ai_timeout = fields.Integer(
        string="HR AI Timeout",
        default=45,
        config_parameter="radwan_hr_ai.timeout",
    )
