# pylint: disable=C0103,C0116

from odoo import models


class ProjectProject(models.Model):
    _inherit = "project.project"

    def action_import_tasks(self):
        self.ensure_one()

        action = self.env["ir.actions.actions"]._for_xml_id(
            "project_task_import.import_project_tasks_action"
        )
        action.update(
            {
                "context": {
                    "default_project_id": self.id,
                    "default_locked": True,
                },
            }
        )
        return action
