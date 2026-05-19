# -*- coding: utf-8 -*-

from odoo import models


class PerformanceAppraiser(models.Model):
    _inherit = "performance.appraiser"

    def _valid_field_parameter(self, field, name):
        return name in {"max", "min"} or super()._valid_field_parameter(field, name)
