# -*- coding: utf-8 -*-

from odoo import fields, models


class MealGroup(models.Model):
    _name = "meal.group"
    _description = "Meal Group"
    _order = "name"

    name = fields.Char(required=True, default="Default Meal Group")
    active = fields.Boolean(default=True)
