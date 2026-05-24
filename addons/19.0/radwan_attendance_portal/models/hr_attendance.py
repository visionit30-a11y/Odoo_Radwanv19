# -*- coding: utf-8 -*-

from odoo import fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    radwan_in_accuracy = fields.Float(string="Check In Accuracy", readonly=True, aggregator=None)
    radwan_out_accuracy = fields.Float(string="Check Out Accuracy", readonly=True, aggregator=None)
    radwan_check_in_user_id = fields.Many2one("res.users", string="Check In User", readonly=True)
    radwan_check_out_user_id = fields.Many2one("res.users", string="Check Out User", readonly=True)
    radwan_check_in_source = fields.Selection(
        selection=[
            ("portal", "Employee Portal"),
            ("backend", "Backend"),
        ],
        string="Check In Source",
        readonly=True,
    )
    radwan_check_out_source = fields.Selection(
        selection=[
            ("portal", "Employee Portal"),
            ("backend", "Backend"),
        ],
        string="Check Out Source",
        readonly=True,
    )
    radwan_location_status = fields.Selection(
        selection=[
            ("inside", "Inside Range"),
            ("outside", "Outside Range"),
            ("weak_accuracy", "Weak Location Accuracy"),
            ("unavailable", "Location Unavailable"),
        ],
        string="Location Status",
        readonly=True,
    )
    radwan_location_warning_message = fields.Text(string="Location Warning Message", readonly=True)
    radwan_nearest_attendance_location_id = fields.Many2one(
        "radwan.attendance.location",
        string="Nearest Attendance Location",
        readonly=True,
    )
    radwan_distance_to_nearest_location = fields.Float(
        string="Distance to Nearest Location (m)",
        readonly=True,
        aggregator=None,
    )
    radwan_allowed_radius = fields.Float(string="Allowed Radius (m)", readonly=True, aggregator=None)
    radwan_checkin_location_id = fields.Many2one(
        "radwan.attendance.location",
        string="Accepted Check In Location",
        readonly=True,
    )
    radwan_checkout_location_id = fields.Many2one(
        "radwan.attendance.location",
        string="Accepted Check Out Location",
        readonly=True,
    )
    radwan_checkin_latitude = fields.Float(string="Check In Latitude", digits=(10, 7), readonly=True, aggregator=None)
    radwan_checkin_longitude = fields.Float(string="Check In Longitude", digits=(10, 7), readonly=True, aggregator=None)
    radwan_checkin_accuracy = fields.Float(string="Check In Accuracy", readonly=True, aggregator=None)
    radwan_checkout_latitude = fields.Float(string="Check Out Latitude", digits=(10, 7), readonly=True, aggregator=None)
    radwan_checkout_longitude = fields.Float(string="Check Out Longitude", digits=(10, 7), readonly=True, aggregator=None)
    radwan_checkout_accuracy = fields.Float(string="Check Out Accuracy", readonly=True, aggregator=None)

    def action_radwan_open_nearest_location(self):
        self.ensure_one()
        return self.radwan_nearest_attendance_location_id.action_open_google_maps()
