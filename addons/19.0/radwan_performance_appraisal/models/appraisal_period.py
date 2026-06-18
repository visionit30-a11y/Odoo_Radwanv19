# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class RadwanAppraisalPeriod(models.Model):
    _name = 'radwan.appraisal.period'
    _description = 'فترة التقييم'
    _inherit = ['mail.thread']
    _order = 'date_start desc'

    name = fields.Char('اسم الفترة', required=True)
    type_id = fields.Many2one(
        'radwan.appraisal.type',
        string='نوع التقييم',
        required=True,
        ondelete='restrict',
    )
    date_start = fields.Date('تاريخ البدء', required=True)
    date_end = fields.Date('تاريخ الانتهاء', required=True)
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('open', 'مفتوحة'),
        ('closed', 'مغلقة'),
    ], default='draft', string='الحالة', tracking=True)
    company_id = fields.Many2one(
        'res.company',
        string='الشركة',
        default=lambda s: s.env.company,
    )
    notes = fields.Text('ملاحظات')
    appraisal_count = fields.Integer(
        compute='_compute_appraisal_count',
        string='التقييمات',
    )

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_start > rec.date_end:
                raise ValidationError('تاريخ البدء يجب أن يكون قبل تاريخ الانتهاء!')

    def _compute_appraisal_count(self):
        data = self.env['radwan.appraisal'].read_group(
            [('period_id', 'in', self.ids)],
            ['period_id'],
            ['period_id'],
        )
        count_map = {d['period_id'][0]: d['period_id_count'] for d in data}
        for rec in self:
            rec.appraisal_count = count_map.get(rec.id, 0)

    def action_open(self):
        for rec in self:
            rec.write({'state': 'open'})

    def action_close(self):
        for rec in self:
            rec.write({'state': 'closed'})

    def action_reset_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    def action_view_appraisals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'تقييمات {self.name}',
            'res_model': 'radwan.appraisal',
            'view_mode': 'list,kanban,form',
            'domain': [('period_id', '=', self.id)],
            'context': {'default_period_id': self.id},
        }
