# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class RadwanHrAiEmployeeAssistant(models.Model):
    _name = "radwan.hr.ai.employee.assistant"
    _description = "Employee HR AI Assistant"
    _order = "create_date desc, id desc"

    name = fields.Char(default="Employee HR Assistant", readonly=True)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user, readonly=True)
    employee_id = fields.Many2one("hr.employee", compute="_compute_employee_id", store=False)
    question = fields.Text(required=True)
    answer = fields.Text(readonly=True)
    scope_summary = fields.Text(readonly=True)
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

    def action_generate_answer(self):
        for record in self:
            scope = self.env["radwan.hr.ai.security"].build_user_scope()
            if not scope["employee_id"] and not scope["is_hr_power_user"]:
                record._write_blocked(_("No employee profile is linked to your user."))
                continue
            answer = record._compose_answer(scope)
            model_names = ", ".join(source["model"] for source in scope["allowed_sources"])
            record.write(
                {
                    "answer": answer,
                    "scope_summary": record._scope_text(scope),
                    "state": "answered",
                }
            )
            self.env["radwan.hr.ai.query.log"].create(
                {
                    "user_id": self.env.uid,
                    "employee_id": scope["employee_id"] or False,
                    "audience": "employee",
                    "question": record.question,
                    "answer": answer,
                    "allowed_model_names": model_names,
                    "visible_employee_count": len(scope["visible_employee_ids"]),
                }
            )
        return True

    def _write_blocked(self, reason):
        self.write({"answer": reason, "scope_summary": reason, "state": "blocked"})
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
