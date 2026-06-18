# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class RadwanAppraisalTemplate(models.Model):
    _name = 'radwan.appraisal.template'
    _description = 'قالب التقييم'
    _order = 'name'

    name = fields.Char('اسم القالب', required=True, translate=True)
    type_id = fields.Many2one(
        'radwan.appraisal.type',
        string='نوع التقييم',
        ondelete='set null',
    )
    line_ids = fields.One2many(
        'radwan.appraisal.template.line',
        'template_id',
        string='المعايير',
    )
    description = fields.Text('الوصف')
    active = fields.Boolean(default=True)
    total_weight = fields.Float(
        compute='_compute_total_weight',
        string='إجمالي الأوزان %',
        digits=(5, 1),
    )
    criteria_count = fields.Integer(
        compute='_compute_criteria_count',
        string='عدد المعايير',
    )

    @api.depends('line_ids.weight')
    def _compute_total_weight(self):
        for rec in self:
            rec.total_weight = sum(rec.line_ids.mapped('weight'))

    @api.depends('line_ids')
    def _compute_criteria_count(self):
        for rec in self:
            rec.criteria_count = len(rec.line_ids)

    @api.constrains('line_ids')
    def _check_total_weight(self):
        for rec in self:
            if rec.line_ids:
                total = sum(rec.line_ids.mapped('weight'))
                if abs(total - 100.0) > 0.1:
                    raise ValidationError(
                        f'إجمالي الأوزان يجب أن يساوي 100%!\n'
                        f'الإجمالي الحالي: {total:.1f}%'
                    )


class RadwanAppraisalTemplateLine(models.Model):
    _name = 'radwan.appraisal.template.line'
    _description = 'سطر قالب التقييم'
    _order = 'sequence, id'

    template_id = fields.Many2one(
        'radwan.appraisal.template',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer('الترتيب', default=10)
    criteria_id = fields.Many2one(
        'radwan.appraisal.criteria',
        string='المعيار',
        required=True,
        ondelete='restrict',
    )
    weight = fields.Float('الوزن %', default=20.0, digits=(5, 1))
    category = fields.Selection(
        related='criteria_id.category',
        store=True,
        string='الفئة',
    )
