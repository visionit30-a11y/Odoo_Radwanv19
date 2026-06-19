# -*- coding: utf-8 -*-

import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import html2plaintext


class RadwanHrAiTrainingTag(models.Model):
    _name = "radwan.hr.ai.training.tag"
    _description = "HR AI Training Tag"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    color = fields.Integer(default=0)
    active = fields.Boolean(default=True)


class RadwanHrAiTrainingKnowledge(models.Model):
    _name = "radwan.hr.ai.training.knowledge"
    _description = "HR AI Training Knowledge"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority asc, write_date desc, id desc"

    name = fields.Char(string="Title", required=True, tracking=True)
    code = fields.Char(string="Reference", readonly=True, copy=False, default=lambda self: _("New"))
    knowledge_type = fields.Selection(
        [
            ("policy", "Policy"),
            ("regulation", "Regulation"),
            ("procedure", "Procedure"),
            ("command", "Assistant Command"),
            ("restriction", "Restriction"),
            ("faq", "FAQ"),
            ("odoo_rule", "Odoo Data Rule"),
            ("template", "Response Template"),
            ("escalation", "Escalation Rule"),
            ("other", "Other"),
        ],
        required=True,
        default="policy",
        tracking=True,
    )
    hr_domain = fields.Selection(
        [
            ("attendance", "Attendance"),
            ("leaves", "Leaves"),
            ("payroll", "Payroll"),
            ("loans", "Loans"),
            ("contracts", "Contracts"),
            ("recruitment", "Recruitment"),
            ("onboarding", "Onboarding"),
            ("performance", "Performance"),
            ("disciplinary", "Disciplinary"),
            ("employee_relations", "Employee Relations"),
            ("training", "Training"),
            ("end_of_service", "End of Service"),
            ("general", "General"),
        ],
        required=True,
        default="general",
        tracking=True,
    )
    description = fields.Text()
    content = fields.Html(string="Training Content", required=True, sanitize=True)
    question_example = fields.Text(string="Example User Question")
    answer_example = fields.Text(string="Expected Answer Example")
    priority = fields.Integer(default=10, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("under_review", "Under Review"),
            ("approved", "Approved"),
            ("archived", "Archived"),
        ],
        default="draft",
        tracking=True,
    )
    allowed_groups_ids = fields.Many2many(
        "res.groups",
        "radwan_hr_ai_training_group_rel",
        "training_id",
        "group_id",
        string="Allowed Groups",
    )
    allowed_company_ids = fields.Many2many(
        "res.company",
        "radwan_hr_ai_training_company_rel",
        "training_id",
        "company_id",
        string="Allowed Companies",
    )
    related_model_id = fields.Many2one("ir.model", string="Related Model", ondelete="set null")
    related_field_ids = fields.Many2many(
        "ir.model.fields",
        "radwan_hr_ai_training_related_field_rel",
        "training_id",
        "field_id",
        string="Related Fields",
    )
    sensitive_field_ids = fields.Many2many(
        "ir.model.fields",
        "radwan_hr_ai_training_sensitive_field_rel",
        "training_id",
        "field_id",
        string="Sensitive Fields",
    )
    block_sensitive_data = fields.Boolean(string="Hide Sensitive Data", default=True)
    confidentiality_level = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("managers", "Managers Only"),
            ("hr_only", "HR Only"),
            ("restricted", "Restricted"),
        ],
        default="internal",
        required=True,
    )
    effective_date = fields.Date(string="Effective Date")
    expiry_date = fields.Date(string="Expiry Date")
    version = fields.Char(default="V1.0")
    last_trained_on = fields.Datetime(readonly=True)
    trained_by = fields.Many2one("res.users", readonly=True)
    tags_ids = fields.Many2many(
        "radwan.hr.ai.training.tag",
        "radwan_hr_ai_training_tag_rel",
        "training_id",
        "tag_id",
        string="Tags",
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "radwan_hr_ai_training_attachment_rel",
        "training_id",
        "attachment_id",
        string="Attachments",
    )
    notes = fields.Text(string="Internal Notes")
    example_ids = fields.One2many(
        "radwan.hr.ai.training.example",
        "training_id",
        string="Test Questions",
    )
    history_ids = fields.One2many(
        "radwan.hr.ai.training.history",
        "training_id",
        string="Training History",
    )
    query_log_ids = fields.Many2many(
        "radwan.hr.ai.query.log",
        "radwan_hr_ai_query_training_rel",
        "training_id",
        "query_log_id",
        string="Query Logs",
        readonly=True,
    )
    query_log_count = fields.Integer(compute="_compute_counts")
    attachment_count = fields.Integer(compute="_compute_counts")
    example_count = fields.Integer(compute="_compute_counts")
    history_count = fields.Integer(compute="_compute_counts")
    allow_ai_read = fields.Boolean(string="Allow AI to Read This Model", default=True)
    allow_ai_summary = fields.Boolean(string="Allow AI Summary", default=True)
    allow_ai_recommendation = fields.Boolean(string="Allow AI Recommendations", default=False)
    forbidden_topics = fields.Text(string="Forbidden Topics")
    response_constraints = fields.Text(string="Response Constraints")
    escalation_rule = fields.Selection(
        [
            ("no_escalation", "No Escalation"),
            ("direct_manager", "Direct Manager"),
            ("hr_officer", "HR Officer"),
            ("hr_manager", "HR Manager"),
            ("system_admin", "System Administrator"),
        ],
        default="no_escalation",
    )

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"].sudo()
        for vals in vals_list:
            if vals.get("code", _("New")) == _("New"):
                vals["code"] = sequence.next_by_code("radwan.hr.ai.training.knowledge") or _("New")
        records = super().create(vals_list)
        for record in records:
            record._log_training_history("created", new_state=record.state, notes=_("Training record created."))
        return records

    def write(self, vals):
        old_states = {record.id: record.state for record in self}
        result = super().write(vals)
        tracked_fields = {"content", "name", "knowledge_type", "hr_domain", "priority", "active"}
        if tracked_fields.intersection(vals):
            for record in self:
                record._log_training_history("updated", notes=_("Training record updated."))
        if "state" in vals:
            for record in self:
                old_state = old_states.get(record.id)
                if old_state != record.state:
                    record._log_training_history("updated", old_state=old_state, new_state=record.state)
        return result

    def _compute_counts(self):
        for record in self:
            record.query_log_count = len(record.query_log_ids)
            record.attachment_count = len(record.attachment_ids)
            record.example_count = len(record.example_ids)
            record.history_count = len(record.history_ids)

    def action_submit_review(self):
        self.write({"state": "under_review"})
        self._post_state_message(_("Submitted for review."))

    def action_approve(self):
        self.write({"state": "approved"})
        self._post_state_message(_("Approved for HR AI answers."))

    def action_set_draft(self):
        self.write({"state": "draft"})
        self._post_state_message(_("Returned to draft."))

    def action_archive_training(self):
        self.write({"state": "archived", "active": False})
        self._post_state_message(_("Archived. This knowledge will not be used in answers."))

    def action_train_rebuild(self):
        for record in self:
            if record.state != "approved":
                raise UserError(_("Only approved knowledge can be trained."))
            if not record._content_text():
                raise UserError(_("Training content is required before rebuilding knowledge."))
            record.write({"last_trained_on": fields.Datetime.now(), "trained_by": self.env.user.id})
            record._log_training_history(
                "trained",
                result_message=_(
                    "Knowledge rebuilt. TODO: push approved content to the embedding/vector database provider."
                ),
            )
            record.message_post(
                body=_(
                    "Knowledge rebuilt. TODO: connect this step to OpenAI, DeepSeek, local LLM, Odoo Knowledge, pgvector, or another vector provider."
                )
            )
        return True

    def action_test_this_knowledge(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Test This Knowledge"),
            "res_model": "radwan.hr.ai.training.test.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_training_id": self.id, "default_test_question": self.question_example or ""},
        }

    def action_view_query_logs(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Query Logs"),
            "res_model": "radwan.hr.ai.query.log",
            "view_mode": "list,form",
            "domain": [("training_knowledge_ids", "in", [self.id])],
        }

    def action_view_attachments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Attachments"),
            "res_model": "ir.attachment",
            "view_mode": "list,form",
            "domain": [("id", "in", self.attachment_ids.ids)],
            "context": {"default_res_model": self._name, "default_res_id": self.id},
        }

    def action_view_examples(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Test Questions"),
            "res_model": "radwan.hr.ai.training.example",
            "view_mode": "list,form",
            "domain": [("training_id", "=", self.id)],
            "context": {"default_training_id": self.id},
        }

    def action_view_history(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Training History"),
            "res_model": "radwan.hr.ai.training.history",
            "view_mode": "list,form",
            "domain": [("training_id", "=", self.id)],
            "context": {"default_training_id": self.id},
        }

    def _post_state_message(self, body):
        for record in self:
            record.message_post(body=body)

    def _log_training_history(self, action_type, old_state=False, new_state=False, notes=False, result_message=False):
        History = self.env["radwan.hr.ai.training.history"].sudo()
        for record in self:
            History.create(
                {
                    "training_id": record.id,
                    "action_type": action_type,
                    "user_id": self.env.uid,
                    "date": fields.Datetime.now(),
                    "old_state": old_state or "",
                    "new_state": new_state or "",
                    "notes": notes or "",
                    "result_message": result_message or "",
                }
            )

    def _content_text(self):
        self.ensure_one()
        text = html2plaintext(self.content or "")
        return re.sub(r"\s+", " ", text or "").strip()

    @api.model
    def _build_ai_training_context(self, user, question, employee=None, model_name=None, limit=8):
        records = self._get_relevant_training_knowledge(user, question, employee=employee, model_name=model_name, limit=limit)
        if not records:
            return "", records
        lines = [
            _("Approved knowledge from AI Training Center:"),
            _("Use these rules before answering. If they conflict with the question, follow the approved knowledge and Odoo permissions."),
            "",
        ]
        for index, record in enumerate(records, start=1):
            lines += [
                "%s. %s [%s]" % (index, record.name, record.code or "-"),
                _("Knowledge Type: %s") % dict(record._fields["knowledge_type"].selection).get(record.knowledge_type, record.knowledge_type),
                _("HR Domain: %s") % dict(record._fields["hr_domain"].selection).get(record.hr_domain, record.hr_domain),
                _("Confidentiality: %s") % dict(record._fields["confidentiality_level"].selection).get(
                    record.confidentiality_level, record.confidentiality_level
                ),
            ]
            if record.response_constraints:
                lines.append(_("Response Constraints: %s") % record.response_constraints.strip())
            if record.forbidden_topics:
                lines.append(_("Forbidden Topics: %s") % record.forbidden_topics.strip())
            if record.escalation_rule and record.escalation_rule != "no_escalation":
                lines.append(_("Escalation Rule: %s") % record.escalation_rule)
            lines += [_("Content:"), record._content_text(), ""]
        return "\n".join(lines), records

    @api.model
    def _get_relevant_training_knowledge(self, user, question, employee=None, model_name=None, limit=8):
        today = fields.Date.context_today(self)
        domain = [
            ("active", "=", True),
            ("state", "=", "approved"),
            "|",
            ("effective_date", "=", False),
            ("effective_date", "<=", today),
            "|",
            ("expiry_date", "=", False),
            ("expiry_date", ">=", today),
        ]
        candidates = self.sudo().search(domain, order="priority asc, write_date desc, id desc", limit=80)
        allowed = candidates.filtered(lambda record: record._can_apply_to_ai_user(user, employee=employee, model_name=model_name))
        question_text = self._normalize_text(question)
        scored = []
        for record in allowed:
            score = record._relevance_score(question_text)
            if score or record.knowledge_type in ("command", "restriction", "escalation") or record.hr_domain == "general":
                scored.append((score, record.priority, record.write_date or record.create_date, record.id))
        scored.sort(key=lambda item: (-item[0], item[1], item[2] or fields.Datetime.now(), item[3]))
        selected_ids = [item[3] for item in scored[:limit]]
        return self.browse(selected_ids)

    def _can_apply_to_ai_user(self, user, employee=None, model_name=None):
        self.ensure_one()
        if self.allowed_company_ids and not (self.allowed_company_ids & user.company_ids):
            return False
        if self.allowed_groups_ids:
            group_xmlids = [group.get_external_id().get(group.id) for group in self.allowed_groups_ids]
            if not any(xmlid and user.has_group(xmlid) for xmlid in group_xmlids):
                return False
        if self.related_model_id and model_name and self.related_model_id.model != model_name:
            return False
        security = self.env["radwan.hr.ai.security"].with_user(user)
        if self.confidentiality_level in ("hr_only", "restricted") and not security._is_hr_power_user():
            return False
        if self.confidentiality_level == "managers" and not (security._is_hr_power_user() or employee and employee.parent_id.user_id == user):
            return False
        return True

    def _relevance_score(self, question_text):
        self.ensure_one()
        if not question_text:
            return 0
        searchable = " ".join(
            [
                self.name or "",
                self.description or "",
                self._content_text(),
                self.question_example or "",
                self.answer_example or "",
                self.hr_domain or "",
                " ".join(self.tags_ids.mapped("name")),
            ]
        )
        haystack = self._normalize_text(searchable)
        score = 0
        for token in set(question_text.split()):
            if len(token) < 3:
                continue
            if token in haystack:
                score += 1
        if self.hr_domain and self.hr_domain in question_text:
            score += 3
        if self.knowledge_type in ("restriction", "command"):
            score += 1
        return score

    @api.model
    def _normalize_text(self, text):
        text = re.sub(r"<[^>]+>", " ", text or "")
        text = re.sub(r"[^\w\u0600-\u06FF]+", " ", text.lower())
        return re.sub(r"\s+", " ", text).strip()


class RadwanHrAiTrainingExample(models.Model):
    _name = "radwan.hr.ai.training.example"
    _description = "HR AI Training Example"
    _order = "id desc"

    training_id = fields.Many2one("radwan.hr.ai.training.knowledge", required=True, ondelete="cascade")
    question = fields.Text(required=True)
    expected_answer = fields.Text()
    active = fields.Boolean(default=True)
    notes = fields.Text()


class RadwanHrAiTrainingHistory(models.Model):
    _name = "radwan.hr.ai.training.history"
    _description = "HR AI Training History"
    _order = "date desc, id desc"

    training_id = fields.Many2one("radwan.hr.ai.training.knowledge", required=True, ondelete="cascade")
    action_type = fields.Selection(
        [
            ("created", "Created"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("trained", "Trained"),
            ("tested", "Tested"),
            ("archived", "Archived"),
            ("updated", "Updated"),
            ("used_in_answer", "Used in Answer"),
        ],
        required=True,
    )
    user_id = fields.Many2one("res.users", required=True)
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    old_state = fields.Char()
    new_state = fields.Char()
    notes = fields.Text()
    result_message = fields.Text()
