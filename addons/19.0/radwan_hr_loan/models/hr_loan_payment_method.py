from odoo import api, fields, models


class HrLoanPaymentMethod(models.Model):
    _name = 'hr.loan.payment.method'
    _description = 'Loan Payment Method'
    _order = 'company_id, name'
    _check_company_auto = True

    name = fields.Char(string='Payment Name', required=True, translate=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company,
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        domain="[('company_id', '=', company_id)]",
        check_company=True,
    )
    loan_account_id = fields.Many2one(
        'account.account',
        string='Loan Account',
        domain="[('company_ids', 'in', company_id)]",
        check_company=True,
        help='Receivable account used to track employee loan balances.',
    )
    disbursement_account_id = fields.Many2one(
        'account.account',
        string='Disbursement Account',
        domain="[('company_ids', 'in', company_id)]",
        check_company=True,
        help='Cash, bank, or clearing account used when paying the loan.',
    )
    payroll_debit_account_id = fields.Many2one(
        'account.account',
        string='Payroll Debit Account',
        domain="[('company_ids', 'in', company_id)]",
        check_company=True,
        help='Optional account to use on the payroll loan deduction rule.',
    )
    payroll_credit_account_id = fields.Many2one(
        'account.account',
        string='Payroll Credit Account',
        domain="[('company_ids', 'in', company_id)]",
        check_company=True,
        help='Optional account to use on the payroll loan deduction rule.',
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        domain="[('company_id', 'in', [False, company_id])]",
    )
    note = fields.Text()

    _name_company_unique = models.Constraint(
        'unique(name, company_id)',
        'The loan payment method must be unique per company.',
    )

    @api.model
    def _get_default_method(self, company):
        return self.search(
            [('company_id', '=', company.id), ('active', '=', True)],
            limit=1,
        )
