# -*- coding: utf-8 -*-

import html
import re

from markupsafe import escape

from odoo import _, api, fields, models


class RadwanHrAiEmployeeAssistant(models.Model):
    _name = "radwan.hr.ai.employee.assistant"
    _description = "Employee HR AI Assistant"
    _order = "create_date desc, id desc"

    name = fields.Char(default="Employee HR Assistant", readonly=True)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user, readonly=True)
    employee_id = fields.Many2one("hr.employee", compute="_compute_employee_id", store=False)
    question = fields.Text()
    input_text = fields.Text(string="Message")
    answer = fields.Text(readonly=True)
    scope_summary = fields.Text(readonly=True)
    message_ids = fields.One2many(
        "radwan.hr.ai.employee.message",
        "assistant_id",
        string="Conversation",
        readonly=True,
    )
    chat_html = fields.Html(compute="_compute_chat_html", sanitize=False)
    state = fields.Selection(
        [("draft", "Draft"), ("answered", "Answered"), ("blocked", "Blocked")],
        default="draft",
        readonly=True,
    )

    @api.depends("user_id")
    def _compute_employee_id(self):
        security = self.env["radwan.hr.ai.security"]
        for record in self:
            record.employee_id = security._current_employee()

    @api.depends("message_ids.body", "message_ids.role", "message_ids.create_date", "question", "answer", "state")
    def _compute_chat_html(self):
        for record in self:
            messages = record.message_ids.sorted(lambda message: (message.create_date, message.id))
            parts = [
                """
                <div style="background:#f5f8fb;border:1px solid #dce6ef;border-radius:16px;
                            padding:18px;min-height:420px;max-height:640px;overflow-y:auto;">
                """
            ]
            if not messages and not record.answer:
                parts.append(
                    """
                    <div style="height:340px;display:flex;align-items:center;justify-content:center;
                                color:#64748b;text-align:center;">
                        <div>
                            <div style="font-size:28px;font-weight:700;color:#0b5e93;margin-bottom:8px;">HR AI</div>
                            <div>Ask a secure HR question. Answers use only your allowed Odoo data.</div>
                        </div>
                    </div>
                    """
                )
            for message in messages:
                is_user = message.role == "user"
                bubble_bg = "#0b5e93" if is_user else "#ffffff"
                text_color = "#ffffff" if is_user else "#1f2937"
                align = "flex-end" if is_user else "flex-start"
                label = _("You") if is_user else _("HR AI")
                safe_body = escape(record._plain_chat_body(message.body)).replace("\n", "<br/>")
                parts.append(
                    """
                    <div style="display:flex;justify-content:%s;margin:10px 0;">
                        <div style="max-width:78%%;">
                            <div style="font-size:12px;color:#64748b;margin:0 8px 4px;">%s</div>
                            <div style="background:%s;color:%s;border-radius:18px;padding:12px 14px;
                                        box-shadow:0 6px 18px rgba(15,23,42,.08);line-height:1.7;
                                        white-space:pre-wrap;direction:auto;">%s</div>
                        </div>
                    </div>
                    """
                    % (align, escape(label), bubble_bg, text_color, safe_body)
                )
            if not messages and record.answer:
                safe_question = escape(record._plain_chat_body(record.question)).replace("\n", "<br/>")
                safe_answer = escape(record._plain_chat_body(record.answer)).replace("\n", "<br/>")
                parts.append(
                    """
                    <div style="display:flex;justify-content:flex-end;margin:10px 0;">
                        <div style="max-width:78%%;">
                            <div style="font-size:12px;color:#64748b;margin:0 8px 4px;">%s</div>
                            <div style="background:#0b5e93;color:#fff;border-radius:18px;padding:12px 14px;line-height:1.7;direction:auto;">%s</div>
                        </div>
                    </div>
                    <div style="display:flex;justify-content:flex-start;margin:10px 0;">
                        <div style="max-width:78%%;">
                            <div style="font-size:12px;color:#64748b;margin:0 8px 4px;">%s</div>
                            <div style="background:#fff;color:#1f2937;border-radius:18px;padding:12px 14px;line-height:1.7;direction:auto;">%s</div>
                        </div>
                    </div>
                    """
                    % (_("You"), safe_question, _("HR AI"), safe_answer)
                )
            parts.append("</div>")
            record.chat_html = "".join(parts)

    def action_send_message(self):
        for record in self:
            question = (record.input_text or record.question or "").strip()
            if not question:
                continue
            record._answer_question(question, add_user_message=True)
            record.input_text = False
        return True

    def action_generate_answer(self):
        for record in self:
            record._answer_question((record.question or record.input_text or "").strip(), add_user_message=True)
        return True

    def _answer_question(self, question, add_user_message=False):
        if not question:
            return False
        self.ensure_one()
        if add_user_message:
            self.env["radwan.hr.ai.employee.message"].create(
                {
                    "assistant_id": self.id,
                    "role": "user",
                    "body": question,
                }
            )
        scope = self.env["radwan.hr.ai.security"].build_user_scope()
        if not scope["employee_id"] and not scope["is_hr_power_user"]:
            self._write_blocked(_("No employee profile is linked to your user."))
            return False
        secure_context = self._compose_secure_context(scope)
        scope_text = self._scope_text(scope)
        llm_answer = self.env["radwan.hr.ai.llm.gateway"].generate(
            question,
            secure_context,
            scope_text,
        )
        answer = self._plain_chat_body(llm_answer or self._compose_answer(scope))
        model_names = ", ".join(source["model"] for source in scope["allowed_sources"])
        self.write(
            {
                "question": question,
                "answer": answer,
                "scope_summary": scope_text,
                "state": "answered",
            }
        )
        self.env["radwan.hr.ai.employee.message"].create(
            {
                "assistant_id": self.id,
                "role": "assistant",
                "body": answer,
            }
        )
        self.env["radwan.hr.ai.query.log"].create(
            {
                "user_id": self.env.uid,
                "employee_id": scope["employee_id"] or False,
                "audience": "employee",
                "question": question,
                "answer": answer,
                "allowed_model_names": model_names,
                "visible_employee_count": len(scope["visible_employee_ids"]),
            }
        )
        return True

    def _write_blocked(self, reason):
        reason = self._plain_chat_body(reason)
        self.write({"answer": reason, "scope_summary": reason, "state": "blocked"})
        self.env["radwan.hr.ai.employee.message"].create(
            {
                "assistant_id": self.id,
                "role": "assistant",
                "body": reason,
            }
        )
        self.env["radwan.hr.ai.query.log"].create(
            {
                "user_id": self.env.uid,
                "employee_id": False,
                "audience": "employee",
                "question": self.question,
                "answer": reason,
                "is_blocked": True,
                "blocked_reason": reason,
            }
        )

    def _compose_answer(self, scope):
        question = (self.question or "").lower()
        security = self.env["radwan.hr.ai.security"]
        employee_ids = scope["visible_employee_ids"] or [0]
        lines = [
            _("Here is a secure summary based on your current Odoo permissions:"),
            "",
        ]

        employee_rows = security._safe_search_read(
            "hr.employee",
            [("id", "in", employee_ids)],
            ["name", "department_id", "job_title", "work_email", "mobile_phone"],
            limit=5,
        )
        if employee_rows:
            emp = employee_rows[0]
            lines += [
                _("Employee: %s") % emp.get("name", "-"),
                _("Department: %s") % self._rel_name(emp.get("department_id")),
                _("Job Title: %s") % (emp.get("job_title") or "-"),
            ]

        if any(word in question for word in ["leave", "vacation", "اجاز", "إجاز"]):
            count = security._safe_metric_count("hr.leave")
            lines.append(_("Leave records visible to you: %s") % count)

        if any(word in question for word in ["attendance", "حضور", "دوام", "انصراف"]):
            count = security._safe_metric_count("hr.attendance")
            lines.append(_("Attendance records visible to you: %s") % count)

        if any(word in question for word in ["salary", "payroll", "راتب", "رواتب"]):
            count = security._safe_metric_count("hr.payslip")
            lines.append(_("Payslips visible to you: %s") % count)

        if any(word in question for word in ["loan", "advance", "سلف", "سلفة"]):
            count = security._safe_metric_count("hr.employee.loan")
            lines.append(_("Loan records visible to you: %s") % count)

        if any(word in question for word in ["task", "ticket", "تذكرة", "مهام", "مهمة"]):
            task_count = security._safe_count("project.task", [("user_ids", "in", [self.env.uid])])
            ticket_count = security._safe_count("helpdesk.ticket", ["|", ("user_id", "=", self.env.uid), ("create_uid", "=", self.env.uid)])
            lines.append(_("Tasks assigned to you: %s") % task_count)
            lines.append(_("Tickets related to you: %s") % ticket_count)

        lines += [
            "",
            _("Security note: this answer was generated only from models and records your user can read."),
        ]
        return "\n".join(lines)

    def _compose_secure_context(self, scope):
        security = self.env["radwan.hr.ai.security"]
        employee_ids = scope["visible_employee_ids"] or [0]
        lines = [self._scope_text(scope), ""]
        employee_fields = self._available_employee_context_fields()
        employee_rows = security._safe_search_read("hr.employee", [("id", "in", employee_ids)], employee_fields, limit=10)
        if employee_rows:
            lines.append("Employee profile records:")
            for emp in employee_rows:
                lines += self._format_employee_context(emp)

        contract_lines = self._compose_contract_context(employee_ids)
        if contract_lines:
            lines.append("")
            lines += contract_lines

        metrics = [
            ("hr.leave", "Leaves", "employee_id"),
            ("hr.attendance", "Attendance", "employee_id"),
            ("hr.payslip", "Payslips", "employee_id"),
            ("hr.employee.loan", "Loans", "employee_id"),
        ]
        lines.append("")
        lines.append("Visible record counts:")
        for model_name, label, employee_field in metrics:
            count = security._safe_metric_count(model_name, employee_field)
            lines.append("- %s: %s" % (label, count))

        task_count = security._safe_count("project.task", [("user_ids", "in", [self.env.uid])])
        ticket_count = security._safe_count(
            "helpdesk.ticket",
            ["|", ("user_id", "=", self.env.uid), ("create_uid", "=", self.env.uid)],
        )
        lines.append("- Tasks assigned to current user: %s" % task_count)
        lines.append("- Tickets related to current user: %s" % ticket_count)
        return "\n".join(lines)

    def _scope_text(self, scope):
        allowed_lines = []
        for source in scope["allowed_sources"]:
            label = source["label"]
            description = source.get("description")
            allowed_lines.append("- %s%s" % (label, ": %s" % description if description else ""))
        allowed = "\n".join(allowed_lines) or "None"
        return "\n".join(
            [
                "User: %s" % scope["user_name"],
                "Employee: %s" % (scope["employee_name"] or "-"),
                "Visible employees: %s" % len(scope["visible_employee_ids"]),
                "Allowed sources:",
                allowed,
            ]
        )

    def _rel_name(self, value):
        if isinstance(value, (list, tuple)) and len(value) > 1:
            return value[1]
        return value or "-"

    def _plain_chat_body(self, value):
        text = html.unescape(value or "")
        text = text.replace("\\n", "\n")
        text = re.sub(r"(?i)<\s*br\s*/?\s*>", "\n", text)
        text = re.sub(r"(?i)</\s*p\s*>", "\n", text)
        text = re.sub(r"(?i)<\s*p[^>]*>", "", text)
        text = re.sub(r"(?i)</?\s*(div|span|strong|b|em|i|ul|ol|li|table|thead|tbody|tr|td|th)[^>]*>", "", text)
        text = re.sub(r"(?m)^\s*[-•]\s*", "- ", text)
        text = re.sub(r"\s*(?:<br\s*/?>|&lt;br\s*/?&gt;)\s*", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"(?m)^\s*\*\s+", "- ", text)
        text = re.sub(r"\s+\n", "\n", text)
        text = re.sub(r"\n\s+", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _available_model_fields(self, model_name, wanted_fields):
        if model_name not in self.env:
            return []
        Model = self.env[model_name]
        return [field for field in wanted_fields if field in Model._fields]

    def _available_employee_context_fields(self):
        wanted_fields = [
            "id",
            "name",
            "radwan_employee_code",
            "employee_number",
            "registration_number",
            "department_id",
            "parent_id",
            "job_id",
            "job_title",
            "work_email",
            "private_email",
            "mobile_phone",
            "work_phone",
            "birthday",
            "country_id",
            "identification_id",
            "passport_id",
            "emergency_contact",
            "emergency_phone",
            "bank_account_id",
            "radwan_joining_date",
            "radwan_contract_number",
            "radwan_contract_start_date",
            "radwan_contract_end_date",
            "radwan_contract_end_date_display",
            "radwan_contract_status",
            "radwan_passport_expiry_date",
            "radwan_passport_expiry_date_display",
            "radwan_passport_status",
            "radwan_id_expiry_date",
            "radwan_id_expiry_date_display",
            "radwan_id_expiry_hijri",
            "radwan_id_status",
            "radwan_medical_insurance_company",
            "radwan_medical_policy_number",
            "radwan_medical_insurance_class",
            "radwan_medical_insurance_end",
            "radwan_medical_insurance_end_display",
            "radwan_medical_insurance_status",
            "remaining_leaves",
            "remaining_leave_days",
            "allocation_remaining_display",
        ]
        return self._available_model_fields("hr.employee", wanted_fields)

    def _compose_contract_context(self, employee_ids):
        security = self.env["radwan.hr.ai.security"]
        if not security._can_use_model_in_ai("hr.version"):
            return []
        fields_to_read = self._available_model_fields(
            "hr.version",
            [
                "id",
                "name",
                "employee_id",
                "date_start",
                "date_end",
                "contract_date_start",
                "contract_date_end",
                "contract_type_id",
                "employee_type",
                "resource_calendar_id",
                "state",
                "wage",
                "radwan_basic",
                "radwan_housing",
                "radwan_transportation",
                "radwan_other_allowances",
                "radwan_total_salary",
                "radwan_contract_other_notes",
                "radwan_non_renewal",
                "trial_date_end",
                "radwan_trial_start_date",
                "radwan_extended_trial_start_date",
                "radwan_extended_trial_end_date",
            ],
        )
        if not fields_to_read:
            return []
        order_parts = [
            "%s desc" % field
            for field in ("contract_date_start", "date_start", "id")
            if field in fields_to_read
        ]
        rows = security._safe_search_read(
            "hr.version",
            [("employee_id", "in", employee_ids or [0])],
            fields_to_read,
            limit=20,
            order=", ".join(order_parts) or None,
        )
        if not rows:
            return []
        lines = ["Contract/version records:"]
        for contract in rows:
            lines += self._format_contract_context(contract)
        return lines

    def _format_contract_context(self, contract):
        values = [
            ("Employee", self._rel_name(contract.get("employee_id"))),
            ("Reference", contract.get("name")),
            ("Contract Start Date", contract.get("contract_date_start") or contract.get("date_start")),
            ("Contract End Date", contract.get("contract_date_end") or contract.get("date_end")),
            ("Contract Type", self._rel_name(contract.get("contract_type_id"))),
            ("Employee Type", contract.get("employee_type")),
            ("Working Schedule", self._rel_name(contract.get("resource_calendar_id"))),
            ("Status", contract.get("state")),
            ("Wage", contract.get("wage")),
            ("Basic Salary", contract.get("radwan_basic")),
            ("Housing", contract.get("radwan_housing")),
            ("Transportation", contract.get("radwan_transportation")),
            ("Other Allowances", contract.get("radwan_other_allowances")),
            ("Total Salary", contract.get("radwan_total_salary")),
            ("Non-Renewal", contract.get("radwan_non_renewal")),
            ("Trial Start Date", contract.get("radwan_trial_start_date")),
            ("Trial End Date", contract.get("trial_date_end")),
            ("Extended Trial Start Date", contract.get("radwan_extended_trial_start_date")),
            ("Extended Trial End Date", contract.get("radwan_extended_trial_end_date")),
            ("Other Notes", contract.get("radwan_contract_other_notes")),
        ]
        lines = ["- Contract/Version ID: %s" % contract.get("id")]
        for label, value in values:
            if value not in (False, None, ""):
                lines.append("  - %s: %s" % (label, value))
        return lines

    def _format_employee_context(self, employee):
        values = [
            ("Name", employee.get("name")),
            (
                "Employee Number",
                employee.get("radwan_employee_code") or employee.get("employee_number") or employee.get("registration_number"),
            ),
            ("Department", self._rel_name(employee.get("department_id"))),
            ("Direct Manager", self._rel_name(employee.get("parent_id"))),
            ("Job Position", self._rel_name(employee.get("job_id")) or employee.get("job_title")),
            ("Job Title", employee.get("job_title")),
            ("Nationality", self._rel_name(employee.get("country_id"))),
            ("Birthday", employee.get("birthday")),
            ("Joining Date", employee.get("radwan_joining_date")),
            ("Contract Number", employee.get("radwan_contract_number")),
            ("Contract Start Date", employee.get("radwan_contract_start_date")),
            ("Contract End Date", employee.get("radwan_contract_end_date_display") or employee.get("radwan_contract_end_date")),
            ("Contract Status", employee.get("radwan_contract_status")),
            ("ID Number", employee.get("identification_id")),
            ("ID Expiry Date", employee.get("radwan_id_expiry_date_display") or employee.get("radwan_id_expiry_date")),
            ("ID Expiry Date Hijri", employee.get("radwan_id_expiry_hijri")),
            ("ID Status", employee.get("radwan_id_status")),
            ("Passport Number", employee.get("passport_id")),
            ("Passport Expiry Date", employee.get("radwan_passport_expiry_date_display") or employee.get("radwan_passport_expiry_date")),
            ("Passport Status", employee.get("radwan_passport_status")),
            ("Mobile Phone", employee.get("mobile_phone")),
            ("Work Phone", employee.get("work_phone")),
            ("Personal Email", employee.get("private_email")),
            ("Work Email", employee.get("work_email")),
            ("Bank Account", self._rel_name(employee.get("bank_account_id"))),
            ("Emergency Contact", employee.get("emergency_contact")),
            ("Emergency Phone", employee.get("emergency_phone")),
            ("Remaining Leaves", employee.get("remaining_leaves") or employee.get("remaining_leave_days") or employee.get("allocation_remaining_display")),
            ("Medical Insurance Company", employee.get("radwan_medical_insurance_company")),
            ("Medical Policy Number", employee.get("radwan_medical_policy_number")),
            ("Medical Insurance End Date", employee.get("radwan_medical_insurance_end_display") or employee.get("radwan_medical_insurance_end")),
            ("Medical Insurance Class", employee.get("radwan_medical_insurance_class")),
            ("Medical Insurance Status", employee.get("radwan_medical_insurance_status")),
        ]
        lines = ["- Employee ID: %s" % employee.get("id")]
        for label, value in values:
            if value not in (False, None, ""):
                lines.append("  - %s: %s" % (label, value))
        if employee.get("id"):
            lines.append("  - Employee Image URL: /web/image/hr.employee/%s/image_128" % employee["id"])
        return lines


class RadwanHrAiEmployeeMessage(models.Model):
    _name = "radwan.hr.ai.employee.message"
    _description = "Employee HR AI Chat Message"
    _order = "create_date asc, id asc"

    assistant_id = fields.Many2one(
        "radwan.hr.ai.employee.assistant",
        required=True,
        ondelete="cascade",
        index=True,
    )
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user, readonly=True)
    role = fields.Selection(
        [("user", "User"), ("assistant", "Assistant")],
        required=True,
        default="user",
    )
    body = fields.Text(required=True)
