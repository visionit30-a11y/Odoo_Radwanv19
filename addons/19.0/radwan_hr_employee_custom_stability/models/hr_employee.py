# -*- coding: utf-8 -*-

from datetime import date

from odoo import fields, models
from odoo.exceptions import ValidationError

try:
    from hijridate import Gregorian, Hijri
except ImportError:
    Gregorian = None
    Hijri = None


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _radwan_to_western_digits(self, value):
        translation_table = str.maketrans({
            "٠": "0",
            "١": "1",
            "٢": "2",
            "٣": "3",
            "٤": "4",
            "٥": "5",
            "٦": "6",
            "٧": "7",
            "٨": "8",
            "٩": "9",
            "۰": "0",
            "۱": "1",
            "۲": "2",
            "۳": "3",
            "۴": "4",
            "۵": "5",
            "۶": "6",
            "۷": "7",
            "۸": "8",
            "۹": "9",
        })
        return str(value or "").translate(translation_table)

    def _radwan_ensure_hijri_library(self):
        if Hijri is None or Gregorian is None:
            raise ValidationError(self.env._(
                "Hijri date conversion library is not installed. "
                "Please install it using: pip install hijridate"
            ))

    def _radwan_hijri_string_to_gregorian_date(self, hijri_value):
        self._radwan_ensure_hijri_library()

        parsed_value = self._radwan_parse_hijri_date(hijri_value)
        if not parsed_value:
            return False

        year, month, day = parsed_value

        try:
            gregorian_date = Hijri(year, month, day).to_gregorian()
        except (OverflowError, TypeError, ValueError) as error:
            raise ValidationError(self.env._(
                "Invalid Hijri date or unsupported Hijri date range. Details: %s",
                error,
            ))

        return date(gregorian_date.year, gregorian_date.month, gregorian_date.day)

    def _radwan_gregorian_to_hijri_string(self, gregorian_date):
        self._radwan_ensure_hijri_library()

        if not gregorian_date:
            return False

        gregorian_date = fields.Date.to_date(gregorian_date)

        try:
            hijri_date = Gregorian(
                gregorian_date.year,
                gregorian_date.month,
                gregorian_date.day,
            ).to_hijri()
        except (OverflowError, TypeError, ValueError) as error:
            raise ValidationError(self.env._(
                "Could not convert Gregorian date to Hijri date. Details: %s",
                error,
            ))

        return "%04d/%02d/%02d" % (
            hijri_date.year,
            hijri_date.month,
            hijri_date.day,
        )

    def _radwan_validate_identification_number_value(
        self,
        identification,
        company_id=False,
        exclude_employee_id=False,
    ):
        identification = self._radwan_clean_identification_number(identification)

        if not identification:
            return False

        if not identification.isdigit():
            raise ValidationError(self.env._(
                "ID / Iqama Number must contain digits only."
            ))

        if len(identification) > 10:
            raise ValidationError(self.env._(
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

            if duplicate_identification != identification:
                continue

            company_name = (
                self.env["res.company"].browse(company_id).display_name
                if company_id else self.env._("Undefined Company")
            )
            raise ValidationError(self.env._(
                "ID / Iqama Number (%s) is already used by employee (%s) in company (%s).",
                identification,
                duplicate_employee.display_name,
                company_name,
            ))

        return identification
