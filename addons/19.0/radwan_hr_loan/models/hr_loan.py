from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero, float_round


class HrEmployeeLoan(models.Model):
    _name = 'hr.employee.loan'
    _description = 'Employee Loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'loan_date desc, id desc'
    _check_company_auto = True

    name = fields.Char(
        default='New',
        readonly=True,
        copy=False,
        tracking=True,
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    currency_id = fields.Many2one(
        related='company_id.currency_id',
        store=True,
        readonly=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        required=True,
        tracking=True,
        check_company=True,
    )
    department_id = fields.Many2one(
        related='employee_id.department_id',
        store=True,
        readonly=True,
    )
    job_id = fields.Many2one(
        related='employee_id.job_id',
        store=True,
        readonly=True,
    )
    version_id = fields.Many2one(
        'hr.version',
        string='Contract',
        compute='_compute_version_id',
        store=True,
        readonly=False,
        tracking=True,
    )
    loan_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    start_date = fields.Date(required=True, tracking=True)
    end_date = fields.Date(compute='_compute_end_date', store=True)
    loan_amount = fields.Monetary(required=True, tracking=True)
    installment_count = fields.Integer(
        string='Number of Months',
        default=1,
        tracking=True,
    )
    installment_amount = fields.Monetary(
        compute='_compute_installment_amount',
        store=True,
    )
    paid_amount = fields.Monetary(
        compute='_compute_amounts',
        store=True,
    )
    balance_amount = fields.Monetary(
        string='Loan Balance',
        compute='_compute_amounts',
        store=True,
    )
    payment_method_id = fields.Many2one(
        'hr.loan.payment.method',
        string='Payment Method',
        check_company=True,
        tracking=True,
    )
    loan_account_id = fields.Many2one(
        related='payment_method_id.loan_account_id',
        readonly=False,
    )
    journal_id = fields.Many2one(
        related='payment_method_id.journal_id',
        readonly=False,
    )
    reason = fields.Text(string='Loan Reason')
    note = fields.Html()
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
        default='draft',
        required=True,
        tracking=True,
    )
    first_approved_by = fields.Many2one(
        'res.users',
        readonly=True,
        copy=False,
    )
    first_approved_date = fields.Datetime(readonly=True, copy=False)
    second_approved_by = fields.Many2one(
        'res.users',
        readonly=True,
        copy=False,
    )
    second_approved_date = fields.Datetime(readonly=True, copy=False)
    disbursed_date = fields.Date(readonly=True, copy=False)
    installment_ids = fields.One2many(
        'hr.loan.installment',
        'loan_id',
        string='Payments Loan',
        copy=True,
    )
    installment_line_count = fields.Integer(
        compute='_compute_smart_counts',
    )
    payslip_count = fields.Integer(compute='_compute_smart_counts')
    move_id = fields.Many2one(
        'account.move',
        string='Loan Journal Entry',
        readonly=True,
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'hr.employee.loan'
                ) or 'New'
            if not vals.get('payment_method_id') and vals.get('company_id'):
                company = self.env['res.company'].browse(vals['company_id'])
                method = self.env['hr.loan.payment.method']._get_default_method(company)
                if method:
                    vals['payment_method_id'] = method.id
        return super().create(vals_list)

    @api.depends('employee_id', 'loan_date', 'start_date')
    def _compute_version_id(self):
        Version = self.env['hr.version']
        for loan in self:
            if not loan.employee_id:
                loan.version_id = False
                continue
            target_date = loan.start_date or loan.loan_date or fields.Date.today()
            domain = [
                ('employee_id', '=', loan.employee_id.id),
                '|',
                ('date_start', '=', False),
                ('date_start', '<=', target_date),
                '|',
                ('date_end', '=', False),
                ('date_end', '>=', target_date),
            ]
            loan.version_id = Version.search(
                domain,
                order='date_version desc, id desc',
                limit=1,
            )

    @api.depends('installment_ids.date', 'installment_count', 'start_date')
    def _compute_end_date(self):
        for loan in self:
            dates = loan.installment_ids.mapped('date')
            if dates:
                loan.end_date = max(dates)
            elif loan.start_date and loan.installment_count:
                loan.end_date = loan.start_date + relativedelta(
                    months=loan.installment_count - 1
                )
            else:
                loan.end_date = False

    @api.depends('loan_amount', 'installment_count')
    def _compute_installment_amount(self):
        for loan in self:
            loan.installment_amount = (
                loan.loan_amount / loan.installment_count
                if loan.installment_count else 0.0
            )

    @api.depends('loan_amount', 'installment_ids.paid_amount', 'installment_ids.amount')
    def _compute_amounts(self):
        for loan in self:
            loan.paid_amount = sum(loan.installment_ids.mapped('paid_amount'))
            loan.balance_amount = max(loan.loan_amount - loan.paid_amount, 0.0)

    def _compute_smart_counts(self):
        Payslip = self.env['hr.payslip']
        for loan in self:
            loan.installment_line_count = len(loan.installment_ids)
            loan.payslip_count = Payslip.search_count([
                ('input_line_ids.loan_installment_ids.loan_id', '=', loan.id),
            ])

    @api.constrains('loan_amount', 'installment_count')
    def _check_positive_amounts(self):
        for loan in self:
            if loan.loan_amount <= 0:
                raise ValidationError(_('Loan amount must be greater than zero.'))
            if loan.installment_count <= 0:
                raise ValidationError(_('Number of months must be greater than zero.'))

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.company_id = self.employee_id.company_id or self.env.company
            self.payment_method_id = self.env['hr.loan.payment.method']._get_default_method(
                self.company_id
            )

    def _ensure_editable_schedule(self):
        blocked = self.installment_ids.filtered(
            lambda line: line.state in ('in_payslip', 'paid')
        )
        if blocked:
            raise UserError(
                _('You cannot regenerate installments after they are linked to payroll.')
            )

    def action_generate_installments(self):
        for loan in self:
            if not loan.start_date:
                raise UserError(_('Please set the start date first.'))
            loan._ensure_editable_schedule()
            loan.installment_ids.unlink()
            currency = loan.currency_id
            amount = float_round(
                loan.loan_amount / loan.installment_count,
                precision_rounding=currency.rounding,
            )
            lines = []
            total = 0.0
            for index in range(loan.installment_count):
                line_amount = amount
                if index == loan.installment_count - 1:
                    line_amount = loan.loan_amount - total
                total += line_amount
                lines.append((0, 0, {
                    'sequence': index + 1,
                    'date': loan.start_date + relativedelta(months=index),
                    'amount': line_amount,
                }))
            loan.installment_ids = lines
        return True

    def action_submit(self):
        for loan in self:
            if not loan.installment_ids:
                loan.action_generate_installments()
            if float_compare(
                sum(loan.installment_ids.mapped('amount')),
                loan.loan_amount,
                precision_rounding=loan.currency_id.rounding,
            ):
                raise UserError(_('Installment total must equal the loan amount.'))
        self.write({'state': 'submit'})

    def action_first_approve(self):
        self.write({
            'state': 'first_approved',
            'first_approved_by': self.env.user.id,
            'first_approved_date': fields.Datetime.now(),
        })

    def action_second_approve(self):
        self.write({
            'state': 'second_approved',
            'second_approved_by': self.env.user.id,
            'second_approved_date': fields.Datetime.now(),
        })

    def _get_employee_partner(self):
        self.ensure_one()
        employee = self.employee_id
        for field_name in ('address_home_id', 'work_contact_id', 'user_partner_id'):
            if field_name in employee._fields and employee[field_name]:
                return employee[field_name]
        if employee.user_id:
            return employee.user_id.partner_id
        return self.env['res.partner']

    def _prepare_disbursement_move_vals(self):
        self.ensure_one()
        method = self.payment_method_id
        if not method:
            raise UserError(_('Please select a loan payment method.'))
        if not method.journal_id or not method.loan_account_id or not method.disbursement_account_id:
            raise UserError(
                _('Configure journal, loan account, and disbursement account on the payment method.')
            )
        partner = self._get_employee_partner()
        return {
            'ref': self.name,
            'journal_id': method.journal_id.id,
            'date': fields.Date.context_today(self),
            'line_ids': [
                (0, 0, {
                    'name': self.name,
                    'partner_id': partner.id or False,
                    'account_id': method.loan_account_id.id,
                    'debit': self.loan_amount,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': self.name,
                    'partner_id': partner.id or False,
                    'account_id': method.disbursement_account_id.id,
                    'debit': 0.0,
                    'credit': self.loan_amount,
                }),
            ],
        }

    def action_disburse(self):
        for loan in self:
            if loan.state not in ('second_approved', 'running'):
                raise UserError(_('Only second approved loans can be disbursed.'))
            if not loan.installment_ids:
                loan.action_generate_installments()
            if not loan.move_id:
                move = self.env['account.move'].create(
                    loan._prepare_disbursement_move_vals()
                )
                move.action_post()
                loan.move_id = move
            loan.write({
                'state': 'running',
                'disbursed_date': fields.Date.context_today(loan),
            })

    def action_cancel(self):
        paid = self.installment_ids.filtered(lambda line: line.state == 'paid')
        if paid:
            raise UserError(_('You cannot cancel a loan that has paid installments.'))
        self.write({'state': 'cancel'})

    def action_reset_to_draft(self):
        for loan in self:
            if loan.move_id and loan.move_id.state == 'posted':
                raise UserError(_('Reverse the journal entry before resetting to draft.'))
        self.write({'state': 'draft'})

    def action_register_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Register Loan Payment'),
            'res_model': 'hr.loan.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_loan_id': self.id},
        }

    def action_view_account_move(self):
        self.ensure_one()
        if not self.move_id:
            return {'type': 'ir.actions.act_window_close'}
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'view_mode': 'form',
        }

    def action_view_payslips(self):
        self.ensure_one()
        payslips = self.env['hr.payslip'].search([
            ('input_line_ids.loan_installment_ids.loan_id', '=', self.id),
        ])
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payslips'),
            'res_model': 'hr.payslip',
            'view_mode': 'list,form',
            'domain': [('id', 'in', payslips.ids)],
        }

    def _refresh_paid_state(self):
        for loan in self:
            if loan.installment_ids and all(
                line.state == 'paid' for line in loan.installment_ids
            ):
                loan.state = 'done'
            elif loan.state == 'done':
                loan.state = 'running'

    def unlink(self):
        if any(loan.state not in ('draft', 'cancel') for loan in self):
            raise UserError(_('Only draft or cancelled loans can be deleted.'))
        return super().unlink()


