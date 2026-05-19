from odoo import fields, models


class HrLoanReportWizard(models.TransientModel):
    _name = 'hr.loan.report.wizard'
    _description = 'Loan Report Wizard'

    report_type = fields.Selection(
        [
            ('loan', 'Loan Analysis Report'),
            ('installment', 'Loan Installment Report'),
        ],
        required=True,
        default='loan',
    )
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company,
    )
    employee_ids = fields.Many2many('hr.employee')
    date_from = fields.Date()
    date_to = fields.Date()
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submit', 'Submitted'),
            ('first_approved', 'First Approved'),
            ('second_approved', 'Second Approved'),
            ('running', 'Running'),
            ('done', 'Paid'),
            ('cancel', 'Cancelled'),
        ],
    )

    def _loan_domain(self):
        domain = [('company_id', '=', self.company_id.id)]
        if self.employee_ids:
            domain.append(('employee_id', 'in', self.employee_ids.ids))
        if self.state:
            domain.append(('state', '=', self.state))
        if self.date_from:
            domain.append(('loan_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('loan_date', '<=', self.date_to))
        return domain

    def action_open_report(self):
        self.ensure_one()
        if self.report_type == 'installment':
            domain = [('loan_id.company_id', '=', self.company_id.id)]
            if self.employee_ids:
                domain.append(('employee_id', 'in', self.employee_ids.ids))
            if self.date_from:
                domain.append(('date', '>=', self.date_from))
            if self.date_to:
                domain.append(('date', '<=', self.date_to))
            return {
                'type': 'ir.actions.act_window',
                'name': 'Loan Installment Report',
                'res_model': 'hr.loan.installment',
                'view_mode': 'list,pivot,graph',
                'domain': domain,
            }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Loan Analysis Report',
            'res_model': 'hr.employee.loan',
            'view_mode': 'list,pivot,graph,form',
            'domain': self._loan_domain(),
        }
