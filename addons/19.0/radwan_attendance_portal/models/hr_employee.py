# -*- coding: utf-8 -*-

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    radwan_attendance_location_ids = fields.Many2many(
        "radwan.attendance.location",
        "radwan_employee_attendance_location_rel",
        "employee_id",
        "location_id",
        string="Allowed Attendance Locations",
    )
