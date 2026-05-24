# Radwan Employee Profile Detail Views

These files extend the same Odoo employee form, but only for fields and tabs
whose models are defined by `radwan_hr_employee_profile_details`.

- `hr_employee_form_tabs.xml`
  Adds profile-detail tabs, extra fields, and the final tab order.

- `hr_employee_profile_sections.xml`
  Refines the HR Information tab with profile-detail sections, including
  passport details and social insurance data.

Keep these view records in this module because the referenced fields are
defined here. Moving them into `radwan_hr_employee_custom` would create a module
dependency cycle.
