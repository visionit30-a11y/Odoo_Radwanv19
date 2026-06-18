# -*- coding: utf-8 -*-
from odoo import models, fields, api


class RadwanAppraisalType(models.Model):
    _name = 'radwan.appraisal.type'
    _description = 'نوع التقييم'
    _order = 'sequence, name'

    name = fields.Char('الاسم', required=True, translate=True)
    code = fields.Char('الرمز')
    sequence = fields.Integer('الترتيب', default=10)
    frequency = fields.Selection([
        ('monthly', 'شهري'),
        ('quarterly', 'ربع سنوي'),
        ('semi_annual', 'نصف سنوي'),
        ('annual', 'سنوي'),
        ('probation', 'فترة اختبار'),
        ('special', 'خاص / طارئ'),
    ], string='الدورية', required=True, default='annual')
    description = fields.Text('الوصف', translate=True)
    active = fields.Boolean(default=True)
    color = fields.Integer('اللون', default=0)
    appraisal_count = fields.Integer(
        compute='_compute_appraisal_count',
        string='عدد التقييمات',
    )

    def _compute_appraisal_count(self):
        data = self.env['radwan.appraisal'].read_group(
            [('type_id', 'in', self.ids)],
            ['type_id'],
            ['type_id'],
        )
        count_map = {d['type_id'][0]: d['type_id_count'] for d in data}
        for rec in self:
            rec.appraisal_count = count_map.get(rec.id, 0)

    def action_view_appraisals(self):
        return {
            'type': 'ir.actions.act_window',
            'name': f'تقييمات {self.name}',
            'res_model': 'radwan.appraisal',
            'view_mode': 'list,kanban,form',
            'domain': [('type_id', '=', self.id)],
        }
