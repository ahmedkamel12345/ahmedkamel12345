{
    "name": "Accounting Reports Hub",
    "summary": "Customizable accounting reports with advanced filters",
    "version": "16.0.1.0.0",
    "author": "Custom",
    "website": "https://example.com",
    "license": "LGPL-3",
    "category": "Accounting/Accounting",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "data/account_report_template_data.xml",
        "views/account_report_template_views.xml",
        "views/account_report_filter_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
}
