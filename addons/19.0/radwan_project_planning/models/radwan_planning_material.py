from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RadwanPlanningMaterial(models.Model):
    _name = 'radwan.planning.material'
    _description = 'Planning Material Resource'
    _order = 'name'

    name = fields.Char(required=True)
    code = fields.Char()
    active = fields.Boolean(default=True)
    color = fields.Integer(default=0)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        readonly=True,
    )
    hourly_cost = fields.Monetary(currency_field='currency_id')
    calendar_id = fields.Many2one(
        'resource.calendar',
        string='Working Time',
        domain="[('company_id', 'in', [company_id, False])]",
    )
    role_ids = fields.Many2many(
        'radwan.planning.role',
        'radwan_planning_material_role_rel',
        'material_id',
        'role_id',
        string='Roles',
        domain="[('company_id', 'in', [company_id, False])]",
    )
    default_role_id = fields.Many2one(
        'radwan.planning.role',
        domain="[('id', 'in', role_ids)]",
    )
    slot_count = fields.Integer(compute='_compute_slot_count')

    @api.constrains('default_role_id', 'role_ids')
    def _check_default_role(self):
        for material in self:
            if (
                material.default_role_id
                and material.default_role_id not in material.role_ids
            ):
                raise ValidationError(
                    self.env._('The default role must be one of the material roles.')
                )

    @api.onchange('role_ids')
    def _onchange_role_ids(self):
        for material in self:
            if material.default_role_id not in material.role_ids:
                material.default_role_id = material.role_ids[:1]

    def _compute_slot_count(self):
        grouped = self.env['radwan.planning.slot']._read_group(
            [('material_id', 'in', self.ids)],
            ['material_id'],
            ['__count'],
        )
        counts = {material.id: count for material, count in grouped}
        for material in self:
            material.slot_count = counts.get(material.id, 0)

    def action_view_slots(self):
        self.ensure_one()
        action = self.env.ref(
            'radwan_project_planning.action_radwan_planning_slot'
        ).read()[0]
        action['domain'] = [('material_id', '=', self.id)]
        action['context'] = {
            'default_resource_type': 'material',
            'default_material_id': self.id,
        }
        return action
