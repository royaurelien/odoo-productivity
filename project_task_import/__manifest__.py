# pylint: disable=W0104
{
    "name": "Import GAP",
    "description": "",
    "summary": "",
    "version": "17.0.1.0.0",
    "category": "Productivity",
    "author": "Aurelien ROY",
    "mainteners": ["Aurelien ROY"],
    "website": "https://odoo.com",
    "depends": [
        "base",
        "mail",
        "project",
    ],
    "external_dependencies": {
        "python": [
            "openpyxl",
        ]
    },
    "data": [
        "security/ir.model.access.csv",
        # "data/upgrade_plan_tags.xml",
        # "views/upgrade_plan.xml",
        "wizard/import_project_tasks.xml",
    ],
    "demo": [],
    "assets": {},
    "installable": True,
    "auto_install": False,
    "application": False,
    "license": "LGPL-3",
}
