# -*- coding: utf-8 -*-

from odoo import fields, models


class RadwanAttendancePermission(models.Model):
    _name = "radwan.attendance.permission"
    _description = "Employee Attendance Permission"
    _order = "request_date desc, id desc"

    name = fields.Char(string="Reference", default="New", readonly=True)
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True, ondelete="cascade", index=True)
    user_id = fields.Many2one("res.users", string="Requested By", required=True, readonly=True)
    attendance_id = fields.Many2one("hr.attendance", string="Attendance", readonly=True, ondelete="set null")
    request_date = fields.Date(string="Request Date", default=fields.Date.context_today, required=True)
    permission_type = fields.Selection(
        selection=[
            ("personal", "Personal Permission"),
            ("work", "Work Permission"),
            ("medical", "Medical Permission"),
            ("other", "Other"),
        ],
        string="Permission Type",
        required=True,
        default="personal",
    )
    time_from = fields.Float(string="From")
    time_to = fields.Float(string="To")
    reason = fields.Char(string="Reason", required=True)
    note = fields.Text(string="Notes")
    latitude = fields.Float(string="Latitude", digits=(10, 7), readonly=True, aggregator=None)
    longitude = fields.Float(string="Longitude", digits=(10, 7), readonly=True, aggregator=None)
    accuracy = fields.Float(string="Accuracy", readonly=True, aggregator=None)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("refused", "Refused"),
        ],
        string="Status",
        default="submitted",
        required=True,
        readonly=True,
    )