class HrLoanInstallment(models.Model):
    _name = 'hr.loan.installment'
    _description = 'Loan Installment'
    _order = 'date, sequence, id'
    _check_company_auto = True

    sequence = fields.Integer(default=10)
    loan_id = fields.Many2one(
        'hr.employee.loan',
        required=True,
        ondelete='cascade',
        index=True,
    )
    employee_id = fields.Many2one(
        related='loan_id.employee_id',
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        related='loan_id.company_id',
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        related='loan_id.currency_id',
        store=True,
        readonly=True,
    )
    date = fields.Date(required=True)
    amount = fields.Monetary(required=True)
    paid_amount = fields.Monetary(default=0.0, copy=False)
    balance_amount = fields.Monetary(
        compute='_compute_balance_amount',
        store=True,
    )
    state = fields.Selection(
        [
            ('pending', 'Pending'),
            ('partial', 'Partially Paid'),
            ('in_payslip', 'In Payslip'),
            ('paid', 'Paid'),
            ('cancel', 'Cancelled'),
        ],
        default='pending',
        required=True,
        copy=False,
    )
    payslip_id = fields.Many2one('hr.payslip', readonly=True, copy=False)
    note = fields.Char()

    @api.depends('amount', 'paid_amount')
    def _compute_balance_amount(self):
        for line in self:
            line.balance_amount = max(line.amount - line.paid_amount, 0.0)

    @api.constrains('amount', 'paid_amount')
    def _check_amounts(self):
        for line in self:
            if line.amount <= 0:
                raise ValidationError(_('Installment amount must be greater than zero.'))
            if line.paid_amount < 0:
                raise ValidationError(_('Paid amount cannot be negative.'))
            if float_compare(
                line.paid_amount,
                line.amount,
                precision_rounding=line.currency_id.rounding,
            ) > 0:
                raise ValidationError(_('Paid amount cannot exceed installment amount.'))

    @api.model
    def _get_payroll_installments(self, employee, date_from, date_to):
        return self.search([
            ('employee_id', '=', employee.id),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('state', 'in', ('pending', 'partial', 'in_payslip')),
            ('loan_id.state', '=', 'running'),
            ('company_id', 'in', self.env.companies.ids),
        ])

    def _mark_paid_from_payslip(self, payslip):
        lines = self.filtered(
            lambda line: line.payslip_id == payslip
            and line.date >= payslip.date_from
            and line.date <= payslip.date_to
        )
        for line in lines:
            line.write({
                'paid_amount': line.amount,
                'state': 'paid',
                'payslip_id': payslip.id,
            })
        lines.mapped('loan_id')._refresh_paid_state()

    def _release_from_payslip(self, payslip):
        for line in self.filtered(lambda item: item.payslip_id == payslip):
            line.write({
                'paid_amount': 0.0,
                'state': 'pending',
                'payslip_id': False,
            })
