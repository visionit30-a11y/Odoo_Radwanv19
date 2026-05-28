# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class RadwanHrAiEmployeeController(http.Controller):
    @http.route("/radwan/hr_ai/ask", type="jsonrpc", auth="user", methods=["POST"])
    def ask_hr_ai(self, question, audience="employee"):
        assistant = request.env["radwan.hr.ai.employee.assistant"].create(
            {
                "question": question,
            }
        )
        assistant.action_generate_answer()
        return {
            "success": assistant.state == "answered",
            "state": assistant.state,
            "answer": assistant.answer or "",
            "scope": assistant.scope_summary or "",
            "assistant_id": assistant.id,
        }

    @http.route(["/my/hr-ai"], type="http", auth="user", website=True, methods=["GET", "POST"])
    def hr_ai_portal(self, **post):
        question = post.get("question")
        answer = ""
        scope = ""
        state = "draft"
        if request.httprequest.method == "POST" and question:
            assistant = request.env["radwan.hr.ai.employee.assistant"].create(
                {
                    "question": question,
                }
            )
            assistant.action_generate_answer()
            answer = assistant.answer or ""
            scope = assistant.scope_summary or ""
            state = assistant.state
        return request.render(
            "radwan_hr_ai_employee.portal_hr_ai_assistant",
            {
                "question": question or "",
                "answer": answer,
                "scope": scope,
                "state": state,
            },
        )
