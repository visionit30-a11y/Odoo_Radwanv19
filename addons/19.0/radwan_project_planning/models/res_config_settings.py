from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    radwan_planning_allow_unassignment = fields.Boolean(
        string='Allow Unassignment',
        config_parameter='radwan_project_planning.allow_unassignment',
    )
    radwan_planning_project_planning = fields.Boolean(
        string='Project Planning',
        default=True,
        config_parameter='radwan_project_planning.project_planning',
    )
    radwan_planning_recurring_months_ahead = fields.Integer(
        string='Generate Shifts Months Ahead',
        default=6,
        config_parameter='radwan_project_planning.recurring_months_ahead',
    )

    @api.constrains('radwan_planning_recurring_months_ahead')
    def _check_radwan_planning_recurring_months_ahead(self):
        for settings in self:
            if settings.radwan_planning_recurring_months_ahead < 1:
                raise ValidationError(
                    self.env._('The planning horizon must be at least one month.')
                )
