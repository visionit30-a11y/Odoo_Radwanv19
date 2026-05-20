from odoo import api, fields, models


class RadwanPlanningRole(models.Model):
    _name = 'radwan.planning.role'
    _description = 'Planning Role'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    color = fields.Integer(default=0)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    employee_ids = fields.Many2many(
        'hr.employee',
        'radwan_planning_role_employee_rel',
        'role_id',
        'employee_id',
        string='Employees',
        domain="[('company_id', 'in', [company_id, False])]",
    )
    project_ids = fields.Many2many(
        'project.project',
        'radwan_planning_role_project_rel',
        'role_id',
        'project_id',
        string='Projects',
        domain="[('allow_timesheets', '=', True), ('is_template', '=', False)]",
    )
    slot_count = fields.Integer(compute='_compute_slot_count')

    def _compute_slot_count(self):
        grouped = self.env['radwan.planning.slot']._read_group(
            [('role_id', 'in', self.ids)],
            ['role_id'],
            ['__count'],
        )
        counts = {role.id: count for role, count in grouped}
        for role in self:
            role.slot_count = counts.get(role.id, 0)

    def action_view_slots(self):
        self.ensure_one()
        action = self.env.ref(
            'radwan_project_planning.action_radwan_planning_slot'
        ).read()[0]
        action['domain'] = [('role_id', '=', self.id)]
        action['context'] = {'default_role_id': self.id}
        return action
