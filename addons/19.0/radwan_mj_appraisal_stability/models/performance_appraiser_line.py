# -*- coding: utf-8 -*-

from odoo import models


class PerformanceAppraiserLine(models.Model):
    _inherit = "performance.appraiser.line"

    def _valid_field_parameter(self, field, name):
        return name in {"max", "min", "tracking"} or super()._valid_field_parameter(
            field,
            name,
        )
