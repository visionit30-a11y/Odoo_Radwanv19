# -*- coding: utf-8 -*-
from odoo import models, fields


class RadwanAppraisalCriteria(models.Model):
    _name = 'radwan.appraisal.criteria'
    _description = 'معيار التقييم'
    _order = 'category, sequence, name'

    name = fields.Char('المعيار', required=True, translate=True)
    code = fields.Char('الرمز')
    sequence = fields.Integer('الترتيب', default=10)
    category = fields.Selection([
        ('performance', 'الأداء الوظيفي'),
        ('behavior', 'السلوك والانضباط'),
        ('competency', 'الكفاءات والمهارات'),
        ('goals', 'الأهداف والإنجازات'),
        ('leadership', 'القيادة والإدارة'),
        ('development', 'التطوير والابتكار'),
    ], string='الفئة', required=True, default='performance')
    description = fields.Text('الوصف والتوضيح', translate=True)
    max_score = fields.Float('الدرجة القصوى', default=100.0)
    active = fields.Boolean(default=True)
