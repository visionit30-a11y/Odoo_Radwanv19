from odoo import _, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    loan_ids = fields.One2many('hr.employee.loan', 'employee_id')
    loan_count = fields.Integer(compute='_compute_loan_count')

    def _compute_loan_count(self):
        grouped = self.env['hr.employee.loan']._read_group(
            [('employee_id', 'in', self.ids)],
            ['employee_id'],
            ['__count'],
        )
        counts = {employee.id: count for employee, count in grouped}
        for employee in self:
            employee.loan_count = counts.get(employee.id, 0)

    def action_view_employee_loans(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Employee Loans'),
            'res_model': 'hr.employee.loan',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {
                'default_employee_id': self.id,
                'default_company_id': self.company_id.id,
            },
        }
