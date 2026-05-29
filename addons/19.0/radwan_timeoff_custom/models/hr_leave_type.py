# -*- coding: utf-8 -*-

from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    include_weekly_off_at_start = fields.Boolean(
        string="Include Weekly Off Days at Leave Start",
        help="If enabled, weekly off days at the beginning of the leave period will be counted in leave duration.",
    )
    include_weekly_off_inside = fields.Boolean(
        string="Include Weekly Off Days Inside Leave Period",
        help="If enabled, weekly off days that fall between two leave days will be counted in leave duration.",
    )
    include_weekly_off_at_end = fields.Boolean(
        string="Include Weekly Off Days at Leave End",
        help="If enabled, weekly off days at the end of the leave period will be counted in leave duration.",
    )
