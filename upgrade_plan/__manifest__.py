# pylint: disable=W0104
{
    "name": "Upgrade Plan",
    "description": "Define Odoo upgrade plans for your customers",
    "summary": "Define Odoo upgrade plans for your customers",
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
    "external_dependencies": {},
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/upgrade_plan_tags.xml",
        "views/upgrade_plan.xml",
        "views/upgrade_plan_line.xml",
        "views/upgrade_plan_tags.xml",
        "views/menu.xml",
    ],
    "demo": [],
    "assets": {},
    "installable": True,
    "auto_install": False,
    "application": False,
    "license": "LGPL-3",
}
