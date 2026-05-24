# Radwan Employee Form Views

The employee form is assembled by Odoo from the base `hr.view_employee_form`
plus inherited views. Keep employee UI ownership organized as follows:

- `hr_employee_hr_information.xml`
  Adds the Radwan HR Information tab and custom HR fields that are defined by
  `radwan_hr_employee_custom`.

- `expiry_monitoring_views.xml`
  Adds the expiry monitoring action, list view, and menu entries.

- `../static/src/scss/hr_employee_rtl.scss`
  Controls Arabic/RTL-only visual layout for the employee form, including field
  alignment, details sections, tabs, expiry badges, and smart buttons.

Profile-detail fields that are defined by `radwan_hr_employee_profile_details`
must keep their view inheritance in that module to avoid circular dependencies.
