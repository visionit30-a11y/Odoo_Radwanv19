# -*- coding: utf-8 -*-

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
                safe_body = escape(message.body or "").replace("\n", "<br/>")
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
                safe_question = escape(record.question or "").replace("\n", "<br/>")
                safe_answer = escape(record.answer or "").replace("\n", "<br/>")
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
        answer = llm_answer or self._compose_answer(scope)
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

        employee_rows = security._safe_search_read(
            "hr.employee",
            [("id", "in", employee_ids)],
            ["name", "department_id", "job_title", "work_email", "mobile_phone"],
            limit=10,
        )
        if employee_rows:
            lines.append("Employees:")
            for emp in employee_rows:
                lines.append(
                    "- %s | %s | %s"
                    % (
                        emp.get("name", "-"),
                        self._rel_name(emp.get("department_id")),
                        emp.get("job_title") or "-",
                    )
                )

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
        allowed = ", ".join(source["label"] for source in scope["allowed_sources"]) or "None"
        return "\n".join(
            [
                "User: %s" % scope["user_name"],
                "Employee: %s" % (scope["employee_name"] or "-"),
                "Visible employees: %s" % len(scope["visible_employee_ids"]),
                "Allowed sources: %s" % allowed,
            ]
        )

    def _rel_name(self, value):
        if isinstance(value, (list, tuple)) and len(value) > 1:
            return value[1]
        return value or "-"


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
