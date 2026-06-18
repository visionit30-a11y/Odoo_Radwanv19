# -*- coding: utf-8 -*-
from odoo import models, fields


class RadwanAppraisalRating(models.Model):
    _name = 'radwan.appraisal.rating'
    _description = 'مقياس التقييم'
    _order = 'score_from desc'

    name = fields.Char('المستوى', required=True, translate=True)
    code = fields.Char('الرمز', required=True)
    score_from = fields.Float('من %', required=True, digits=(5, 1))
    score_to = fields.Float('إلى %', required=True, digits=(5, 1))
    color = fields.Integer('اللون', default=0)
    description = fields.Text('الوصف', translate=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'رمز المستوى يجب أن يكون فريداً!'),
    ]
