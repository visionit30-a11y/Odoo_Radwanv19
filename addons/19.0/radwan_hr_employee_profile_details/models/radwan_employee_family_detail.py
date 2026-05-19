from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RadwanEmployeeFamilyDetail(models.Model):
    _name = "radwan.employee.family.detail"
    _description = "Employee Family Detail"
    _order = "name, id"

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(string="Name", required=True)
    relationship = fields.Char(string="Relationship")
    date_of_birth = fields.Date(string="Date of Birth")
    id_type = fields.Selection(
        selection=[
            ("national_id", "National ID"),
            ("iqama", "Iqama"),
            ("border_number", "Border Number"),
            ("passport", "Passport"),
            ("other", "Other"),
        ],
        string="ID Type",
    )
    id_number = fields.Char(string="ID Number")
    id_start_date = fields.Date(string="ID Start Date")
    id_end_date = fields.Date(string="ID End Date")
    passport_number = fields.Char(string="Passport Number")
    passport_issue_place = fields.Char(string="Passport Issue Place")
    passport_start_date = fields.Date(string="Passport Start Date")
    passport_end_date = fields.Date(string="Passport End Date")
    ticket_by = fields.Selection(
        selection=[
            ("company", "Company"),
            ("employee", "Employee"),
        ],
        string="Ticket By",
    )
    medical_by = fields.Selection(
        selection=[
            ("company", "Company"),
            ("employee", "Employee"),
        ],
        string="Medical By",
    )
    is_in_contract = fields.Selection(
        selection=[
            ("yes", "Yes"),
            ("no", "No"),
        ],
        string="Is in Contract",
    )

    @api.constrains(
        "date_of_birth",
        "id_start_date",
        "id_end_date",
        "passport_start_date",
        "passport_end_date",
    )
    def _check_family_dates(self):
        today = fields.Date.context_today(self)
        for family in self:
            if family.date_of_birth and family.date_of_birth > today:
                raise ValidationError(self.env._(
                    "Date of Birth cannot be in the future."
                ))
            if (
                family.id_start_date
                and family.id_end_date
                and family.id_end_date < family.id_start_date
            ):
                raise ValidationError(self.env._(
                    "ID End Date must be on or after ID Start Date."
                ))
            if (
                family.passport_start_date
                and family.passport_end_date
                and family.passport_end_date < family.passport_start_date
            ):
                raise ValidationError(self.env._(
                    "Passport End Date must be on or after Passport Start Date."
                ))
