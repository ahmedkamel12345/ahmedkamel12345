{
    "name": "Advanced Financial Reporting",
    "summary": "Enterprise-grade financial statements and ratio analytics",
    "version": "18.0.1.0.0",
    "category": "Accounting/Accounting",
    "license": "LGPL-3",
    "author": "Your Company",
    "depends": ["account", "analytic", "stock"],
    "data": [
        "security/financial_reporting_security.xml",
        "security/ir.model.access.csv",
        "security/financial_reporting_rules.xml",
        "views/financial_reporting_views.xml",
        "wizard/financial_reporting_wizard_views.xml",
    ],
    "installable": True,
    "application": True,
}
