# -*- coding: utf-8 -*-

import html
import re

from markupsafe import escape

from odoo import _, api, fields, models


class RadwanHrAiEmployeeAssistant(models.Model):
    _name = "radwan.hr.ai.employee.assistant"
    _description = "Employee HR AI Assistant"
    _order = "create_date desc, id desc"

    DETAIL_CONTEXT_LIMIT = 12
    DETAIL_CONTEXT_FIELD_LIMIT = 30
    DETAIL_CONTEXT_FIELDS = {
        "hr.attendance": [
            "employee_id",
            "check_in",
            "check_out",
            "worked_hours",
            "radwan_approval_state",
            "radwan_check_in_source",
            "radwan_check_out_source",
            "radwan_location_status",
            "radwan_location_warning_message",
            "radwan_location_validity_status",
            "radwan_location_validity_warning",
            "radwan_nearest_attendance_location_id",
            "radwan_distance_to_nearest_location",
            "radwan_allowed_radius",
            "radwan_checkin_location_id",
            "radwan_checkout_location_id",
            "radwan_checkin_actual_location",
            "radwan_checkout_actual_location",
            "radwan_checkin_maps_url",
            "radwan_checkout_maps_url",
            "radwan_checkin_latitude",
            "radwan_checkin_longitude",
            "radwan_checkout_latitude",
            "radwan_checkout_longitude",
        ],
        "hr.leave": [
            "employee_id",
            "name",
            "holiday_status_id",
            "request_date_from",
            "request_date_to",
            "date_from",
            "date_to",
            "duration_display",
            "number_of_days",
            "state",
            "create_date",
        ],
        "hr.payslip": [
            "employee_id",
            "name",
            "date_from",
            "date_to",
            "state",
            "basic_wage",
            "gross_wage",
            "net_wage",
            "create_date",
        ],
        "hr.employee.loan": [
            "employee_id",
            "name",
            "loan_date",
            "date",
            "amount",
            "loan_amount",
            "total_amount",
            "paid_amount",
            "remaining_amount",
            "state",
            "create_date",
        ],
        "project.task": [
            "name",
            "project_id",
            "user_ids",
            "date_deadline",
            "stage_id",
            "priority",
            "create_date",
        ],
        "helpdesk.ticket": [
            "name",
            "user_id",
            "partner_id",
            "stage_id",
            "priority",
            "create_date",
        ],
        "approval.request": [
            "name",
            "request_owner_id",
            "employee_id",
            "category_id",
            "request_status",
            "date_start",
            "date_end",
            "reason",
            "create_date",
        ],
        "survey.user_input": [
            "survey_id",
            "partner_id",
            "email",
            "state",
            "start_datetime",
            "end_datetime",
            "create_date",
        ],
        "radwan.attendance.permission": [
            "employee_id",
            "attendance_id",
            "request_type",
            "request_date",
            "reason",
            "state",
            "create_date",
        ],
    }
    DETAIL_CONTEXT_ORDER = {
        "hr.attendance": "check_in desc, id desc",
        "hr.leave": "request_date_from desc, date_from desc, id desc",
        "hr.payslip": "date_to desc, date_from desc, id desc",
        "hr.employee.loan": "loan_date desc, date desc, id desc",
        "project.task": "date_deadline desc, id desc",
        "helpdesk.ticket": "create_date desc, id desc",
        "approval.request": "create_date desc, id desc",
        "survey.user_input": "create_date desc, id desc",
        "radwan.attendance.permission": "create_date desc, id desc",
    }

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
                safe_body = record._chat_body_html(message.body)
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
                safe_question = record._chat_body_html(record.question)
                safe_answer = record._chat_body_html(record.answer)
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
        employee = self.env["hr.employee"].browse(scope["employee_id"]) if scope["employee_id"] else self.env["hr.employee"]
        training_context, training_records = self.env["radwan.hr.ai.training.knowledge"]._build_ai_training_context(
            self.env.user,
            question,
            employee=employee,
        )
        if training_context:
            secure_context = "\n\n".join([training_context, secure_context])
        if self._is_payslip_report_request(question):
            answer = self._compose_payslip_report_answer(question, scope)
            model_names = ", ".join(dict.fromkeys(source["model"] for source in scope["allowed_sources"]))
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
                    "training_knowledge_ids": [(6, 0, training_records.ids)],
                    "visible_employee_count": len(scope["visible_employee_ids"]),
                }
            )
            self._log_used_training_knowledge(training_records, question, answer)
            return True
        if self._is_employee_report_request(question):
            answer = self._compose_employee_report_answer(scope)
            model_names = ", ".join(dict.fromkeys(source["model"] for source in scope["allowed_sources"]))
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
                    "training_knowledge_ids": [(6, 0, training_records.ids)],
                    "visible_employee_count": len(scope["visible_employee_ids"]),
                }
            )
            self._log_used_training_knowledge(training_records, question, answer)
            return True
        llm_answer = self.env["radwan.hr.ai.llm.gateway"].generate(
            question,
            secure_context,
            scope_text,
        )
        answer = self._plain_chat_body(llm_answer or self._compose_answer(scope))
        model_names = ", ".join(dict.fromkeys(source["model"] for source in scope["allowed_sources"]))
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
                "training_knowledge_ids": [(6, 0, training_records.ids)],
                "visible_employee_count": len(scope["visible_employee_ids"]),
            }
        )
        self._log_used_training_knowledge(training_records, question, answer)
        return True

    def _log_used_training_knowledge(self, training_records, question, answer):
        for training in training_records.sudo():
            training._log_training_history(
                "used_in_answer",
                notes=(question or "")[:500],
                result_message=(answer or "")[:500],
            )

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

        detail_lines = self._compose_allowed_record_context(scope, employee_ids)
        if detail_lines:
            lines.append("")
            lines += detail_lines

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

    def _compose_allowed_record_context(self, scope, employee_ids):
        allowed_sources = scope.get("allowed_sources") or []
        allowed_models = []
        labels_by_model = {}
        for source in allowed_sources:
            model_name = source.get("model")
            if model_name and model_name not in allowed_models:
                allowed_models.append(model_name)
                labels_by_model[model_name] = source.get("label") or model_name

        lines = []
        for model_name in allowed_models:
            if model_name in ("hr.employee", "hr.version", "ir.attachment"):
                continue
            model_lines = self._compose_model_record_context(
                model_name,
                labels_by_model.get(model_name, model_name),
                employee_ids,
            )
            if model_lines:
                lines += model_lines
        return lines

    def _compose_model_record_context(self, model_name, label, employee_ids):
        security = self.env["radwan.hr.ai.security"]
        if model_name not in self.env or not security._can_use_model_in_ai(model_name):
            return []
        fields_to_read = self._context_fields_for_model(model_name)
        if not fields_to_read:
            return []
        rows = security._safe_search_read(
            model_name,
            self._context_domain_for_model(model_name, employee_ids),
            fields_to_read,
            limit=self.DETAIL_CONTEXT_LIMIT,
            order=self._context_order_for_model(model_name),
        )
        if not rows:
            return []
        lines = ["Recent %s records (%s):" % (label, model_name)]
        for row in rows:
            lines += self._format_generic_record_context(model_name, row)
        return lines

    def _is_employee_report_request(self, question):
        text = (question or "").lower()
        report_words = ("pdf", "تقرير", "طباع", "print", "report")
        employee_words = ("موظف", "الموظفين", "employee", "employees", "اسماء", "أسماء", "الاسماء", "الأسماء")
        return any(word in text for word in report_words) and any(word in text for word in employee_words)

    def _is_payslip_report_request(self, question):
        text = (question or "").lower()
        report_words = ("pdf", "qweb", "تقرير", "طباع", "print", "report", "صورة")
        payslip_words = (
            "payslip",
            "pay slip",
            "salary slip",
            "مسير",
            "راتب",
            "رواتب",
            "باي سليب",
            "باى سليب",
            "سليب",
        )
        return any(word in text for word in report_words) and any(word in text for word in payslip_words)

    def _compose_payslip_report_answer(self, question, scope):
        security = self.env["radwan.hr.ai.security"]
        if "hr.payslip" not in self.env or not security._can_use_model_in_ai("hr.payslip"):
            return _("Payslip data is not available under your current HR AI permissions.")
        payslip = self._find_report_payslip(question, scope)
        if not payslip:
            return _("No payslip records are available under your current HR AI permissions.")
        report_name = "om_hr_payroll.report_payslip"
        html_url = "/report/html/%s/%s" % (report_name, payslip.id)
        pdf_url = "/report/pdf/%s/%s" % (report_name, payslip.id)
        employee_name = payslip.employee_id.name or "-"
        period = "%s - %s" % (payslip.date_from or "-", payslip.date_to or "-")
        return "\n".join(
            [
                _("Payslip report is ready."),
                _("Employee: %s") % employee_name,
                _("Period: %s") % period,
                _("Open printable report: %s") % html_url,
                _("Download PDF: %s") % pdf_url,
            ]
        )

    def _find_report_payslip(self, question, scope):
        employee_ids = scope.get("visible_employee_ids") or [0]
        domain = [("employee_id", "in", employee_ids)]
        question_text = (question or "").lower()
        try:
            with self.env.cr.savepoint():
                payslips = self.env["hr.payslip"].search(domain, order="date_to desc, date_from desc, id desc", limit=30)
        except Exception:
            return self.env["hr.payslip"].browse()
        if not payslips:
            return payslips
        for payslip in payslips:
            employee_name = (payslip.employee_id.name or "").lower()
            name_parts = [part for part in re.split(r"\s+", employee_name) if len(part) >= 3]
            if employee_name and employee_name in question_text:
                return payslip
            if name_parts and any(part in question_text for part in name_parts):
                return payslip
        current_employee_id = scope.get("employee_id")
        if current_employee_id:
            own_payslip = payslips.filtered(lambda slip: slip.employee_id.id == current_employee_id)[:1]
            if own_payslip:
                return own_payslip
        return payslips[:1]

    def _compose_employee_report_answer(self, scope):
        security = self.env["radwan.hr.ai.security"]
        if not security._can_use_model_in_ai("hr.employee"):
            return _("Employee data is not available under your current HR AI permissions.")
        employee_rows = self._employee_report_rows(scope)
        if not employee_rows:
            return _("No employee records are available under your current HR AI permissions.")
        html_url = "/report/html/radwan_hr_ai_employee.report_hr_ai_employee_names/%s" % self.id
        pdf_url = "/report/pdf/radwan_hr_ai_employee.report_hr_ai_employee_names/%s" % self.id
        return "\n".join(
            [
                _("Employee names report is ready."),
                _("Visible employees: %s") % len(employee_rows),
                _("Open printable report: %s") % html_url,
                _("Download PDF: %s") % pdf_url,
            ]
        )

    def _employee_report_rows(self, scope=None):
        self.ensure_one()
        security = self.env["radwan.hr.ai.security"]
        if not security._can_use_model_in_ai("hr.employee"):
            return []
        scope = scope or security.build_user_scope()
        employee_ids = scope.get("visible_employee_ids") or [0]
        fields_to_read = self._available_model_fields(
            "hr.employee",
            [
                "name",
                "radwan_employee_code",
                "employee_number",
                "registration_number",
                "department_id",
                "job_id",
                "job_title",
                "parent_id",
                "work_email",
                "mobile_phone",
            ],
        )
        rows = security._safe_search_read(
            "hr.employee",
            [("id", "in", employee_ids)],
            fields_to_read,
            limit=500,
            order="name asc",
        )
        result = []
        for index, row in enumerate(rows, start=1):
            result.append(
                {
                    "index": index,
                    "name": row.get("name") or "-",
                    "employee_number": row.get("radwan_employee_code")
                    or row.get("employee_number")
                    or row.get("registration_number")
                    or "-",
                    "department": self._rel_name(row.get("department_id")),
                    "job": self._rel_name(row.get("job_id")) or row.get("job_title") or "-",
                    "manager": self._rel_name(row.get("parent_id")),
                    "work_email": row.get("work_email") or "-",
                    "mobile_phone": row.get("mobile_phone") or "-",
                }
            )
        return result

    def _context_domain_for_model(self, model_name, employee_ids):
        Model = self.env[model_name]
        if model_name == "project.task":
            return [("user_ids", "in", [self.env.uid])]
        if model_name == "helpdesk.ticket":
            return ["|", ("user_id", "=", self.env.uid), ("create_uid", "=", self.env.uid)]
        if "employee_id" in Model._fields:
            return [("employee_id", "in", employee_ids or [0])]
        if "employee_ids" in Model._fields:
            return [("employee_ids", "in", employee_ids or [0])]
        if "user_id" in Model._fields:
            return [("user_id", "=", self.env.uid)]
        if "user_ids" in Model._fields:
            return [("user_ids", "in", [self.env.uid])]
        return []

    def _context_order_for_model(self, model_name):
        order = self.DETAIL_CONTEXT_ORDER.get(model_name)
        if order:
            return self._sanitize_context_order(model_name, order)
        Model = self.env[model_name]
        for field_name in ("date", "request_date", "date_from", "create_date", "id"):
            if field_name == "id" or field_name in Model._fields:
                return "%s desc" % field_name
        return None

    def _sanitize_context_order(self, model_name, order):
        if not order or model_name not in self.env:
            return None
        fields_map = self.env[model_name]._fields
        valid_parts = []
        for part in order.split(","):
            tokens = part.strip().split()
            if not tokens:
                continue
            field_name = tokens[0]
            if field_name == "id" or field_name in fields_map:
                direction = tokens[1].lower() if len(tokens) > 1 else "asc"
                valid_parts.append("%s %s" % (field_name, "desc" if direction == "desc" else "asc"))
        return ", ".join(valid_parts) or None

    def _context_fields_for_model(self, model_name):
        configured = self.DETAIL_CONTEXT_FIELDS.get(model_name)
        if configured:
            return self._available_model_fields(model_name, configured)
        return self._generic_context_fields(model_name)

    def _generic_context_fields(self, model_name):
        Model = self.env[model_name]
        safe_types = {"char", "text", "selection", "many2one", "date", "datetime", "float", "integer", "monetary", "boolean"}
        skipped_names = {
            "message_ids",
            "message_follower_ids",
            "message_partner_ids",
            "activity_ids",
            "website_message_ids",
            "access_token",
            "api_key",
            "password",
        }
        priority = [
            "display_name",
            "name",
            "employee_id",
            "user_id",
            "department_id",
            "state",
            "date",
            "request_date",
            "date_from",
            "date_to",
            "amount",
            "total_amount",
            "description",
            "reason",
            "create_date",
        ]
        fields_to_read = []
        for field_name in priority:
            if self._is_context_field_safe(Model, field_name, safe_types, skipped_names):
                fields_to_read.append(field_name)
        for field_name in Model._fields:
            if len(fields_to_read) >= self.DETAIL_CONTEXT_FIELD_LIMIT:
                break
            if field_name in fields_to_read:
                continue
            if self._is_context_field_safe(Model, field_name, safe_types, skipped_names):
                fields_to_read.append(field_name)
        return fields_to_read

    def _is_context_field_safe(self, Model, field_name, safe_types, skipped_names):
        if field_name not in Model._fields or field_name in skipped_names:
            return False
        lowered = field_name.lower()
        if any(secret in lowered for secret in ("password", "passwd", "token", "api_key", "secret", "private_key")):
            return False
        field = Model._fields[field_name]
        if field.type not in safe_types:
            return False
        if field.type == "text" and field_name in ("comment", "note") and "hr" not in Model._name and "radwan" not in Model._name:
            return False
        return True

    def _format_generic_record_context(self, model_name, row):
        Model = self.env[model_name]
        lines = ["- Record ID: %s" % row.get("id")]
        for field_name, value in row.items():
            if field_name == "id" or value in (False, None, "", []):
                continue
            field = Model._fields.get(field_name)
            label = field.string if field else field_name
            lines.append("  - %s: %s" % (label, self._context_value_to_text(value)))
        return lines

    def _context_value_to_text(self, value):
        if isinstance(value, (list, tuple)):
            if len(value) == 2 and isinstance(value[0], int):
                return value[1]
            values = []
            for item in value[:8]:
                values.append(self._context_value_to_text(item))
            suffix = "..." if len(value) > 8 else ""
            return ", ".join(values) + suffix
        text = str(value)
        text = self._plain_chat_body(text)
        if len(text) > 500:
            return text[:497] + "..."
        return text

    def _scope_text(self, scope):
        allowed_lines = []
        seen_models = set()
        for source in scope["allowed_sources"]:
            model_name = source.get("model") or ""
            if model_name in seen_models:
                continue
            seen_models.add(model_name)
            label = source.get("label") or model_name
            rule = source.get("access_rule")
            description = source.get("description")
            parts = [label]
            if model_name:
                parts.append("(%s)" % model_name)
            if rule:
                parts.append("- Rule: %s" % rule)
            if description:
                parts.append("- %s" % description)
            allowed_lines.append("- %s" % " ".join(parts))
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
        text = value or ""
        for _index in range(4):
            unescaped = html.unescape(text)
            if unescaped == text:
                break
            text = unescaped
        text = re.sub(
            r'(?is)<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>.*?</a>',
            r"\1",
            text,
        )
        text = text.replace("\\n", "\n")
        text = re.sub(r"(?i)(?:&amp;lt;|&lt;|<)\s*br\s*/?\s*(?:&amp;gt;|&gt;|>)", "\n", text)
        text = re.sub(r"(?i)</\s*p\s*>", "\n", text)
        text = re.sub(r"(?i)<\s*p[^>]*>", "", text)
        text = re.sub(r"(?i)<\s*/?\s*br\s*/?\s*>", "\n", text)
        text = re.sub(r"(?i)&lt;\s*/?\s*br\s*/?\s*&gt;", "\n", text)
        text = re.sub(r"(?i)</?\s*(div|span|strong|b|em|i|ul|ol|li|table|thead|tbody|tr|td|th)[^>]*>", "", text)
        text = re.sub(r"(?i)<[^>]+>", "", text)
        text = re.sub(r"(?i)&lt;[^&]+&gt;", "", text)
        text = re.sub(r"(?m)^\s*[-•]\s*", "- ", text)
        text = re.sub(r"\s*(?:<br\s*/?>|&lt;br\s*/?&gt;)\s*", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        text = re.sub(r"(?m)^\s*\|?[-:\s|]{3,}\|?\s*$", "", text)
        text = re.sub(r"\s*\|\s*", " | ", text)
        text = re.sub(r"(?m)^\s*\*\s+", "- ", text)
        text = re.sub(r"(?m)^(\s*\d+)\.\s*", r"\1. ", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        text = re.sub(r"\s+\n", "\n", text)
        text = re.sub(r"\n\s+", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _chat_body_html(self, value):
        lines = []
        for line in self._plain_chat_body(value).splitlines():
            report_match = re.match(
                r"^\s*(Open printable report|Download PDF)\s*:\s*(/report/(?:html|pdf)/[A-Za-z0-9_.]+/\d+)\s*$",
                line,
                flags=re.IGNORECASE,
            )
            if report_match:
                label = report_match.group(1)
                url = report_match.group(2)
                lines.append(
                    '<a href="%s" target="_blank" '
                    'style="display:inline-block;margin:4px 0;padding:8px 12px;'
                    'border-radius:10px;background:#e8f3fb;color:#0b5e93;'
                    'font-weight:700;text-decoration:none;">%s</a>'
                    % (escape(url), escape(label))
                )
                continue
            image_match = re.search(r"(/web/image/[A-Za-z0-9_.]+/\d+/[A-Za-z0-9_]+)", line)
            if image_match:
                image_url = image_match.group(1)
                label = line[: image_match.start()].strip(" :-") or _("Employee Image")
                lines.append(
                    '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
                    '<img src="%s" alt="%s" '
                    'style="width:96px;height:96px;border-radius:50%%;object-fit:cover;'
                    'border:3px solid #e8f3fb;background:#f8fafc;"/>'
                    '<a href="%s" target="_blank" '
                    'style="display:inline-block;padding:8px 12px;border-radius:10px;'
                    'background:#e8f3fb;color:#0b5e93;font-weight:700;text-decoration:none;">%s</a>'
                    "</div>"
                    % (escape(image_url), escape(label), escape(image_url), escape(label))
                )
                continue
            lines.append(str(escape(line)))
        return "<br/>".join(lines)

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
            lines.append("  - Employee Image: /web/image/hr.employee/%s/image_1920" % employee["id"])
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
