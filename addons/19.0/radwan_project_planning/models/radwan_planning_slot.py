from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round


class RadwanPlanningSlot(models.Model):
    _name = 'radwan.planning.slot'
    _description = 'Planning Shift'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime, employee_id, material_id, id'

    name = fields.Char(
        default=lambda self: self.env._('New'),
        copy=False,
        readonly=True,
        tracking=True,
    )
    description = fields.Char()
    active = fields.Boolean(default=True)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('published', 'Published'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        default='draft',
        required=True,
        tracking=True,
    )
    resource_type = fields.Selection(
        [
            ('employee', 'Employee'),
            ('material', 'Material'),
            ('open', 'Open Shift'),
        ],
        default='employee',
        required=True,
        tracking=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        tracking=True,
        domain="[('company_id', 'in', [company_id, False])]",
    )
    material_id = fields.Many2one(
        'radwan.planning.material',
        tracking=True,
        domain="[('company_id', 'in', [company_id, False])]",
    )
    role_id = fields.Many2one(
        'radwan.planning.role',
        tracking=True,
        domain="[('company_id', 'in', [company_id, False])]",
    )
    project_id = fields.Many2one(
        'project.project',
        tracking=True,
        domain="[('allow_timesheets', '=', True), ('is_template', '=', False)]",
    )
    task_id = fields.Many2one(
        'project.task',
        tracking=True,
        domain="[('project_id', '=', project_id)]",
    )
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company,
    )
    company_currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        readonly=True,
    )
    start_datetime = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    )
    end_datetime = fields.Datetime(
        required=True,
        default=lambda self: fields.Datetime.now() + timedelta(hours=8),
        tracking=True,
    )
    allocated_hours = fields.Float(
        compute='_compute_allocated_hours',
        store=True,
    )
    planned_cost = fields.Monetary(
        compute='_compute_planned_cost',
        store=True,
        currency_field='company_currency_id',
    )
    timesheet_line_ids = fields.One2many(
        'account.analytic.line',
        'radwan_planning_slot_id',
        string='Timesheets',
    )
    timesheet_count = fields.Integer(compute='_compute_timesheet_metrics', store=True)
    actual_hours = fields.Float(compute='_compute_timesheet_metrics', store=True)
    remaining_hours = fields.Float(compute='_compute_timesheet_metrics', store=True)
    progress = fields.Float(compute='_compute_timesheet_metrics', store=True)
    color = fields.Integer(related='role_id.color', readonly=True)
    published_by_id = fields.Many2one('res.users', readonly=True, copy=False)
    published_date = fields.Datetime(readonly=True, copy=False)
    note = fields.Text()

    @api.depends('start_datetime', 'end_datetime')
    def _compute_allocated_hours(self):
        for slot in self:
            if slot.start_datetime and slot.end_datetime:
                delta = slot.end_datetime - slot.start_datetime
                slot.allocated_hours = max(delta.total_seconds() / 3600.0, 0.0)
            else:
                slot.allocated_hours = 0.0

    @api.depends(
        'allocated_hours',
        'employee_id.hourly_cost',
        'material_id.hourly_cost',
        'resource_type',
    )
    def _compute_planned_cost(self):
        for slot in self:
            hourly_cost = 0.0
            if slot.resource_type == 'employee' and slot.employee_id:
                hourly_cost = slot.employee_id.hourly_cost
            elif slot.resource_type == 'material' and slot.material_id:
                hourly_cost = slot.material_id.hourly_cost
            slot.planned_cost = slot.allocated_hours * hourly_cost

    @api.depends('timesheet_line_ids.unit_amount', 'allocated_hours')
    def _compute_timesheet_metrics(self):
        for slot in self:
            actual = sum(slot.timesheet_line_ids.mapped('unit_amount'))
            slot.timesheet_count = len(slot.timesheet_line_ids)
            slot.actual_hours = actual
            slot.remaining_hours = max(slot.allocated_hours - actual, 0.0)
            if slot.allocated_hours:
                slot.progress = float_round(
                    actual / slot.allocated_hours * 100.0,
                    precision_digits=2,
                )
            else:
                slot.progress = 0.0

    @api.constrains('start_datetime', 'end_datetime')
    def _check_dates(self):
        for slot in self:
            if slot.end_datetime <= slot.start_datetime:
                raise ValidationError(
                    self.env._('The end date must be after the start date.')
                )

    @api.constrains(
        'resource_type',
        'employee_id',
        'material_id',
        'start_datetime',
        'end_datetime',
        'state',
    )
    def _check_resource_overlap(self):
        for slot in self:
            if slot.state == 'cancelled':
                continue
            domain = [
                ('id', '!=', slot.id),
                ('state', '!=', 'cancelled'),
                ('start_datetime', '<', slot.end_datetime),
                ('end_datetime', '>', slot.start_datetime),
            ]
            if slot.resource_type == 'employee' and slot.employee_id:
                domain.append(('employee_id', '=', slot.employee_id.id))
            elif slot.resource_type == 'material' and slot.material_id:
                domain.append(('material_id', '=', slot.material_id.id))
            else:
                continue
            if self.search_count(domain):
                raise ValidationError(
                    self.env._('This resource already has a shift in this period.')
                )

    @api.onchange('resource_type')
    def _onchange_resource_type(self):
        for slot in self:
            if slot.resource_type == 'employee':
                slot.material_id = False
            elif slot.resource_type == 'material':
                slot.employee_id = False
            else:
                slot.employee_id = False
                slot.material_id = False

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for slot in self:
            if slot.employee_id:
                slot.resource_type = 'employee'
                if slot.employee_id.company_id:
                    slot.company_id = slot.employee_id.company_id
                if not slot.role_id:
                    slot.role_id = slot.employee_id.radwan_planning_role_ids[:1]

    @api.onchange('material_id')
    def _onchange_material_id(self):
        for slot in self:
            if slot.material_id:
                slot.resource_type = 'material'
                if slot.material_id.company_id:
                    slot.company_id = slot.material_id.company_id
                if not slot.role_id:
                    slot.role_id = slot.material_id.default_role_id

    @api.onchange('project_id')
    def _onchange_project_id(self):
        for slot in self:
            if slot.task_id.project_id != slot.project_id:
                slot.task_id = False
            if slot.project_id.company_id:
                slot.company_id = slot.project_id.company_id

    @api.onchange('task_id')
    def _onchange_task_id(self):
        for slot in self:
            if slot.task_id and slot.task_id.project_id:
                slot.project_id = slot.task_id.project_id

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('name', self.env._('New')) == self.env._('New'):
                vals['name'] = (
                    sequence.next_by_code('radwan.planning.slot')
                    or self.env._('New')
                )
            self._normalize_resource_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._normalize_resource_vals(vals)
        return super().write(vals)

    def _normalize_resource_vals(self, vals):
        resource_type = vals.get('resource_type')
        if resource_type == 'employee':
            vals['material_id'] = False
        elif resource_type == 'material':
            vals['employee_id'] = False
        elif resource_type == 'open':
            vals['employee_id'] = False
            vals['material_id'] = False

    def action_publish(self):
        self.write({
            'state': 'published',
            'published_by_id': self.env.user.id,
            'published_date': fields.Datetime.now(),
        })

    def action_set_draft(self):
        self.write({'state': 'draft'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_unassign(self):
        allow_unassignment = (
            self.env['ir.config_parameter']
            .sudo()
            .get_param('radwan_project_planning.allow_unassignment', 'False')
        ) in ('1', 'True', 'true')
        is_manager = self.env.user.has_group('project.group_project_manager')
        for slot in self:
            if not allow_unassignment:
                raise UserError(self.env._('Unassignment is disabled in settings.'))
            if slot.employee_id.user_id != self.env.user and not is_manager:
                raise UserError(
                    self.env._('You can only unassign your own planning shifts.')
                )
        self.write({'resource_type': 'open', 'employee_id': False})

    def _prepare_timesheet_values(self):
        self.ensure_one()
        if not self.employee_id:
            raise UserError(self.env._('Only employee shifts can create timesheets.'))
        if not self.project_id:
            raise UserError(self.env._('Select a project before creating a timesheet.'))
        if not self.project_id.allow_timesheets:
            raise UserError(
                self.env._('Timesheets must be enabled on the selected project.')
            )
        return {
            'name': self.description or self.name,
            'employee_id': self.employee_id.id,
            'project_id': self.project_id.id,
            'task_id': self.task_id.id,
            'date': fields.Date.to_date(self.start_datetime),
            'unit_amount': self.allocated_hours,
            'company_id': self.company_id.id,
            'radwan_planning_slot_id': self.id,
        }

    def action_create_timesheet(self):
        line_model = self.env['account.analytic.line']
        for slot in self:
            if slot.timesheet_line_ids:
                continue
            line_model.create(slot._prepare_timesheet_values())
        return self.action_view_timesheets()

    def action_match_timesheets(self):
        for slot in self:
            if not slot.employee_id or not slot.project_id:
                continue
            domain = [
                ('radwan_planning_slot_id', '=', False),
                ('employee_id', '=', slot.employee_id.id),
                ('project_id', '=', slot.project_id.id),
                ('date', '=', fields.Date.to_date(slot.start_datetime)),
            ]
            if slot.task_id:
                domain.append(('task_id', '=', slot.task_id.id))
            self.env['account.analytic.line'].search(domain).write({
                'radwan_planning_slot_id': slot.id,
            })

    def action_view_timesheets(self):
        self.ensure_one()
        action = self.env.ref('hr_timesheet.act_hr_timesheet_line').read()[0]
        action['domain'] = [('radwan_planning_slot_id', '=', self.id)]
        action['context'] = {
            'default_radwan_planning_slot_id': self.id,
            'default_employee_id': self.employee_id.id,
            'default_project_id': self.project_id.id,
            'default_task_id': self.task_id.id,
            'default_date': fields.Date.to_date(self.start_datetime),
        }
        return action
