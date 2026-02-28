from odoo import fields, models


class AccountReportFilterWizard(models.TransientModel):
    _name = "account.report.filter.wizard"
    _description = "Account Report Filter Wizard"

    template_id = fields.Many2one(
        "account.report.template",
        string="Report Template",
        required=True,
        domain=[("active", "=", True)],
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    date_from = fields.Date()
    date_to = fields.Date()
    journal_ids = fields.Many2many("account.journal", string="Journals")
    account_ids = fields.Many2many("account.account", string="Accounts")
    partner_ids = fields.Many2many("res.partner", string="Partners")
    move_state = fields.Selection(
        [("all", "All Entries"), ("posted", "Posted Entries"), ("draft", "Draft Entries")],
        default="posted",
        required=True,
    )

    def action_open_filtered_lines(self):
        self.ensure_one()
        domain = list(self.template_id._get_base_domain())

        domain.append(("company_id", "=", self.company_id.id))

        if self.date_from:
            domain.append(("date", ">=", self.date_from))
        if self.date_to:
            domain.append(("date", "<=", self.date_to))

        if self.journal_ids:
            domain.append(("journal_id", "in", self.journal_ids.ids))
        if self.account_ids:
            domain.append(("account_id", "in", self.account_ids.ids))
        if self.partner_ids:
            domain.append(("partner_id", "in", self.partner_ids.ids))

        if self.move_state == "posted":
            domain.append(("parent_state", "=", "posted"))
        elif self.move_state == "draft":
            domain.append(("parent_state", "=", "draft"))

        report_type = self.template_id.report_type
        if report_type == "receivable":
            domain.append(("account_id.account_type", "=", "asset_receivable"))
        elif report_type == "payable":
            domain.append(("account_id.account_type", "=", "liability_payable"))
        elif report_type == "tax":
            domain.append(("tax_line_id", "!=", False))

        return {
            "type": "ir.actions.act_window",
            "name": self.template_id.name,
            "res_model": "account.move.line",
            "view_mode": "list,pivot,graph",
            "domain": domain,
            "context": {
                "search_default_group_by_account_id": 1,
                "search_default_group_by_date": 1,
            },
            "target": "current",
        }
