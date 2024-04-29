# pylint: disable=W0104
{
    "name": "Import Project Tasks (GAP v2)",
    "description": "Create Project Tasks from GAP v2",
    "summary": "Create Project Tasks from GAP v2",
    "version": "17.0.1.0.0",
    "category": "Productivity",
    "author": "Aurelien ROY",
    "mainteners": ["Aurelien ROY"],
    "website": "https://odoo.com",
    "depends": [
        "base",
        "mail",
        "project",
        "project_task_import",
    ],
    "external_dependencies": {
        "python": [
            "openpyxl",
        ]
    },
    "data": [
        "templates/description.xml",
        "wizard/import_project_tasks.xml",
    ],
    "demo": [],
    "assets": {},
    "installable": True,
    "auto_install": False,
    "application": False,
    "license": "LGPL-3",
}
