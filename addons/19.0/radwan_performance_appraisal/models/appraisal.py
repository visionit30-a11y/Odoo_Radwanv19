# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RadwanAppraisal(models.Model):
    _name = 'radwan.appraisal'
    _description = 'تقييم الأداء'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_open desc, id desc'

    name = fields.Char(
        'رقم التقييم',
        default='جديد',
        copy=False,
        readonly=True,
        tracking=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='الموظف',
        required=True,
        tracking=True,
        index=True,
    )
    reviewer_id = fields.Many2one(
        'hr.employee',
        string='المقيِّم المباشر',
        tracking=True,
    )
    hr_reviewer_id = fields.Many2one(
        'res.users',
        string='مراجع الموارد البشرية',
    )
    hr_participant_ids = fields.Many2many(
        'res.users',
        'radwan_appraisal_hr_participant_rel',
        'appraisal_id',
        'user_id',
        string='HR Participants',
        help='Human Resources users who can participate in this appraisal review.',
    )
    period_id = fields.Many2one(
        'radwan.appraisal.period',
        string='فترة التقييم',
        required=True,
        tracking=True,
        index=True,
    )
    type_id = fields.Many2one(
        'radwan.appraisal.type',
        related='period_id.type_id',
        store=True,
        string='نوع التقييم',
        index=True,
    )
    template_id = fields.Many2one(
        'radwan.appraisal.template',
        string='قالب التقييم',
    )
    date_open = fields.Date(
        'تاريخ الفتح',
        default=fields.Date.today,
    )
    date_close = fields.Date('تاريخ الإغلاق', readonly=True)
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('confirmed', 'مؤكد'),
        ('self_review', 'تقييم ذاتي'),
        ('manager_review', 'مراجعة المدير'),
        ('hr_review', 'مراجعة الموارد البشرية'),
        ('done', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ], default='draft', tracking=True, string='الحالة', copy=False, index=True)

    priority = fields.Selection([
        ('0', 'عادي'),
        ('1', 'مهم'),
        ('2', 'عاجل'),
    ], default='0', string='الأولوية')

    line_ids = fields.One2many(
        'radwan.appraisal.line',
        'appraisal_id',
        string='بنود التقييم',
    )

    self_score = fields.Float(
        compute='_compute_scores',
        store=True,
        string='الدرجة الذاتية %',
        digits=(5, 1),
    )
    manager_score = fields.Float(
        compute='_compute_scores',
        store=True,
        string='درجة المدير %',
        digits=(5, 1),
    )
    total_score = fields.Float(
        compute='_compute_scores',
        store=True,
        string='الدرجة الإجمالية %',
        digits=(5, 1),
    )
    rating_id = fields.Many2one(
        'radwan.appraisal.rating',
        compute='_compute_rating',
        store=True,
        string='التقدير',
    )

    badge_id = fields.Many2one(
        'gamification.badge',
        string='Completion Badge',
        help='Optional badge to grant to the employee after the appraisal is completed.',
    )
    badge_user_id = fields.Many2one(
        'gamification.badge.user',
        string='Granted Badge',
        readonly=True,
        copy=False,
    )

    department_id = fields.Many2one(
        related='employee_id.department_id',
        store=True,
        string='القسم',
        index=True,
    )
    job_id = fields.Many2one(
        related='employee_id.job_id',
        store=True,
        string='المسمى الوظيفي',
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda s: s.env.company,
        string='الشركة',
    )
    color = fields.Integer(
        compute='_compute_color',
        store=True,
        string='اللون',
    )
    notes = fields.Html('ملاحظات وتوصيات')

    @api.depends('state')
    def _compute_color(self):
        color_map = {
            'draft': 0,
            'confirmed': 1,
            'self_review': 3,
            'manager_review': 2,
            'hr_review': 5,
            'done': 10,
            'cancelled': 9,
        }
        for rec in self:
            rec.color = color_map.get(rec.state, 0)

    @api.depends('line_ids.weighted_self_score', 'line_ids.weighted_manager_score', 'state')
    def _compute_scores(self):
        for rec in self:
            rec.self_score = sum(rec.line_ids.mapped('weighted_self_score'))
            rec.manager_score = sum(rec.line_ids.mapped('weighted_manager_score'))
            if rec.state in ('manager_review', 'hr_review', 'done'):
                rec.total_score = rec.manager_score
            else:
                rec.total_score = rec.self_score

    @api.depends('total_score', 'state')
    def _compute_rating(self):
        for rec in self:
            if rec.total_score > 0 and rec.state in ('hr_review', 'done'):
                rating = self.env['radwan.appraisal.rating'].search([
                    ('score_from', '<=', rec.total_score),
                    ('score_to', '>=', rec.total_score),
                    ('active', '=', True),
                ], limit=1)
                rec.rating_id = rating
            else:
                rec.rating_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'جديد') == 'جديد':
                vals['name'] = self.env['ir.sequence'].next_by_code('radwan.appraisal') or 'جديد'
        records = super().create(vals_list)
        records._subscribe_hr_participants()
        return records

    def write(self, vals):
        result = super().write(vals)
        if {'hr_participant_ids', 'hr_reviewer_id'} & set(vals):
            self._subscribe_hr_participants()
        return result

    def _subscribe_hr_participants(self):
        for rec in self:
            users = rec.hr_participant_ids | rec.hr_reviewer_id
            partners = users.mapped('partner_id')
            if partners:
                rec.message_subscribe(partner_ids=partners.ids)

    def _load_template_lines(self):
        self.ensure_one()
        if not self.template_id:
            return
        self.line_ids.unlink()
        lines = []
        for seq, tl in enumerate(self.template_id.line_ids, start=1):
            lines.append({
                'appraisal_id': self.id,
                'criteria_id': tl.criteria_id.id,
                'weight': tl.weight,
                'sequence': seq * 10,
            })
        if lines:
            self.env['radwan.appraisal.line'].create(lines)

    def action_load_template(self):
        self.ensure_one()
        if not self.template_id:
            raise UserError('يرجى اختيار قالب التقييم أولاً!')
        self._load_template_lines()

    def action_confirm(self):
        for rec in self:
            if rec.template_id and not rec.line_ids:
                rec._load_template_lines()
            rec.write({'state': 'confirmed'})

    def action_self_review(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError('يجب إضافة بنود التقييم أولاً قبل بدء التقييم الذاتي!')
            rec.write({'state': 'self_review'})

    def action_manager_review(self):
        self.write({'state': 'manager_review'})

    def action_hr_review(self):
        self.write({'state': 'hr_review'})

    def action_done(self):
        self.write({
            'state': 'done',
            'date_close': fields.Date.today(),
        })

    def action_grant_appraisal_badge(self):
        for rec in self:
            if rec.state != 'done':
                raise UserError(_('The appraisal must be completed before granting a badge.'))
            if not rec.badge_id:
                raise UserError(_('Please select a completion badge first.'))
            if not rec.employee_id.user_id:
                raise UserError(_('The employee must be linked to an Odoo user before granting a badge.'))
            if rec.badge_user_id:
                raise UserError(_('A badge has already been granted for this appraisal.'))
            badge_user = self.env['gamification.badge.user'].sudo().create({
                'user_id': rec.employee_id.user_id.id,
                'sender_id': self.env.user.id,
                'badge_id': rec.badge_id.id,
                'comment': _('Granted from appraisal %s') % rec.display_name,
            })
            badge_user._send_badge()
            rec.badge_user_id = badge_user.id
            rec.message_post(body=_('Badge granted: %s') % rec.badge_id.display_name)
        return True

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_view_employee_appraisals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'تقييمات {self.employee_id.name}',
            'res_model': 'radwan.appraisal',
            'view_mode': 'list,kanban,form',
            'domain': [('employee_id', '=', self.employee_id.id), ('id', '!=', self.id)],
        }


