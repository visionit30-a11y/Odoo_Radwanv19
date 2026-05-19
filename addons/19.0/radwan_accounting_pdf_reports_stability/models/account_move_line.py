# -*- coding: utf-8 -*-

import ast

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    accounting_pdf_analytic_names = fields.Char(
        string="Analytic Accounts",
        compute="_compute_accounting_pdf_analytic_names",
    )

    @api.depends("analytic_distribution")
    def _compute_accounting_pdf_analytic_names(self):
        for line in self:
            analytic_accounts = line.distribution_analytic_account_ids
            line.accounting_pdf_analytic_names = ", ".join(
                analytic_accounts.mapped("display_name")
            )

    @api.model
    def _query_get(self, domain=None):
        """Keep legacy accounting PDF reports compatible with Odoo 19.

        The third-party report module still expects the removed old-style
        ``_query_get`` tuple: tables, where clause and params. Build it from
        the Odoo 19 ``_search`` query object to avoid deprecated osv APIs.
        """
        context = dict(self.env.context or {})
        domain = domain or []
        if not isinstance(domain, (list, tuple)):
            domain = ast.literal_eval(domain)
        domain = list(domain)

        date_field = "date_maturity" if context.get("aged_balance") else "date"
        if context.get("date_to"):
            domain.append((date_field, "<=", context["date_to"]))
        if context.get("date_from"):
            if not context.get("strict_range"):
                domain += [
                    "|",
                    (date_field, ">=", context["date_from"]),
                    ("account_id.include_initial_balance", "=", True),
                ]
            elif context.get("initial_bal"):
                domain.append((date_field, "<", context["date_from"]))
            else:
                domain.append((date_field, ">=", context["date_from"]))

        if context.get("journal_ids"):
            domain.append(("journal_id", "in", context["journal_ids"]))

        state = context.get("state")
        if state and state.lower() != "all":
            domain.append(("parent_state", "=", state))

        if context.get("company_id"):
            domain.append(("company_id", "=", context["company_id"]))
        elif context.get("allowed_company_ids"):
            domain.append(("company_id", "in", self.env.companies.ids))
        else:
            domain.append(("company_id", "=", self.env.company.id))

        if context.get("reconcile_date"):
            domain += [
                "|",
                ("reconciled", "=", False),
                "|",
                ("matched_debit_ids.max_date", ">", context["reconcile_date"]),
                ("matched_credit_ids.max_date", ">", context["reconcile_date"]),
            ]

        if context.get("account_tag_ids"):
            domain.append(("account_id.tag_ids", "in", context["account_tag_ids"].ids))
        if context.get("account_ids"):
            domain.append(("account_id", "in", context["account_ids"].ids))
        if context.get("analytic_tag_ids") and "analytic_tag_ids" in self._fields:
            domain.append(("analytic_tag_ids", "in", context["analytic_tag_ids"].ids))
        if context.get("analytic_account_ids"):
            domain.append(("analytic_distribution", "in", context["analytic_account_ids"].ids))
        if context.get("partner_ids"):
            domain.append(("partner_id", "in", context["partner_ids"].ids))
        if context.get("partner_categories"):
            domain.append(("partner_id.category_id", "in", context["partner_categories"].ids))

        domain += [
            ("display_type", "not in", ("line_section", "line_note")),
            ("parent_state", "!=", "cancel"),
        ]
        query = self._search(domain, active_test=True)
        return (
            query.from_clause.code,
            query.where_clause.code,
            query.from_clause.params + query.where_clause.params,
        )
