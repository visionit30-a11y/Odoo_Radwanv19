# -*- coding: utf-8 -*-

from odoo import _, fields, models


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
    radwan_checkin_photo = fields.Image(string="Check In Photo", readonly=True, max_width=1280, max_height=1280)
    radwan_checkout_photo = fields.Image(string="Check Out Photo", readonly=True, max_width=1280, max_height=1280)
    radwan_approval_state = fields.Selection(
        selection=[
            ("to_review", "To Review"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Approval Status",
        default="to_review",
        readonly=True,
        copy=False,
    )
    radwan_approved_by_id = fields.Many2one("res.users", string="Approved By", readonly=True, copy=False)
    radwan_approved_date = fields.Datetime(string="Approved Date", readonly=True, copy=False)
    radwan_rejected_by_id = fields.Many2one("res.users", string="Rejected By", readonly=True, copy=False)
    radwan_rejected_date = fields.Datetime(string="Rejected Date", readonly=True, copy=False)
    radwan_rejection_reason = fields.Text(string="Rejection Reason", readonly=True, copy=False)

    def action_radwan_open_nearest_location(self):
        self.ensure_one()
        return self.radwan_nearest_attendance_location_id.action_open_google_maps()

    def action_radwan_approve_attendance(self):
        self.write(
            {
                "radwan_approval_state": "approved",
                "radwan_approved_by_id": self.env.user.id,
                "radwan_approved_date": fields.Datetime.now(),
                "radwan_rejected_by_id": False,
                "radwan_rejected_date": False,
                "radwan_rejection_reason": False,
            }
        )

    def action_radwan_reject_attendance(self):
        self.write(
            {
                "radwan_approval_state": "rejected",
                "radwan_rejected_by_id": self.env.user.id,
                "radwan_rejected_date": fields.Datetime.now(),
                "radwan_rejection_reason": _("Rejected from Odoo attendance review."),
            }
        )
