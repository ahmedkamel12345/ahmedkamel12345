from dateutil.relativedelta import relativedelta

from odoo import fields, models


class FinancialReportingWizard(models.TransientModel):
    _name = "financial.reporting.wizard"
    _description = "Financial Reporting Wizard"

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    comparison_mode = fields.Selection(
        [("previous_period", "Previous Period"), ("last_year", "Same Period Last Year")],
        default="previous_period",
        required=True,
    )
    company_ids = fields.Many2many(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    journal_ids = fields.Many2many("account.journal")
    account_ids = fields.Many2many("account.account")
    analytic_account_ids = fields.Many2many("account.analytic.account")
    partner_ids = fields.Many2many("res.partner")
    branch_ids = fields.Many2many("res.company", string="Branches")
    warehouse_ids = fields.Many2many("stock.warehouse")
    salesperson_ids = fields.Many2many("res.users")
    target_move = fields.Selection(
        [("posted", "Posted Entries"), ("all", "All Entries")],
        default="posted",
        required=True,
    )

    def _base_domain(self):
        self.ensure_one()
        domain = [
            ("company_id", "in", self.company_ids.ids),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
        ]
        if self.target_move == "posted":
            domain.append(("parent_state", "=", "posted"))
        if self.journal_ids:
            domain.append(("journal_id", "in", self.journal_ids.ids))
        if self.account_ids:
            domain.append(("account_id", "in", self.account_ids.ids))
        if self.analytic_account_ids:
            domain.append(("analytic_account_id", "in", self.analytic_account_ids.ids))
        if self.partner_ids:
            domain.append(("partner_id", "in", self.partner_ids.ids))
        if self.branch_ids:
            domain.append(("branch_id", "in", self.branch_ids.ids))
        if self.warehouse_ids:
            domain.append(("warehouse_id", "in", self.warehouse_ids.ids))
        if self.salesperson_ids:
            domain.append(("salesperson_id", "in", self.salesperson_ids.ids))
        return domain

    def _comparison_context(self):
        self.ensure_one()
        delta = relativedelta(years=1) if self.comparison_mode == "last_year" else relativedelta(
            days=(self.date_to - self.date_from).days + 1
        )
        return {
            "comparison_mode": self.comparison_mode,
            "comparison_date_from": self.date_from - delta,
            "comparison_date_to": self.date_to - delta,
        }

    def action_open_financial_statements(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Financial Statements",
            "res_model": "financial.statement.report",
            "view_mode": "list,pivot,graph",
            "domain": self._base_domain(),
            "context": self._comparison_context(),
            "target": "current",
        }

    def action_open_financial_ratios(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Financial Ratios Comparison",
            "res_model": "financial.ratio.report",
            "view_mode": "list,pivot,graph",
            "domain": [
                ("company_id", "in", self.company_ids.ids),
                ("period_start", ">=", self.date_from),
                ("period_start", "<=", self.date_to),
            ],
            "context": self._comparison_context(),
            "target": "current",
        }
