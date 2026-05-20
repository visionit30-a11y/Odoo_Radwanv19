from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RadwanEmployeeTravelTicket(models.Model):
    _name = "radwan.employee.travel.ticket"
    _description = "Employee Travel Ticket"
    _order = "date_from desc, id desc"

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True,
    )
    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To")
    destination_from = fields.Char(string="Destination From")
    destination_to = fields.Char(string="Destination To")
    total_cost = fields.Monetary(
        string="Total Cost",
        currency_field="currency_id",
    )
    booking_number = fields.Char(string="Booking Number")
    boarding_number = fields.Char(string="Boarding Number")
    responsibility = fields.Selection(
        selection=[
            ("company", "On Company"),
            ("employee", "On Employee"),
        ],
        string="Responsibility",
        default="company",
        required=True,
    )

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        for ticket in self:
            if ticket.employee_id.company_id:
                ticket.company_id = ticket.employee_id.company_id

    @api.constrains("date_from", "date_to")
    def _check_ticket_dates(self):
        for ticket in self:
            if ticket.date_from and ticket.date_to and ticket.date_to < ticket.date_from:
                raise ValidationError(self.env._(
                    "Date To must be on or after Date From."
                ))


class RadwanEmployeeVisa(models.Model):
    _name = "radwan.employee.visa"
    _description = "Employee Visa"
    _order = "date_from desc, issue_date desc, id desc"

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    visa_number = fields.Char(string="Visa Number", required=True)
    visa_type = fields.Char(string="Visa Type")
    issue_date = fields.Date(string="Issue Date")
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    purpose = fields.Char(string="Purpose")
    actual_exit_datetime = fields.Datetime(string="Actual Exit")
    actual_return_datetime = fields.Datetime(string="Actual Return")
    issuing_authority = fields.Char(string="Issuing Authority")
    paid_by = fields.Selection(
        selection=[
            ("company", "On Company"),
            ("employee", "On Employee"),
        ],
        string="Paid By",
        default="company",
        required=True,
    )

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        for visa in self:
            if visa.employee_id.company_id:
                visa.company_id = visa.employee_id.company_id

    @api.constrains(
        "date_from",
        "date_to",
        "actual_exit_datetime",
        "actual_return_datetime",
    )
    def _check_visa_dates(self):
        for visa in self:
            if visa.date_from and visa.date_to and visa.date_to < visa.date_from:
                raise ValidationError(self.env._(
                    "Date To must be on or after Date From."
                ))
            if (
                visa.actual_exit_datetime
                and visa.actual_return_datetime
                and visa.actual_return_datetime < visa.actual_exit_datetime
            ):
                raise ValidationError(self.env._(
                    "Actual Return must be on or after Actual Exit."
                ))
