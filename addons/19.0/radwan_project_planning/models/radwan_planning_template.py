from datetime import datetime, time

import pytz

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RadwanPlanningTemplate(models.Model):
    _name = 'radwan.planning.template'
    _description = 'Planning Shift Template'
    _order = 'name'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    start_hour = fields.Float(default=8.0, required=True)
    duration = fields.Float(default=8.0, required=True)
    end_hour = fields.Float(compute='_compute_end_hour')
    role_id = fields.Many2one(
        'radwan.planning.role',
        domain="[('company_id', 'in', [company_id, False])]",
    )
    employee_id = fields.Many2one(
        'hr.employee',
        domain="[('company_id', 'in', [company_id, False])]",
    )
    material_id = fields.Many2one(
        'radwan.planning.material',
        domain="[('company_id', 'in', [company_id, False])]",
    )
    project_id = fields.Many2one(
        'project.project',
        domain="[('allow_timesheets', '=', True), ('is_template', '=', False)]",
    )
    task_id = fields.Many2one(
        'project.task',
        domain="[('project_id', '=', project_id)]",
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    note = fields.Text()

    @api.depends('start_hour', 'duration')
    def _compute_end_hour(self):
        for template in self:
            template.end_hour = template.start_hour + template.duration

    @api.constrains('start_hour', 'duration')
    def _check_hours(self):
        for template in self:
            if template.start_hour < 0 or template.start_hour >= 24:
                raise ValidationError(
                    self.env._('Start hour must be between 0 and 24.')
                )
            if template.duration <= 0:
                raise ValidationError(self.env._('Duration must be positive.'))
            if template.start_hour + template.duration > 24:
                raise ValidationError(
                    self.env._('Templates cannot cross midnight.')
                )

    @api.onchange('project_id')
    def _onchange_project_id(self):
        for template in self:
            if template.task_id.project_id != template.project_id:
                template.task_id = False
            if template.project_id.company_id:
                template.company_id = template.project_id.company_id

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for template in self:
            if template.employee_id.company_id:
                template.company_id = template.employee_id.company_id

    def _local_datetime(self, date, float_hour):
        hours = int(float_hour)
        minutes = int(round((float_hour - hours) * 60))
        if minutes == 60:
            hours += 1
            minutes = 0
        local_tz = pytz.timezone(self.env.user.tz or 'UTC')
        local_dt = local_tz.localize(
            datetime.combine(date, time(hour=hours, minute=minutes))
        )
        return local_dt.astimezone(pytz.UTC).replace(tzinfo=None)

    def _prepare_slot_values(self, date, employee=False, project=False):
        self.ensure_one()
        employee = employee or self.employee_id
        project = project or self.project_id
        resource_type = 'employee' if employee else 'material' if self.material_id else 'open'
        return {
            'resource_type': resource_type,
            'employee_id': employee.id if employee else False,
            'material_id': self.material_id.id if resource_type == 'material' else False,
            'role_id': self.role_id.id,
            'project_id': project.id if project else False,
            'task_id': self.task_id.id if self.task_id.project_id == project else False,
            'company_id': (
                employee.company_id.id
                or project.company_id.id
                or self.company_id.id
            ),
            'start_datetime': self._local_datetime(date, self.start_hour),
            'end_datetime': self._local_datetime(
                date, self.start_hour + self.duration
            ),
            'note': self.note,
        }
