# -*- coding: utf-8 -*-

from odoo import api, models


class RadwanHrAiSecurity(models.AbstractModel):
    _name = "radwan.hr.ai.security"
    _description = "Radwan HR AI Security Gateway"

    HR_MODEL_LABELS = {
        "hr.employee": "Employees",
        "hr.attendance": "Attendance",
        "hr.leave": "Leaves",
        "hr.payslip": "Payroll",
        "hr.employee.loan": "Loans",
        "hr.expense": "Expenses",
        "approval.request": "Approvals",
        "survey.user_input": "Surveys",
        "project.task": "Tasks",
        "helpdesk.ticket": "Tickets",
        "ir.attachment": "Documents",
    }

    def _model_available(self, model_name):
        return model_name in self.env

    def _can_read_model(self, model_name):
        if not self._model_available(model_name):
            return False
        return self.env[model_name].check_access_rights("read", raise_exception=False)

    def _is_hr_power_user(self):
        return (
            self.env.user.has_group("hr.group_hr_manager")
            or self.env.user.has_group("hr.group_hr_user")
            or self.env.user.has_group("base.group_system")
        )

    def _current_employee(self):
        Employee = self.env["hr.employee"]
        return Employee.search([("user_id", "=", self.env.uid)], limit=1)

    def _visible_employee_domain(self):
        if self._is_hr_power_user():
            return []
        employee = self._current_employee()
        if not employee:
            return [("id", "=", 0)]
        return ["|", ("id", "=", employee.id), ("parent_id.user_id", "=", self.env.uid)]

    def _visible_employee_ids(self):
        if not self._can_read_model("hr.employee"):
            return []
        return self.env["hr.employee"].search(self._visible_employee_domain()).ids

    def _employee_related_domain(self, employee_field="employee_id"):
        employee_ids = self._visible_employee_ids()
        return [(employee_field, "in", employee_ids or [0])]

    def _safe_search_read(self, model_name, domain=None, fields=None, limit=20, order=None):
        if not self._can_read_model(model_name):
            return []
        domain = domain or []
        try:
            return self.env[model_name].search_read(
                domain,
                fields=fields or [],
                limit=limit,
                order=order,
            )
        except Exception:
            return []

    def _safe_count(self, model_name, domain=None):
        if not self._can_read_model(model_name):
            return 0
        try:
            return self.env[model_name].search_count(domain or [])
        except Exception:
            return 0

    def _allowed_sources(self):
        sources = []
        for model_name, label in self.HR_MODEL_LABELS.items():
            if self._can_read_model(model_name):
                sources.append({"model": model_name, "label": label})
        return sources

    def _safe_metric_count(self, model_name, employee_field="employee_id", extra_domain=None):
        domain = self._employee_related_domain(employee_field)
        if extra_domain:
            domain += extra_domain
        return self._safe_count(model_name, domain)

    @api.model
    def build_user_scope(self):
        employee = self._current_employee()
        return {
            "user_id": self.env.uid,
            "user_name": self.env.user.name,
            "employee_id": employee.id if employee else False,
            "employee_name": employee.name if employee else "",
            "is_hr_power_user": self._is_hr_power_user(),
            "visible_employee_ids": self._visible_employee_ids(),
            "allowed_sources": self._allowed_sources(),
        }
