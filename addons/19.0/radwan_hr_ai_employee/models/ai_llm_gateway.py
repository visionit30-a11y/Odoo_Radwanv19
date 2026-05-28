# -*- coding: utf-8 -*-

import logging

import requests

from odoo import _, models

_logger = logging.getLogger(__name__)


class RadwanHrAiLlmGateway(models.AbstractModel):
    _name = "radwan.hr.ai.llm.gateway"
    _description = "Radwan HR AI LLM Gateway"

    def _config(self):
        config_id = self.env.context.get("radwan_hr_ai_config_id")
        Config = self.env["radwan.hr.ai.provider.config"].sudo()
        if config_id:
            return Config.browse(config_id).exists()
        return Config.search([("active", "=", True)], limit=1)

    def _param(self, key, default=None):
        return self.env["ir.config_parameter"].sudo().get_param(key, default)

    def _set_test_error(self, config, error):
        if not self.env.context.get("radwan_hr_ai_testing") or not config:
            return
        self.env["ir.config_parameter"].sudo().set_param(
            "radwan_hr_ai.last_test_error.%s" % config.id,
            str(error or "")[:1000],
        )

    def _format_request_error(self, error):
        response = getattr(error, "response", None)
        if response is not None:
            body = (response.text or "").strip()
            return "HTTP %s: %s" % (response.status_code, body[:800])
        return str(error)

    def _timeout(self):
        config = self._config()
        if config:
            return config.timeout or 45
        try:
            return int(self._param("radwan_hr_ai.timeout", "45"))
        except (TypeError, ValueError):
            return 45

    def is_enabled(self):
        config = self._config()
        if config:
            return config.provider != "disabled"
        return self._param("radwan_hr_ai.provider", "disabled") != "disabled"

    def generate(self, question, secure_context, scope_summary):
        config = self._config()
        provider = config.provider if config else self._param("radwan_hr_ai.provider", "disabled")
        if provider == "ollama":
            return self._generate_ollama(question, secure_context, scope_summary, config)
        if provider in ("openai_compatible", "gemini", "deepseek", "qwen3", "groq", "openrouter"):
            return self._generate_openai_compatible(question, secure_context, scope_summary, config)
        return False

    def _system_prompt(self):
        return _(
            "You are a secure HR assistant inside Odoo. Answer using only the "
            "provided context. Never invent HR data. If the answer is not in "
            "the context, say that the information is not available under the "
            "current user's permissions. Match the user's language. Return plain "
            "text only. Do not return HTML tags, markdown symbols, tables, code "
            "blocks, <br/> tags, asterisks, or escaped HTML entities. Use short "
            "sentences and simple numbered lines only when needed."
        )

    def _messages(self, question, secure_context, scope_summary):
        return [
            {"role": "system", "content": self._system_prompt()},
            {
                "role": "user",
                "content": "\n\n".join(
                    [
                        "SECURITY SCOPE:",
                        scope_summary or "-",
                        "AUTHORIZED ODOO CONTEXT:",
                        secure_context or "-",
                        "USER QUESTION:",
                        question or "",
                    ]
                ),
            },
        ]

    def _generate_ollama(self, question, secure_context, scope_summary, config=False):
        endpoint = (
            (config.endpoint if config else self._param("radwan_hr_ai.endpoint", "http://127.0.0.1:11434")) or ""
        ).rstrip("/")
        model = config.model_name if config else self._param("radwan_hr_ai.model", "qwen2.5:7b-instruct")
        api_key = ((config.api_key if config else self._param("radwan_hr_ai.api_key", "")) or "").strip()
        url = "%s/chat" % endpoint if endpoint.endswith("/api") else "%s/api/chat" % endpoint
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = "Bearer %s" % api_key
        payload = {
            "model": model,
            "messages": self._messages(question, secure_context, scope_summary),
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_ctx": 8192,
            },
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self._timeout())
            response.raise_for_status()
            data = response.json()
            message = data.get("message") or {}
            return (message.get("content") or "").strip()
        except Exception as error:
            self._set_test_error(config, self._format_request_error(error))
            _logger.warning("Ollama HR AI request failed: %s", error)
            return False

    def _generate_openai_compatible(self, question, secure_context, scope_summary, config=False):
        endpoint = ((config.endpoint if config else self._param("radwan_hr_ai.endpoint", "")) or "").rstrip("/")
        model = config.model_name if config else self._param("radwan_hr_ai.model", "Qwen/Qwen2.5-7B-Instruct")
        api_key = ((config.api_key if config else self._param("radwan_hr_ai.api_key", "")) or "").strip()
        if not endpoint:
            return False
        url = endpoint if endpoint.endswith("/chat/completions") else "%s/v1/chat/completions" % endpoint
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = "Bearer %s" % api_key
        payload = {
            "model": model,
            "messages": self._messages(question, secure_context, scope_summary),
            "temperature": 0.2,
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self._timeout())
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                return False
            message = choices[0].get("message") or {}
            return (message.get("content") or "").strip()
        except Exception as error:
            self._set_test_error(config, self._format_request_error(error))
            _logger.warning("OpenAI-compatible HR AI request failed: %s", error)
            return False
