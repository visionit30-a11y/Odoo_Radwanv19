# -*- coding: utf-8 -*-

import re
from datetime import date, timedelta

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import format_date

try:
    from hijridate import Hijri, Gregorian
except Exception:
    Hijri = None
    Gregorian = None


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # ---------------------------------------------------------
    # Internal HR Data
    # ---------------------------------------------------------

    radwan_employee_code = fields.Char(
        string="Employee Internal Code",
        copy=False
    )

    radwan_file_number = fields.Char(
        string="Paper File Number",
        copy=False
    )

    radwan_joining_date = fields.Date(
        string="Actual Joining Date"
    )

    radwan_employment_status = fields.Selection(
        selection=[
            ("active", "Active"),
            ("vacation", "On Vacation"),
            ("suspended", "Suspended"),
            ("ended", "Service Ended"),
        ],
        string="Operational Employment Status",
        default="active"
    )

    radwan_operation_site = fields.Char(
        string="Actual Operation Site"
    )

    # ---------------------------------------------------------
    # Identity / Iqama Data
    # ---------------------------------------------------------

    radwan_id_type = fields.Selection(
        selection=[
            ("national_id", "National ID"),
            ("iqama", "Iqama"),
            ("border_number", "Border Number"),
            ("other", "Other"),
        ],
        string="ID Type"
    )

    radwan_id_issue_date = fields.Date(
        string="ID / Iqama Issue Date"
    )

    radwan_id_expiry_date = fields.Date(
        string="ID / Iqama Expiry Date"
    )

    radwan_id_expiry_hijri = fields.Char(
        string="ID / Iqama Expiry Date Hijri"
    )

    radwan_iqama_profession = fields.Char(
        string="Iqama Profession"
    )

    radwan_border_number = fields.Char(
        string="Border Number",
        copy=False
    )

    radwan_sponsor_name = fields.Char(
        string="Sponsor Name"
    )

    # ---------------------------------------------------------
    # Passport Data
    # ---------------------------------------------------------

    radwan_passport_expiry_date = fields.Date(
        string="Passport Expiry Date"
    )

    # ---------------------------------------------------------
    # Medical Insurance Data
    # ---------------------------------------------------------

    radwan_medical_insurance_company = fields.Char(
        string="Medical Insurance Company"
    )

    radwan_medical_policy_number = fields.Char(
        string="Medical Policy Number",
        copy=False
    )

    radwan_medical_insurance_class = fields.Selection(
        selection=[
            ("vip", "VIP"),
            ("a", "A"),
            ("b", "B"),
            ("c", "C"),
            ("other", "Other"),
        ],
        string="Medical Insurance Class"
    )

    radwan_medical_insurance_end = fields.Date(
        string="Medical Insurance End Date"
    )

    # ---------------------------------------------------------
    # Contract Data
    # ---------------------------------------------------------

    radwan_contract_number = fields.Char(
        string="Contract Number",
        copy=False
    )

    radwan_contract_start_date = fields.Date(
        string="Contract Start Date"
    )

    radwan_contract_end_date = fields.Date(
        string="Contract End Date"
    )

    # ---------------------------------------------------------
    # Date Display Fields
    # ---------------------------------------------------------

    radwan_id_expiry_date_display = fields.Char(
        string="ID / Iqama Expiry Date",
        compute="_compute_radwan_date_displays",
        readonly=True
    )

    radwan_passport_expiry_date_display = fields.Char(
        string="Passport Expiry Date",
        compute="_compute_radwan_date_displays",
        readonly=True
    )

    radwan_medical_insurance_end_display = fields.Char(
        string="Medical Insurance End Date",
        compute="_compute_radwan_date_displays",
        readonly=True
    )

    radwan_contract_end_date_display = fields.Char(
        string="Contract End Date",
        compute="_compute_radwan_date_displays",
        readonly=True
    )

    # ---------------------------------------------------------
    # Computed Expiry Status Fields
    # ---------------------------------------------------------

    radwan_id_status = fields.Selection(
        selection=[
            ("not_set", "Not Set"),
            ("valid", "Valid"),
            ("expiring_soon", "Expiring Soon"),
            ("expired", "Expired"),
        ],
        string="ID / Iqama Status",
        compute="_compute_radwan_expiry_statuses",
        store=True,
        readonly=True
    )

    radwan_passport_status = fields.Selection(
        selection=[
            ("not_set", "Not Set"),
            ("valid", "Valid"),
            ("expiring_soon", "Expiring Soon"),
            ("expired", "Expired"),
        ],
        string="Passport Status",
        compute="_compute_radwan_expiry_statuses",
        store=True,
        readonly=True
    )

    radwan_medical_insurance_status = fields.Selection(
        selection=[
            ("not_set", "Not Set"),
            ("valid", "Valid"),
            ("expiring_soon", "Expiring Soon"),
            ("expired", "Expired"),
        ],
        string="Medical Insurance Status",
        compute="_compute_radwan_expiry_statuses",
        store=True,
        readonly=True
    )

    radwan_contract_status = fields.Selection(
        selection=[
            ("not_set", "Not Set"),
            ("valid", "Valid"),
            ("expiring_soon", "Expiring Soon"),
            ("expired", "Expired"),
        ],
        string="Contract Status",
        compute="_compute_radwan_expiry_statuses",
        store=True,
        readonly=True
    )

    # ---------------------------------------------------------
    # Create / Write
    # ---------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._radwan_prepare_identity_values(vals)
            self._radwan_validate_identification_values_before_save(vals=vals)

        records = super().create(vals_list)
        records._check_radwan_identification_id_rules()
        return records

    def write(self, vals):
        vals = dict(vals)
        self._radwan_prepare_identity_values(vals)

        for employee in self:
            employee._radwan_validate_identification_values_before_save(
                vals=vals,
                employee=employee
            )

        result = super().write(vals)
        self._check_radwan_identification_id_rules()
        return result

    def _radwan_prepare_identity_values(self, vals):
        if "identification_id" in vals:
            cleaned_identification = self._radwan_clean_identification_number(
                vals.get("identification_id")
            )
            vals["identification_id"] = cleaned_identification or False

        if "radwan_id_expiry_hijri" in vals:
            if vals.get("radwan_id_expiry_hijri"):
                gregorian_date = self._radwan_hijri_string_to_gregorian_date(
                    vals.get("radwan_id_expiry_hijri")
                )
                vals["radwan_id_expiry_date"] = fields.Date.to_string(gregorian_date)
                vals["radwan_id_expiry_hijri"] = self._radwan_normalize_hijri_string(
                    vals.get("radwan_id_expiry_hijri")
                )
            else:
                vals["radwan_id_expiry_date"] = False

        elif "radwan_id_expiry_date" in vals:
            if vals.get("radwan_id_expiry_date"):
                gregorian_date = fields.Date.to_date(vals.get("radwan_id_expiry_date"))
                vals["radwan_id_expiry_hijri"] = self._radwan_gregorian_to_hijri_string(
                    gregorian_date
                )
            else:
                vals["radwan_id_expiry_hijri"] = False

    # ---------------------------------------------------------
    # Identification Validation
    # ---------------------------------------------------------

    def _radwan_to_western_digits(self, value):
        translation_table = str.maketrans(
            "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
            "01234567890123456789"
        )
        return str(value or "").translate(translation_table)

    def _radwan_clean_identification_number(self, value):
        value = self._radwan_to_western_digits(value)
        value = re.sub(r"\s+", "", value.strip())
        return value

    def _radwan_get_effective_company_id(self, employee=False, vals=False):
        vals = vals or {}

        if "company_id" in vals and vals.get("company_id"):
            return vals.get("company_id")

        if employee and employee.company_id:
            return employee.company_id.id

        return self.env.company.id if self.env.company else False

    def _radwan_validate_identification_number_value(
        self,
        identification,
        company_id=False,
        exclude_employee_id=False
    ):
        identification = self._radwan_clean_identification_number(identification)

        if not identification:
            return False

        if not identification.isdigit():
            raise ValidationError(_(
                "ID / Iqama Number must contain digits only."
            ))

        if len(identification) > 10:
            raise ValidationError(_(
                "ID / Iqama Number must not exceed 10 digits."
            ))

        duplicate_domain = [
            ("identification_id", "!=", False),
        ]

        if exclude_employee_id:
            duplicate_domain.append(("id", "!=", exclude_employee_id))

        if company_id:
            duplicate_domain += [
                "|",
                ("company_id", "=", company_id),
                ("company_id", "=", False),
            ]
        else:
            duplicate_domain.append(("company_id", "=", False))

        possible_duplicates = self.sudo().with_context(active_test=False).search(
            duplicate_domain
        )

        for duplicate_employee in possible_duplicates:
            duplicate_identification = self._radwan_clean_identification_number(
                duplicate_employee.identification_id
            )

            if duplicate_identification == identification:
                company_name = (
                    self.env["res.company"].browse(company_id).display_name
                    if company_id else "Undefined Company"
                )

                raise ValidationError(_(
                    "ID / Iqama Number (%s) is already used by employee (%s) in company (%s)."
                ) % (
                    identification,
                    duplicate_employee.display_name,
                    company_name
                ))

        return identification

    def _radwan_validate_identification_values_before_save(self, vals, employee=False):
        if employee:
            identification = vals.get(
                "identification_id",
                employee.identification_id
            )
            company_id = self._radwan_get_effective_company_id(
                employee=employee,
                vals=vals
            )
            exclude_employee_id = employee.id
        else:
            identification = vals.get("identification_id")
            company_id = self._radwan_get_effective_company_id(vals=vals)
            exclude_employee_id = False

        return self._radwan_validate_identification_number_value(
            identification=identification,
            company_id=company_id,
            exclude_employee_id=exclude_employee_id
        )

    @api.constrains("identification_id", "company_id")
    def _check_radwan_identification_id_rules(self):
        for employee in self:
            company_id = employee._radwan_get_effective_company_id(
                employee=employee
            )

            employee._radwan_validate_identification_number_value(
                identification=employee.identification_id,
                company_id=company_id,
                exclude_employee_id=employee.id
            )

    @api.onchange("identification_id")
    def _onchange_radwan_identification_id(self):
        for employee in self:
            if employee.identification_id:
                cleaned_identification = employee._radwan_clean_identification_number(
                    employee.identification_id
                )

                if employee.identification_id != cleaned_identification:
                    employee.identification_id = cleaned_identification

                if not cleaned_identification.isdigit():
                    raise ValidationError(_(
                        "ID / Iqama Number must contain digits only."
                    ))

                if len(cleaned_identification) > 10:
                    raise ValidationError(_(
                        "ID / Iqama Number must not exceed 10 digits."
                    ))

    # ---------------------------------------------------------
    # Onchange: Gregorian <-> Hijri
    # ---------------------------------------------------------

    @api.onchange("radwan_id_expiry_date")
    def _onchange_radwan_id_expiry_date(self):
        for employee in self:
            if employee.radwan_id_expiry_date:
                employee.radwan_id_expiry_hijri = employee._radwan_gregorian_to_hijri_string(
                    employee.radwan_id_expiry_date
                )
            else:
                employee.radwan_id_expiry_hijri = False

    @api.onchange("radwan_id_expiry_hijri")
    def _onchange_radwan_id_expiry_hijri(self):
        for employee in self:
            if employee.radwan_id_expiry_hijri:
                gregorian_date = employee._radwan_hijri_string_to_gregorian_date(
                    employee.radwan_id_expiry_hijri
                )
                employee.radwan_id_expiry_date = gregorian_date
                employee.radwan_id_expiry_hijri = employee._radwan_normalize_hijri_string(
                    employee.radwan_id_expiry_hijri
                )
            else:
                employee.radwan_id_expiry_date = False

    # ---------------------------------------------------------
    # Hijri Conversion Helpers
    # ---------------------------------------------------------

    def _radwan_ensure_hijri_library(self):
        if Hijri is None or Gregorian is None:
            raise ValidationError(_(
                "Hijri date conversion library is not installed. "
                "Please install it using: pip install hijridate"
            ))

    def _radwan_parse_hijri_date(self, hijri_value):
        text_value = str(hijri_value or "").strip()

        if not text_value:
            return False

        text_value = self._radwan_to_western_digits(text_value)
        text_value = re.sub(r"\s+", "", text_value)

        parts = re.split(r"[-/\.]", text_value)
        parts = [part for part in parts if part]

        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            raise ValidationError(_(
                "Invalid Hijri date format. Please use one of these formats: "
                "1448/02/01 or 1448-02-01 or 01/02/1448."
            ))

        numbers = [int(part) for part in parts]

        if len(parts[0]) == 4 or numbers[0] >= 1300:
            year, month, day = numbers
        elif len(parts[2]) == 4 or numbers[2] >= 1300:
            day, month, year = numbers
        else:
            raise ValidationError(_(
                "Invalid Hijri date format. The Hijri year must be clear, for example: 1448/02/01."
            ))

        return year, month, day

    def _radwan_normalize_hijri_string(self, hijri_value):
        parsed_value = self._radwan_parse_hijri_date(hijri_value)

        if not parsed_value:
            return False

        year, month, day = parsed_value
        return "%04d/%02d/%02d" % (year, month, day)

    def _radwan_hijri_string_to_gregorian_date(self, hijri_value):
        self._radwan_ensure_hijri_library()

        parsed_value = self._radwan_parse_hijri_date(hijri_value)

        if not parsed_value:
            return False

        year, month, day = parsed_value

        try:
            gregorian_date = Hijri(year, month, day).to_gregorian()
            return date(gregorian_date.year, gregorian_date.month, gregorian_date.day)
        except Exception as error:
            raise ValidationError(_(
                "Invalid Hijri date or unsupported Hijri date range. Details: %s"
            ) % error)

    def _radwan_gregorian_to_hijri_string(self, gregorian_date):
        self._radwan_ensure_hijri_library()

        if not gregorian_date:
            return False

        gregorian_date = fields.Date.to_date(gregorian_date)

        try:
            hijri_date = Gregorian(
                gregorian_date.year,
                gregorian_date.month,
                gregorian_date.day
            ).to_hijri()
            return "%04d/%02d/%02d" % (hijri_date.year, hijri_date.month, hijri_date.day)
        except Exception as error:
            raise ValidationError(_(
                "Could not convert Gregorian date to Hijri date. Details: %s"
            ) % error)

    # ---------------------------------------------------------
    # Date Display Helpers
    # ---------------------------------------------------------

    def _radwan_format_date_for_user(self, date_value):
        if not date_value:
            return ""
        return format_date(self.env, date_value)

    @api.depends_context("lang")
    @api.depends(
        "radwan_id_expiry_date",
        "radwan_passport_expiry_date",
        "radwan_medical_insurance_end",
        "radwan_contract_end_date"
    )
    def _compute_radwan_date_displays(self):
        for employee in self:
            employee.radwan_id_expiry_date_display = employee._radwan_format_date_for_user(
                employee.radwan_id_expiry_date
            )
            employee.radwan_passport_expiry_date_display = employee._radwan_format_date_for_user(
                employee.radwan_passport_expiry_date
            )
            employee.radwan_medical_insurance_end_display = employee._radwan_format_date_for_user(
                employee.radwan_medical_insurance_end
            )
            employee.radwan_contract_end_date_display = employee._radwan_format_date_for_user(
                employee.radwan_contract_end_date
            )

    # ---------------------------------------------------------
    # Expiry Status Computation
    # ---------------------------------------------------------

    def _radwan_get_expiry_status(self, expiry_date, today, warning_date):
        expiry_date = fields.Date.to_date(expiry_date)

        if not expiry_date:
            return "not_set"

        if expiry_date < today:
            return "expired"

        if expiry_date <= warning_date:
            return "expiring_soon"

        return "valid"

    @api.depends(
        "radwan_id_expiry_date",
        "radwan_passport_expiry_date",
        "radwan_medical_insurance_end",
        "radwan_contract_end_date"
    )
    def _compute_radwan_expiry_statuses(self):
        for employee in self:
            today = fields.Date.context_today(employee)
            warning_date = today + timedelta(days=30)

            employee.radwan_id_status = employee._radwan_get_expiry_status(
                employee.radwan_id_expiry_date,
                today,
                warning_date
            )

            employee.radwan_passport_status = employee._radwan_get_expiry_status(
                employee.radwan_passport_expiry_date,
                today,
                warning_date
            )

            employee.radwan_medical_insurance_status = employee._radwan_get_expiry_status(
                employee.radwan_medical_insurance_end,
                today,
                warning_date
            )

            employee.radwan_contract_status = employee._radwan_get_expiry_status(
                employee.radwan_contract_end_date,
                today,
                warning_date
            )

    # ---------------------------------------------------------
    # Scheduled Action
    # ---------------------------------------------------------

    @api.model
    def radwan_cron_refresh_expiry_statuses(self):
        """Refresh stored expiry status fields daily.

        This keeps filters, group-by, and list badges accurate as dates move
        from Valid to Expiring Soon to Expired without manually editing records.
        """
        employees = self.with_context(active_test=False).search([])
        if employees:
            employees._compute_radwan_expiry_statuses()
        return True

