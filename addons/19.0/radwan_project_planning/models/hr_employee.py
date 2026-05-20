from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    radwan_planning_role_ids = fields.Many2many(
        'radwan.planning.role',
        'radwan_planning_role_employee_rel',
        'employee_id',
        'role_id',
        string='Planning Roles',
    )
    radwan_planning_slot_ids = fields.One2many(
        'radwan.planning.slot',
        'employee_id',
        string='Planning Shifts',
    )
    radwan_planning_slot_count = fields.Integer(
        compute='_compute_radwan_planning_slot_count'
    )

    def _compute_radwan_planning_slot_count(self):
        grouped = self.env['radwan.planning.slot']._read_group(
            [('employee_id', 'in', self.ids), ('state', '!=', 'cancelled')],
            ['employee_id'],
            ['__count'],
        )
        counts = {employee.id: count for employee, count in grouped}
        for employee in self:
            employee.radwan_planning_slot_count = counts.get(employee.id, 0)

    def action_view_radwan_planning_slots(self):
        self.ensure_one()
        action = self.env.ref(
            'radwan_project_planning.action_radwan_planning_slot'
        ).read()[0]
        action['domain'] = [('employee_id', '=', self.id)]
        action['context'] = {
            'default_resource_type': 'employee',
            'default_employee_id': self.id,
        }
        return action
