from odoo import api, fields, models, tools


class FinancialRatioReport(models.Model):
    _name = "financial.ratio.report"
    _description = "Financial Ratio SQL Report"
    _auto = False
    _rec_name = "period_label"
    _order = "period_start desc"

    company_id = fields.Many2one("res.company", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", readonly=True)
    period_start = fields.Date(readonly=True, index=True)
    period_label = fields.Char(readonly=True)

    current_assets = fields.Monetary(currency_field="currency_id", readonly=True)
    current_liabilities = fields.Monetary(currency_field="currency_id", readonly=True)
    inventory = fields.Monetary(currency_field="currency_id", readonly=True)
    cash = fields.Monetary(currency_field="currency_id", readonly=True)
    revenue = fields.Monetary(currency_field="currency_id", readonly=True)
    cogs = fields.Monetary(currency_field="currency_id", readonly=True)
    operating_income = fields.Monetary(currency_field="currency_id", readonly=True)
    net_profit = fields.Monetary(currency_field="currency_id", readonly=True)
    total_assets = fields.Monetary(currency_field="currency_id", readonly=True)
    equity = fields.Monetary(currency_field="currency_id", readonly=True)
    receivables = fields.Monetary(currency_field="currency_id", readonly=True)

    comparison_mode = fields.Selection(
        [("previous_period", "Previous Period"), ("last_year", "Same Period Last Year")],
        compute="_compute_comparison_mode",
    )

    current_ratio = fields.Float(compute="_compute_ratios", digits=(16, 4))
    quick_ratio = fields.Float(compute="_compute_ratios", digits=(16, 4))
    cash_ratio = fields.Float(compute="_compute_ratios", digits=(16, 4))
    gross_profit_margin = fields.Float(compute="_compute_ratios", digits=(16, 4))
    net_profit_margin = fields.Float(compute="_compute_ratios", digits=(16, 4))
    operating_margin = fields.Float(compute="_compute_ratios", digits=(16, 4))
    roa = fields.Float(compute="_compute_ratios", digits=(16, 4))
    roe = fields.Float(compute="_compute_ratios", digits=(16, 4))
    inventory_turnover = fields.Float(compute="_compute_ratios", digits=(16, 4))
    receivable_turnover = fields.Float(compute="_compute_ratios", digits=(16, 4))

    comparison_revenue = fields.Monetary(currency_field="currency_id", compute="_compute_comparison_values")
    change_percentage = fields.Float(compute="_compute_comparison_values", digits=(16, 4))

    prev_period_revenue = fields.Monetary(currency_field="currency_id", readonly=True)
    prev_year_revenue = fields.Monetary(currency_field="currency_id", readonly=True)

    @api.depends_context("comparison_mode")
    def _compute_comparison_mode(self):
        mode = self.env.context.get("comparison_mode", "previous_period")
        for rec in self:
            rec.comparison_mode = mode

    @api.depends(
        "current_assets",
        "current_liabilities",
        "inventory",
        "cash",
        "revenue",
        "cogs",
        "operating_income",
        "net_profit",
        "total_assets",
        "equity",
        "receivables",
    )
    def _compute_ratios(self):
        for rec in self:
            rec.current_ratio = rec.current_assets / rec.current_liabilities if rec.current_liabilities else 0.0
            rec.quick_ratio = (rec.current_assets - rec.inventory) / rec.current_liabilities if rec.current_liabilities else 0.0
            rec.cash_ratio = rec.cash / rec.current_liabilities if rec.current_liabilities else 0.0

            gross_profit = rec.revenue - rec.cogs
            rec.gross_profit_margin = (gross_profit / rec.revenue) * 100 if rec.revenue else 0.0
            rec.net_profit_margin = (rec.net_profit / rec.revenue) * 100 if rec.revenue else 0.0
            rec.operating_margin = (rec.operating_income / rec.revenue) * 100 if rec.revenue else 0.0
            rec.roa = (rec.net_profit / rec.total_assets) * 100 if rec.total_assets else 0.0
            rec.roe = (rec.net_profit / rec.equity) * 100 if rec.equity else 0.0
            rec.inventory_turnover = rec.cogs / rec.inventory if rec.inventory else 0.0
            rec.receivable_turnover = rec.revenue / rec.receivables if rec.receivables else 0.0

    @api.depends("revenue", "prev_period_revenue", "prev_year_revenue")
    @api.depends_context("comparison_mode")
    def _compute_comparison_values(self):
        mode = self.env.context.get("comparison_mode", "previous_period")
        for rec in self:
            base = rec.prev_year_revenue if mode == "last_year" else rec.prev_period_revenue
            rec.comparison_revenue = base
            rec.change_percentage = ((rec.revenue - base) / base) * 100 if base else 0.0

    def _select(self):
        return """
            SELECT
                row_number() OVER(ORDER BY t.company_id, t.period_start) AS id,
                t.company_id,
                t.currency_id,
                t.period_start,
                to_char(t.period_start, 'YYYY-MM') AS period_label,
                t.current_assets,
                t.current_liabilities,
                t.inventory,
                t.cash,
                t.revenue,
                t.cogs,
                t.operating_income,
                t.net_profit,
                t.total_assets,
                t.equity,
                t.receivables,
                LAG(t.revenue) OVER(PARTITION BY t.company_id ORDER BY t.period_start) AS prev_period_revenue,
                LAG(t.revenue, 12) OVER(PARTITION BY t.company_id ORDER BY t.period_start) AS prev_year_revenue
            FROM (
                SELECT
                    aml.company_id,
                    rc.currency_id,
                    date_trunc('month', aml.date)::date AS period_start,
                    SUM(CASE WHEN aa.account_type IN ('asset_current', 'asset_cash') THEN aml.balance ELSE 0 END) AS current_assets,
                    ABS(SUM(CASE WHEN aa.account_type = 'liability_current' THEN aml.balance ELSE 0 END)) AS current_liabilities,
                    SUM(CASE WHEN aa.account_type = 'asset_current' AND lower(aa.name) LIKE '%inventory%' THEN aml.balance ELSE 0 END) AS inventory,
                    SUM(CASE WHEN aa.account_type = 'asset_cash' THEN aml.balance ELSE 0 END) AS cash,
                    ABS(SUM(CASE WHEN aa.account_type IN ('income', 'income_other') THEN aml.balance ELSE 0 END)) AS revenue,
                    SUM(CASE WHEN aa.account_type = 'expense_direct_cost' THEN aml.balance ELSE 0 END) AS cogs,
                    ABS(SUM(CASE WHEN aa.account_type IN ('income', 'income_other') THEN aml.balance ELSE 0 END))
                        - SUM(CASE WHEN aa.account_type IN ('expense', 'expense_depreciation', 'expense_direct_cost') THEN aml.balance ELSE 0 END) AS operating_income,
                    ABS(SUM(CASE WHEN aa.account_type IN ('income', 'income_other') THEN aml.balance ELSE 0 END))
                        - SUM(CASE WHEN aa.account_type IN ('expense', 'expense_depreciation', 'expense_direct_cost') THEN aml.balance ELSE 0 END) AS net_profit,
                    SUM(CASE WHEN aa.account_type LIKE 'asset%' THEN aml.balance ELSE 0 END) AS total_assets,
                    ABS(SUM(CASE WHEN aa.account_type = 'equity' THEN aml.balance ELSE 0 END)) AS equity,
                    SUM(CASE WHEN aa.account_type = 'asset_receivable' THEN aml.balance ELSE 0 END) AS receivables
                FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                JOIN account_account aa ON aa.id = aml.account_id
                JOIN res_company rc ON rc.id = aml.company_id
                WHERE am.state IN ('draft', 'posted')
                GROUP BY aml.company_id, rc.currency_id, date_trunc('month', aml.date)
            ) t
        """

    def init(self):
        self.env.cr.execute("CREATE INDEX IF NOT EXISTS aml_company_month_idx ON account_move_line (company_id, date)")
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"CREATE or REPLACE VIEW {self._table} AS ({self._select()})")
