from odoo import api, models


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    @api.model
    def _radwan_sync_loan_salary_rules(self):
        """Keep existing loan deduction rules connected to loan installments."""
        loan_rule = self.env.ref(
            'radwan_hr_loan.hr_salary_rule_employee_loan',
            raise_if_not_found=False,
        )
        loan_rules = self.search([
            '|',
            '|',
            ('code', 'in', ['loan_d', 'LOAN']),
            ('name', 'in', ['Loan_Deduction', 'Employee Loan Deduction']),
            ('id', '=', loan_rule.id if loan_rule else 0),
        ])
        if not loan_rules:
            return

        deduction_category = self.env.ref(
            'om_hr_payroll.DED',
            raise_if_not_found=False,
        )
        vals = {
            'name': 'Loan_Deduction',
            'code': 'loan_d',
            'sequence': 5,
            'condition_select': 'python',
            'condition_python': (
                "loan_input = inputs.dict.get('LOAN')\n"
                "result = bool(loan_input and loan_input.amount)"
            ),
            'amount_select': 'code',
            'amount_python_compute': (
                "loan_input = inputs.dict.get('LOAN')\n"
                "result = -(loan_input.amount if loan_input else 0.0)"
            ),
            'appears_on_payslip': True,
        }
        if deduction_category:
            vals['category_id'] = deduction_category.id

        loan_rules.write(vals)

        loan_input = self.env.ref(
            'radwan_hr_loan.hr_rule_input_employee_loan',
            raise_if_not_found=False,
        )
        target_rule = loan_rule or loan_rules[:1]
        if loan_input and target_rule:
            loan_input.write({
                'name': 'Employee Loan Installment',
                'code': 'LOAN',
                'input_id': target_rule.id,
            })

        self.env['hr.payroll.structure'].search([])._ensure_loan_salary_rule()
