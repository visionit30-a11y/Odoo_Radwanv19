from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields, models
from odoo.exceptions import UserError


class RadwanPlanningGenerateWizard(models.TransientModel):
    _name = 'radwan.planning.generate.wizard'
    _description = 'Generate Planning Shifts'

    date_start = fields.Date(
        required=True,
        default=lambda self: fields.Date.context_today(self),
    )
    date_stop = fields.Date(
        required=True,
        default=lambda self: self._default_date_stop(),
    )
    template_ids = fields.Many2many(
        'radwan.planning.template',
        string='Templates',
        required=True,
    )
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    project_id = fields.Many2one(
        'project.project',
        domain="[('allow_timesheets', '=', True), ('is_template', '=', False)]",
    )
    include_weekends = fields.Boolean(default=True)
    publish = fields.Boolean(string='Publish Generated Shifts')

    def _default_date_stop(self):
        months_ahead = (
            self.env['ir.config_parameter']
            .sudo()
            .get_param('radwan_project_planning.recurring_months_ahead', '1')
        )
        try:
            months_ahead = int(months_ahead)
        except ValueError:
            months_ahead = 1
        return fields.Date.context_today(self) + relativedelta(
            months=max(months_ahead, 1)
        )

    def action_generate(self):
        self.ensure_one()
        if self.date_stop < self.date_start:
            raise UserError(self.env._('End date must be after start date.'))
        created_slots = self.env['radwan.planning.slot']
        current = self.date_start
        while current <= self.date_stop:
            if self.include_weekends or current.weekday() < 5:
                created_slots |= self._generate_day(current)
            current += timedelta(days=1)
        if self.publish:
            created_slots.action_publish()
        action = self.env.ref(
            'radwan_project_planning.action_radwan_planning_slot'
        ).read()[0]
        action['domain'] = [('id', 'in', created_slots.ids)]
        return action

    def _generate_day(self, date):
        Slot = self.env['radwan.planning.slot']
        created_slots = Slot
        employees = self.employee_ids or self.env['hr.employee']
        for template in self.template_ids:
            if employees:
                for employee in employees:
                    values = template._prepare_slot_values(
                        date,
                        employee=employee,
                        project=self.project_id or template.project_id,
                    )
                    created_slots |= Slot.create(values)
            else:
                values = template._prepare_slot_values(
                    date,
                    project=self.project_id or template.project_id,
                )
                created_slots |= Slot.create(values)
        return created_slots
