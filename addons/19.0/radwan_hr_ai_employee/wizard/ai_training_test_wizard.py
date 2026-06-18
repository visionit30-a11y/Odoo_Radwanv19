# -*- coding: utf-8 -*-

from odoo import _, fields, models


class RadwanHrAiTrainingTestWizard(models.TransientModel):
    _name = "radwan.hr.ai.training.test.wizard"
    _description = "HR AI Training Test Wizard"

    training_id = fields.Many2one("radwan.hr.ai.training.knowledge", required=True, readonly=True)
    test_question = fields.Text(required=True)
    expected_context = fields.Text(readonly=True)
    ai_response = fields.Text(readonly=True)
    result_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("passed", "Passed"),
            ("needs_review", "Needs Review"),
            ("failed", "Failed"),
        ],
        default="draft",
    )
    notes = fields.Text()

    def action_generate_test_answer(self):
        self.ensure_one()
        training = self.training_id.sudo()
        context = "\n\n".join(
            [
                _("Training Knowledge Under Test:"),
                training._content_text(),
                _("Question: %s") % (self.test_question or ""),
            ]
        )
        scope = _("Manual training test by %s") % self.env.user.display_name
        response = self.env["radwan.hr.ai.llm.gateway"].generate(self.test_question, context, scope)
        if not response:
            response = _("No AI provider response was returned. Review provider connection and try again.")
        self.write({"expected_context": context, "ai_response": response, "result_status": "needs_review"})
        training._log_training_history(
            "tested",
            notes=(self.test_question or "")[:500],
            result_message=(response or "")[:500],
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_mark_passed(self):
        self.write({"result_status": "passed"})
        return {"type": "ir.actions.act_window_close"}

    def action_mark_needs_review(self):
        self.write({"result_status": "needs_review"})
        return {"type": "ir.actions.act_window_close"}

    def action_mark_failed(self):
        self.write({"result_status": "failed"})
        return {"type": "ir.actions.act_window_close"}
