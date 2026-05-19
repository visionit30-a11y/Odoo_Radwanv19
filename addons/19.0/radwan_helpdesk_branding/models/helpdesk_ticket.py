import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    attachment_count = fields.Integer(
        string="Ticket Attachment Count",
        compute="_compute_attachment_count",
    )

    @api.model
    def _check_sla_status(self):
        """Check SLA tickets with fewer repeated searches per ticket."""
        tickets = self.search([
            ("state", "not in", ["resolved", "closed", "cancelled"]),
            ("sla_policy_id", "!=", False),
        ])
        if not tickets:
            return True

        tickets._compute_sla_status()

        reminder_rules = self.env["helpdesk.reminder.rule"]
        if self._get_config_bool("helpdesk.enable_reminders", True):
            reminder_rules = reminder_rules.search([
                ("active", "=", True),
            ], order="sequence, id")

        escalation_rules = self.env["helpdesk.escalation.rule"]
        if self._get_config_bool("helpdesk.enable_escalation", True):
            escalation_rules = escalation_rules.search([
                ("active", "=", True),
            ], order="sequence, escalation_level, id")

        for ticket in tickets:
            ticket._check_sla_warnings()
            ticket._check_sla_escalations()
            ticket._check_sla_breaches()
            if escalation_rules:
                ticket._radwan_check_escalation_rules(escalation_rules)
            if reminder_rules:
                ticket._radwan_check_reminder_rules(reminder_rules)

        return True

    def _radwan_check_reminder_rules(self, rules):
        self.ensure_one()
        for rule in rules:
            try:
                rule.create_reminder(self)
            except Exception as error:
                _logger.error(
                    "Error creating reminder from rule %s on ticket %s: %s",
                    rule.name,
                    self.ticket_number,
                    error,
                )

    def _radwan_check_escalation_rules(self, rules):
        self.ensure_one()
        for rule in rules:
            try:
                if not rule._evaluate_condition(self) or not rule._evaluate_trigger(self):
                    continue

                last_escalation = self.env["helpdesk.escalation.log"].search([
                    ("rule_id", "=", rule.id),
                    ("ticket_id", "=", self.id),
                ], order="escalation_date desc", limit=1)
                if last_escalation and not rule.repeat_escalation:
                    continue

                if last_escalation and rule.repeat_escalation:
                    hours_since = (
                        fields.Datetime.now() - last_escalation.escalation_date
                    ).total_seconds() / 3600.0
                    if hours_since < rule.repeat_interval_hours:
                        continue

                    escalation_count = self.env["helpdesk.escalation.log"].search_count([
                        ("rule_id", "=", rule.id),
                        ("ticket_id", "=", self.id),
                    ])
                    if escalation_count >= rule.max_repeats:
                        continue

                rule.execute_on_ticket(self)
            except Exception as error:
                _logger.error(
                    "Error executing escalation rule %s on ticket %s: %s",
                    rule.name,
                    self.ticket_number,
                    error,
                )

    def _radwan_last_sla_message(self, subject, body_text=False):
        self.ensure_one()
        domain = [
            ("model", "=", self._name),
            ("res_id", "=", self.id),
            ("subject", "ilike", subject),
        ]
        if body_text:
            domain.append(("body", "ilike", body_text))
        return self.env["mail.message"].sudo().search(
            domain,
            order="date desc",
            limit=1,
        )

    def _check_sla_warnings(self):
        self.ensure_one()
        if not self.sla_policy_id:
            return

        now = fields.Datetime.now()
        policy = self.sla_policy_id

        if self.sla_response_deadline and not self.assigned_date:
            elapsed = (now - self.create_date).total_seconds() / 3600.0
            percentage = (elapsed / policy.response_time) * 100 if policy.response_time > 0 else 0
            warning_threshold = policy.response_warning_threshold or 80.0
            escalation_threshold = policy.response_escalation_threshold or 90.0

            if warning_threshold <= percentage < escalation_threshold:
                last_warning = self._radwan_last_sla_message("SLA Warning")
                if not last_warning or (now - last_warning.date).total_seconds() > 3600:
                    self._send_sla_warning_alert("response", percentage)

        if self.sla_resolution_deadline and self.state not in ["resolved", "closed"]:
            elapsed = (now - self.create_date).total_seconds() / 3600.0
            percentage = (
                (elapsed / policy.resolution_time) * 100
                if policy.resolution_time > 0 else 0
            )
            warning_threshold = policy.resolution_warning_threshold or 80.0
            escalation_threshold = policy.resolution_escalation_threshold or 90.0

            if warning_threshold <= percentage < escalation_threshold:
                last_warning = self._radwan_last_sla_message("SLA Warning")
                if not last_warning or (now - last_warning.date).total_seconds() > 3600:
                    self._send_sla_warning_alert("resolution", percentage)

    def _check_sla_escalations(self):
        self.ensure_one()
        if not self.sla_policy_id:
            return

        now = fields.Datetime.now()
        policy = self.sla_policy_id

        if self.sla_response_deadline and not self.assigned_date:
            elapsed = (now - self.create_date).total_seconds() / 3600.0
            percentage = (elapsed / policy.response_time) * 100 if policy.response_time > 0 else 0
            escalation_threshold = policy.response_escalation_threshold or 90.0

            if escalation_threshold <= percentage < 100:
                last_escalation = self._radwan_last_sla_message("SLA Escalation")
                if (
                    not last_escalation
                    or (now - last_escalation.date).total_seconds() > 3600
                ):
                    self._send_sla_escalation_alert("response", percentage)

        if self.sla_resolution_deadline and self.state not in ["resolved", "closed"]:
            elapsed = (now - self.create_date).total_seconds() / 3600.0
            percentage = (
                (elapsed / policy.resolution_time) * 100
                if policy.resolution_time > 0 else 0
            )
            escalation_threshold = policy.resolution_escalation_threshold or 90.0

            if escalation_threshold <= percentage < 100:
                last_escalation = self._radwan_last_sla_message("SLA Escalation")
                if (
                    not last_escalation
                    or (now - last_escalation.date).total_seconds() > 3600
                ):
                    self._send_sla_escalation_alert("resolution", percentage)

    def _check_sla_breaches(self):
        self.ensure_one()
        if not self.sla_policy_id:
            return

        now = fields.Datetime.now()

        if self.sla_response_deadline and self.sla_response_deadline < now:
            if not self.assigned_date or self.assigned_date > self.sla_response_deadline:
                last_breach = self._radwan_last_sla_message("SLA Breach", "response")
                if not last_breach:
                    self._handle_sla_breach("response")

        if self.sla_resolution_deadline and self.sla_resolution_deadline < now:
            if self.state not in ["resolved", "closed"]:
                last_breach = self._radwan_last_sla_message("SLA Breach", "resolution")
                if not last_breach:
                    self._handle_sla_breach("resolution")
