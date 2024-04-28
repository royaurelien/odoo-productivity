# pylint: disable=C0103,C0116

from odoo import _, api, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.model
    def create_from_import(self, vals_list, project_id, filename):
        def _update(vals_list):
            def __update(vals):
                vals["project_id"] = project_id
                return vals

            return list(map(__update, vals_list))

        records = self.create(_update(vals_list))
        for record in records:
            record.message_post(
                body=_("Created automatically via file import (%s).") % filename
            )

        return records
