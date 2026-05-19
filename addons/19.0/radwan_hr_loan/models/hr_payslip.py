from odoo import _, api, fields, models


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    loan_installment_ids = fields.Many2many(
        'hr.loan.installment',
        'hr_payslip_input_loan_installment_rel',
        'input_id',
        'installment_id',
        string='Loan Installments',
        copy=False,
    )


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    loan_installment_count = fields.Integer(
        compute='_compute_loan_installment_count',
    )

    @api.depends('input_line_ids.loan_installment_ids')
    def _compute_loan_installment_count(self):
        for slip in self:
            slip.loan_installment_count = len(
                slip.input_line_ids.mapped('loan_installment_ids')
            )

    @api.model
    def get_inputs(self, versions, date_from, date_to):
        res = super().get_inputs(versions, date_from, date_to)
        Installment = self.env['hr.loan.installment']
        for version in versions:
            employee = version.employee_id
            installments = Installment._get_payroll_installments(
                employee,
                date_from,
                date_to,
            )
            if not installments:
                continue
            amount = sum(installments.mapped('balance_amount'))
            if amount:
                res.append({
                    'name': _('Employee Loan Installments'),
                    'sequence': 999,
                    'code': 'LOAN',
                    'amount': amount,
                    'version_id': version.id,
                    'loan_installment_ids': [(6, 0, installments.ids)],
                })
        return res

    def _sync_loan_inputs(self):
        Installment = self.env['hr.loan.installment']
        for slip in self.filtered(lambda item: item.state == 'draft'):
            if not slip.employee_id or not slip.date_from or not slip.date_to:
                continue
            old_inputs = slip.input_line_ids.filtered(
                lambda line: line.loan_installment_ids
            )
            linked_installments = old_inputs.mapped('loan_installment_ids')
            old_inputs.unlink()
            linked_installments.filtered(
                lambda line: line.state == 'in_payslip'
                and (not line.payslip_id or line.payslip_id == slip)
            ).write({
                'state': 'pending',
                'payslip_id': False,
            })
            installments = Installment._get_payroll_installments(
                slip.employee_id,
                slip.date_from,
                slip.date_to,
            )
            if not installments:
                continue
            amount = sum(installments.mapped('balance_amount'))
            if not amount:
                continue
            version = installments.mapped('loan_id.version_id')[:1] or slip.version_id
            if not version and 'version_id' in slip.employee_id._fields:
                version = slip.employee_id.version_id
            if not version:
                continue
            slip.input_line_ids = [(0, 0, {
                'name': _('Employee Loan Installments'),
                'sequence': 999,
                'code': 'LOAN',
                'amount': amount,
                'version_id': version.id,
                'loan_installment_ids': [(6, 0, installments.ids)],
            })]
            installments.write({
                'state': 'in_payslip',
                'payslip_id': slip.id,
            })

    def compute_sheet(self):
        self._sync_loan_inputs()
        return super().compute_sheet()

    def action_payslip_done(self):
        res = super().action_payslip_done()
        for slip in self:
            installments = slip.input_line_ids.mapped('loan_installment_ids').filtered(
                lambda line: line.payslip_id == slip
                and line.date >= slip.date_from
                and line.date <= slip.date_to
            )
            installments._mark_paid_from_payslip(slip)
        return res

    def action_payslip_cancel(self):
        for slip in self:
            installments = slip.input_line_ids.mapped('loan_installment_ids')
            installments._release_from_payslip(slip)
        return super().action_payslip_cancel()

    def action_view_loan_installments(self):
        self.ensure_one()
        installments = self.input_line_ids.mapped('loan_installment_ids')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Loan Installments'),
            'res_model': 'hr.loan.installment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', installments.ids)],
        }
