from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class AccountReportTemplate(models.Model):
    _name = "account.report.template"
    _description = "Account Report Template"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    report_type = fields.Selection(
        [
            ("general", "General Ledger"),
            ("receivable", "Customer Balance"),
            ("payable", "Vendor Balance"),
            ("tax", "Tax Lines"),
            ("journal", "Journal Items"),
        ],
        default="general",
        required=True,
    )
    description = fields.Text(translate=True)
    base_domain = fields.Text(
        string="Base Domain",
        default="[]",
        help="Optional base domain in python list format. Example: [('debit', '>', 0)]",
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("account_report_template_code_uniq", "unique(code)", "Template code must be unique."),
    ]

    @api.constrains("base_domain")
    def _check_base_domain(self):
        for record in self:
            record._get_base_domain()

    def _get_base_domain(self):
        self.ensure_one()
        try:
            result = safe_eval(self.base_domain or "[]", {"context": dict(self.env.context)})
        except Exception as error:
            raise ValidationError(
                self.env._("Invalid base domain syntax for template '%s': %s")
                % (self.display_name, error)
            ) from error

        if not isinstance(result, list):
            raise ValidationError(self.env._("Base domain must evaluate to a list."))
        return result
