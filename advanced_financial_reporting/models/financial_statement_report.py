from odoo import fields, models, tools


class FinancialStatementReport(models.Model):
    _name = "financial.statement.report"
    _description = "Financial Statement SQL Report"
    _auto = False
    _rec_name = "move_line_name"
    _order = "date desc, id desc"

    date = fields.Date(index=True)
    company_id = fields.Many2one("res.company", index=True)
    company_currency_id = fields.Many2one("res.currency")
    move_line_id = fields.Many2one("account.move.line", readonly=True)
    move_id = fields.Many2one("account.move", readonly=True)
    move_name = fields.Char(readonly=True)
    move_line_name = fields.Char(readonly=True)
    parent_state = fields.Selection(
        [("draft", "Draft"), ("posted", "Posted"), ("cancel", "Cancelled")],
        readonly=True,
        index=True,
    )

    journal_id = fields.Many2one("account.journal", readonly=True, index=True)
    account_id = fields.Many2one("account.account", readonly=True, index=True)
    partner_id = fields.Many2one("res.partner", readonly=True, index=True)
    analytic_account_id = fields.Many2one("account.analytic.account", readonly=True, index=True)
    salesperson_id = fields.Many2one("res.users", readonly=True, index=True)
    branch_id = fields.Many2one("res.company", readonly=True, index=True)
    warehouse_id = fields.Many2one("stock.warehouse", readonly=True, index=True)

    account_type = fields.Char(readonly=True)
    statement_type = fields.Selection(
        [
            ("balance_sheet", "Financial Position"),
            ("income_statement", "Income Statement"),
            ("cash_flow", "Cash Flow Summary"),
        ],
        readonly=True,
        index=True,
    )
    statement_section = fields.Char(readonly=True, index=True)

    debit = fields.Monetary(currency_field="company_currency_id", readonly=True)
    credit = fields.Monetary(currency_field="company_currency_id", readonly=True)
    balance = fields.Monetary(currency_field="company_currency_id", readonly=True)
    amount_currency = fields.Monetary(currency_field="company_currency_id", readonly=True)

    def action_open_journal_item(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.move_line_name or self.move_name,
            "res_model": "account.move.line",
            "view_mode": "form",
            "res_id": self.move_line_id.id,
            "target": "current",
        }

    @property
    def _table_query(self):
        return """
            SELECT
                aml.id AS id,
                aml.id AS move_line_id,
                aml.move_id,
                am.name AS move_name,
                COALESCE(NULLIF(aml.name, ''), am.ref, am.name) AS move_line_name,
                aml.date,
                aml.company_id,
                rc.currency_id AS company_currency_id,
                am.state AS parent_state,
                aml.journal_id,
                aml.account_id,
                aml.partner_id,
                NULL::integer AS analytic_account_id,
                am.invoice_user_id AS salesperson_id,
                aml.company_id AS branch_id,
                NULL::integer AS warehouse_id,
                aa.account_type,
                CASE
                    WHEN aa.account_type LIKE 'asset%%' OR aa.account_type LIKE 'liability%%' OR aa.account_type = 'equity' THEN 'balance_sheet'
                    WHEN aa.account_type IN ('income', 'income_other', 'expense', 'expense_depreciation', 'expense_direct_cost') THEN 'income_statement'
                    ELSE 'cash_flow'
                END AS statement_type,
                CASE
                    WHEN aa.account_type IN ('asset_current', 'asset_cash') THEN 'current_assets'
                    WHEN aa.account_type = 'asset_non_current' THEN 'non_current_assets'
                    WHEN aa.account_type = 'liability_current' THEN 'current_liabilities'
                    WHEN aa.account_type = 'liability_non_current' THEN 'non_current_liabilities'
                    WHEN aa.account_type = 'equity' THEN 'equity'
                    WHEN aa.account_type IN ('income', 'income_other') THEN 'revenue'
                    WHEN aa.account_type IN ('expense', 'expense_depreciation', 'expense_direct_cost') THEN 'expenses'
                    ELSE 'other'
                END AS statement_section,
                aml.debit,
                aml.credit,
                aml.balance,
                aml.amount_currency
            FROM account_move_line aml
            JOIN account_move am ON am.id = aml.move_id
            JOIN account_account aa ON aa.id = aml.account_id
            JOIN res_company rc ON rc.id = aml.company_id
            WHERE am.state IN ('draft', 'posted')
        """

    def init(self):
        self.env.cr.execute("CREATE INDEX IF NOT EXISTS aml_company_date_idx ON account_move_line (company_id, date)")
        self.env.cr.execute("CREATE INDEX IF NOT EXISTS aml_account_date_idx ON account_move_line (account_id, date)")
        self.env.cr.execute("CREATE INDEX IF NOT EXISTS aml_partner_date_idx ON account_move_line (partner_id, date)")
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"CREATE or REPLACE VIEW {self._table} AS ({self._table_query})")
