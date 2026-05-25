from odoo import Command, api, models


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    @api.model_create_multi
    def create(self, vals_list):
        structures = super().create(vals_list)
        structures._ensure_loan_salary_rule()
        return structures

    def _ensure_loan_salary_rule(self):
        rule = self.env.ref(
            'radwan_hr_loan.hr_salary_rule_employee_loan',
            raise_if_not_found=False,
        )
        if not rule:
            return
        for structure in self:
            existing_loan_rule = structure.rule_ids.filtered(
                lambda item: item.code in ('loan_d', 'LOAN')
                or item.name in ('Loan_Deduction', 'Employee Loan Deduction')
            )
            if not existing_loan_rule and rule not in structure.rule_ids:
                structure.write({'rule_ids': [Command.link(rule.id)]})

