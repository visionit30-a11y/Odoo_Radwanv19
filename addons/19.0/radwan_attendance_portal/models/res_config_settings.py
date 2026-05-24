# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    radwan_attendance_geo_required = fields.Boolean(
        string="Geolocation Required",
        config_parameter="radwan_attendance_portal.geo_required",
        default=True,
    )
    radwan_attendance_max_accuracy = fields.Float(
        string="Maximum Allowed Accuracy (m)",
        config_parameter="radwan_attendance_portal.max_accuracy",
        default=150.0,
    )
    radwan_attendance_reject_outside_range = fields.Boolean(
        string="Reject Outside Allowed Range",
        config_parameter="radwan_attendance_portal.reject_outside_range",
        default=True,
    )
    radwan_attendance_log_rejected_attempts = fields.Boolean(
        string="Log Rejected Attempts",
        config_parameter="radwan_attendance_portal.log_rejected_attempts",
        default=True,
    )
    radwan_attendance_show_distance_details = fields.Boolean(
        string="Show Distance Details to Employee",
        config_parameter="radwan_attendance_portal.show_distance_details",
        default=True,
    )
    radwan_attendance_outside_range_message = fields.Text(
        string="Outside Range Message",
        config_parameter="radwan_attendance_portal.outside_range_message",
        default="You are outside your allowed attendance locations. The operation cannot be recorded from this location.",
    )
    radwan_attendance_weak_accuracy_message = fields.Text(
        string="Weak Accuracy Message",
        config_parameter="radwan_attendance_portal.weak_accuracy_message",
        default="Location accuracy is weak. Please try again from a clearer location.",
    )
