# -*- coding: utf-8 -*-

from odoo import fields, models


class RadwanAttendancePhotoPreview(models.TransientModel):
    _name = "radwan.attendance.photo.preview"
    _description = "Attendance Photo Preview"

    name = fields.Char(string="Title", readonly=True)
    attendance_id = fields.Many2one("hr.attendance", string="Attendance", readonly=True)
    employee_id = fields.Many2one(related="attendance_id.employee_id", string="Employee", readonly=True)
    photo_type = fields.Selection(
        selection=[
            ("check_in", "Check In Photo"),
            ("check_out", "Check Out Photo"),
        ],
        string="Photo Type",
        readonly=True,
    )
    photo = fields.Image(string="Photo", readonly=True, max_width=1920, max_height=1920)
