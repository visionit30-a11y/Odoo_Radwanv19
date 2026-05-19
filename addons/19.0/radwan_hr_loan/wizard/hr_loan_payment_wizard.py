from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class HrLoanPaymentWizard(models.TransientModel):
    _name = 'hr.loan.payment.wizard'
    _description = 'Register Loan Payment'

    loan_id = fields.Many2one('hr.employee.loan', required=True)
    company_id = fields.Many2one(related='loan_id.company_id', readonly=True)
    currency_id = fields.Many2one(related='loan_id.currency_id', readonly=True)
    payment_method_id = fields.Many2one(
        related='loan_id.payment_method_id',
        readonly=False,
    )
    payment_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
    )
    amount = fields.Monetary(required=True)
    apply_future_installments = fields.Boolean(
        string='Settle Future Installments',
        help='Allow this payment to settle installments after the payment date.',
    )
    journal_id = fields.Many2one(
        'account.journal',
        related='payment_method_id.journal_id',
        readonly=False,
    )
    note = fields.Char()

    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        loan = self.env['hr.employee.loan'].browse(
            self.env.context.get('default_loan_id')
        )
        if loan:
            payment_date = vals.get('payment_date') or fields.Date.context_today(self)
            vals.setdefault(
                'amount',
                self._get_default_payment_amount(loan, payment_date),
            )
        return vals

    @api.model
    def _get_default_payment_amount(self, loan, payment_date):
        installments = loan.installment_ids.filtered(
            lambda line: line.state in ('pending', 'partial')
            and line.balance_amount
        ).sorted('date')
        due_installments = installments.filtered(
            lambda line: line.date <= payment_date
        )
        return sum((due_installments or installments[:1]).mapped('balance_amount'))

    def _get_payment_installments(self):
        self.ensure_one()
        payment_date = self.payment_date or fields.Date.context_today(self)
        installments = self.loan_id.installment_ids.filtered(
            lambda line: line.state in ('pending', 'partial')
            and line.balance_amount
        ).sorted('date')
        if self.apply_future_installments:
            return installments
        due_installments = installments.filtered(
            lambda line: line.date <= payment_date
        )
        return due_installments or installments[:1]

    @api.onchange('loan_id', 'payment_date', 'apply_future_installments')
    def _onchange_payment_scope(self):
        if not self.loan_id:
            return
        self.amount = sum(self._get_payment_installments().mapped('balance_amount'))

    def _prepare_payment_move_vals(self):
        self.ensure_one()
        method = self.payment_method_id
        if not method or not method.journal_id:
            raise UserError(_('Please configure a journal on the loan payment method.'))
        if not method.loan_account_id or not method.disbursement_account_id:
            raise UserError(
                _('Configure loan account and disbursement account on the payment method.')
            )
        partner = self.loan_id._get_employee_partner()
        return {
            'ref': _('Loan repayment: %s') % self.loan_id.name,
            'journal_id': method.journal_id.id,
            'date': self.payment_date,
            'line_ids': [
                (0, 0, {
                    'name': self.loan_id.name,
                    'partner_id': partner.id or False,
                    'account_id': method.disbursement_account_id.id,
                    'debit': self.amount,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': self.loan_id.name,
                    'partner_id': partner.id or False,
                    'account_id': method.loan_account_id.id,
                    'debit': 0.0,
                    'credit': self.amount,
                }),
            ],
        }

    def action_confirm(self):
        self.ensure_one()
        loan = self.loan_id
        if self.amount <= 0:
            raise UserError(_('Payment amount must be greater than zero.'))
        installments = self._get_payment_installments()
        allowed_amount = sum(installments.mapped('balance_amount'))
        if not installments or float_is_zero(
            allowed_amount,
            precision_rounding=loan.currency_id.rounding,
        ):
            raise UserError(_('There are no due loan installments to pay.'))
        if float_compare(
            self.amount,
            allowed_amount,
            precision_rounding=loan.currency_id.rounding,
        ) > 0:
            raise UserError(
                _(
                    'Payment amount cannot exceed due installments. '
                    'Enable "Settle Future Installments" for early settlement.'
                )
            )

        if self.journal_id:
            move = self.env['account.move'].create(self._prepare_payment_move_vals())
            move.action_post()

        remaining = self.amount
        for installment in installments:
            if float_is_zero(
                remaining,
                precision_rounding=loan.currency_id.rounding,
            ):
                break
            pay_amount = min(installment.balance_amount, remaining)
            paid_amount = installment.paid_amount + pay_amount
            state = 'paid'
            if float_compare(
                paid_amount,
                installment.amount,
                precision_rounding=loan.currency_id.rounding,
            ) < 0:
                state = 'partial'
            installment.write({
                'paid_amount': paid_amount,
                'state': state,
                'note': self.note or installment.note,
            })
            remaining -= pay_amount
        loan._refresh_paid_state()
        return {'type': 'ir.actions.act_window_close'}
