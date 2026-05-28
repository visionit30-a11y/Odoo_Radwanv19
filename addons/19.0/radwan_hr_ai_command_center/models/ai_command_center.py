# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import _, fields, models


class RadwanHrAiCommandCenter(models.Model):
    _name = "radwan.hr.ai.command.center"
    _description = "HR AI Command Center"

    name = fields.Char(default="HR AI Command Center", required=True)
    date_from = fields.Date(default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date(default=fields.Date.today)
    employee_count = fields.Integer(readonly=True)
    attendance_count = fields.Integer(readonly=True)
    leave_count = fields.Integer(readonly=True)
    payslip_count = fields.Integer(readonly=True)
    loan_count = fields.Integer(readonly=True)
    ticket_count = fields.Integer(readonly=True)
    insight_ids = fields.Many2many("radwan.hr.ai.insight", string="Generated Insights", readonly=True)

    def action_refresh_insights(self):
        self.ensure_one()
        security = self.env["radwan.hr.ai.security"]
        scope = security.build_user_scope()
        if not scope["is_hr_power_user"] and not self.env.user.has_group("radwan_hr_ai_employee.group_hr_ai_manager"):
            return False

        employee_ids = scope["visible_employee_ids"] or [0]
        date_domain = []
        if self.date_from:
            date_domain.append(("create_date", ">=", fields.Datetime.to_string(self.date_from)))
        if self.date_to:
            date_domain.append(("create_date", "<=", fields.Datetime.to_string(self.date_to + timedelta(days=1))))

        employee_count = security._safe_count("hr.employee", [("id", "in", employee_ids)])
        attendance_count = security._safe_count("hr.attendance", [("employee_id", "in", employee_ids)] + date_domain)
        leave_count = security._safe_count("hr.leave", [("employee_id", "in", employee_ids)] + date_domain)
        payslip_count = security._safe_count("hr.payslip", [("employee_id", "in", employee_ids)] + date_domain)
        loan_count = security._safe_count("hr.employee.loan", [("employee_id", "in", employee_ids)] + date_domain)
        ticket_count = security._safe_count("helpdesk.ticket", date_domain)

        insights = self._generate_insights(
            attendance_count=attendance_count,
            leave_count=leave_count,
            payslip_count=payslip_count,
            loan_count=loan_count,
            ticket_count=ticket_count,
            employee_count=employee_count,
        )
        self.write(
            {
                "employee_count": employee_count,
                "attendance_count": attendance_count,
                "leave_count": leave_count,
                "payslip_count": payslip_count,
                "loan_count": loan_count,
                "ticket_count": ticket_count,
                "insight_ids": [(6, 0, insights.ids)],
            }
        )
        return True

    def _generate_insights(self, **metrics):
        Insight = self.env["radwan.hr.ai.insight"]
        vals_list = []
        if metrics["employee_count"]:
            leave_ratio = metrics["leave_count"] / max(metrics["employee_count"], 1)
            if leave_ratio >= 1:
                vals_list.append(
                    {
                        "name": _("High leave activity"),
                        "insight_type": "leave",
                        "severity": "2",
                        "summary": _("Leave requests are high compared with the visible employee count."),
                        "recommendation": _("Review department coverage and pending leave approvals."),
                        "source_model": "hr.leave",
                        "source_count": metrics["leave_count"],
                    }
                )
        if metrics["loan_count"]:
            vals_list.append(
                {
                    "name": _("Loan activity requires review"),
                    "insight_type": "loan",
                    "severity": "1",
                    "summary": _("There are loan records in the selected period."),
                    "recommendation": _("Review outstanding balances and approval status."),
                    "source_model": "hr.employee.loan",
                    "source_count": metrics["loan_count"],
                }
            )
        if metrics["ticket_count"]:
            vals_list.append(
                {
                    "name": _("Employee service tickets"),
                    "insight_type": "ticket",
                    "severity": "1",
                    "summary": _("There are helpdesk tickets in the selected period."),
                    "recommendation": _("Classify repeated HR issues and prepare policy or self-service improvements."),
                    "source_model": "helpdesk.ticket",
                    "source_count": metrics["ticket_count"],
                }
            )
        if not vals_list:
            vals_list.append(
                {
                    "name": _("No critical HR AI alerts"),
                    "insight_type": "general",
                    "severity": "0",
                    "summary": _("No immediate risk indicators were detected for the selected period."),
                    "recommendation": _("Keep monitoring attendance, leaves, loans, documents, and service tickets."),
                    "source_count": 0,
                }
            )
        return Insight.create(vals_list)
