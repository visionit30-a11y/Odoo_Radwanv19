from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    radwan_planning_slot_ids = fields.One2many(
        'radwan.planning.slot',
        'project_id',
        string='Planning Shifts',
    )
    radwan_planning_slot_count = fields.Integer(
        compute='_compute_radwan_planning_metrics'
    )
    radwan_planned_hours = fields.Float(compute='_compute_radwan_planning_metrics')

    def _compute_radwan_planning_metrics(self):
        grouped = self.env['radwan.planning.slot']._read_group(
            [('project_id', 'in', self.ids), ('state', '!=', 'cancelled')],
            ['project_id'],
            ['__count', 'allocated_hours:sum'],
        )
        metrics = {
            project.id: (count, allocated_hours)
            for project, count, allocated_hours in grouped
        }
        for project in self:
            count, hours = metrics.get(project.id, (0, 0.0))
            project.radwan_planning_slot_count = count
            project.radwan_planned_hours = hours

    def action_view_radwan_planning_slots(self):
        self.ensure_one()
        action = self.env.ref(
            'radwan_project_planning.action_radwan_planning_slot'
        ).read()[0]
        action['domain'] = [('project_id', '=', self.id)]
        action['context'] = {'default_project_id': self.id}
        return action
