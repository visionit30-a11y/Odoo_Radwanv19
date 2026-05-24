# -*- coding: utf-8 -*-

from odoo import fields, models


class RadwanAttendanceAttemptLog(models.Model):
    _name = "radwan.attendance.attempt.log"
    _description = "Rejected Attendance Attempt"
    _order = "attempt_datetime desc, id desc"

    employee_id = fields.Many2one("hr.employee", string="Employee", required=True, ondelete="cascade", index=True)
    user_id = fields.Many2one("res.users", string="User", required=True, readonly=True)
    action_type = fields.Selection(
        selection=[
            ("check_in", "Check In"),
            ("check_out", "Check Out"),
            ("permission", "Permission"),
        ],
        string="Operation Type",
        required=True,
    )
    attempt_datetime = fields.Datetime(string="Attempt Date and Time", default=fields.Datetime.now, required=True)
    latitude = fields.Float(string="Latitude", digits=(10, 7), readonly=True, aggregator=None)
    longitude = fields.Float(string="Longitude", digits=(10, 7), readonly=True, aggregator=None)
    accuracy = fields.Float(string="Accuracy", readonly=True, aggregator=None)
    nearest_attendance_location_id = fields.Many2one(
        "radwan.attendance.location",
        string="Nearest Attendance Location",
        readonly=True,
    )
    distance_to_nearest_location = fields.Float(string="Distance to Nearest Location (m)", readonly=True, aggregator=None)
    allowed_radius = fields.Float(string="Allowed Radius (m)", readonly=True, aggregator=None)
    rejection_reason = fields.Selection(
        selection=[
            ("outside_range", "Outside Allowed Range"),
            ("weak_accuracy", "Weak Location Accuracy"),
            ("location_unavailable", "Location Unavailable"),
        ],
        string="Rejection Reason",
        required=True,
    )
    warning_message = fields.Text(string="Warning Message", readonly=True)
    google_maps_url = fields.Char(string="Google Maps URL", compute="_compute_google_maps_url")
    user_agent = fields.Char(string="User Agent", readonly=True)
    ip_address = fields.Char(string="IP Address", readonly=True)

    def _compute_google_maps_url(self):
        for attempt in self:
            if attempt.latitude and attempt.longitude:
                attempt.google_maps_url = "https://maps.google.com?q=%s,%s" % (
                    attempt.latitude,
                    attempt.longitude,
                )
            else:
                attempt.google_maps_url = False

    def action_open_google_maps(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": self.google_maps_url or "https://maps.google.com",
            "target": "new",
        }