class RadwanAppraisalLine(models.Model):
    _name = 'radwan.appraisal.line'
    _description = 'بند التقييم'
    _order = 'sequence, id'

    appraisal_id = fields.Many2one(
        'radwan.appraisal',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer('الترتيب', default=10)
    criteria_id = fields.Many2one(
        'radwan.appraisal.criteria',
        string='المعيار',
        required=True,
        ondelete='restrict',
    )
    category = fields.Selection(
        related='criteria_id.category',
        store=True,
        string='الفئة',
    )
    weight = fields.Float('الوزن %', default=20.0, digits=(5, 1))
    self_score = fields.Float('التقييم الذاتي', digits=(5, 1), default=0.0)
    manager_score = fields.Float('تقييم المدير', digits=(5, 1), default=0.0)
    weighted_self_score = fields.Float(
        compute='_compute_weighted_scores',
        store=True,
        string='الذاتي الموزون',
        digits=(5, 2),
    )
    weighted_manager_score = fields.Float(
        compute='_compute_weighted_scores',
        store=True,
        string='المدير الموزون',
        digits=(5, 2),
    )
    comment = fields.Text('التغذية الراجعة')

    @api.depends('self_score', 'manager_score', 'weight')
    def _compute_weighted_scores(self):
        for line in self:
            line.weighted_self_score = (line.self_score * line.weight) / 100.0
            line.weighted_manager_score = (line.manager_score * line.weight) / 100.0
