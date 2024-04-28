# pylint: disable=C0103,C0116

from odoo import api, models


class ProjectTags(models.Model):
    _inherit = "project.tags"

    @api.model
    def search_or_create(self, names):
        tags = self.search([("name", "in", list(names))]).read(["name"])
        to_create = names.difference({item["name"] for item in tags})

        if to_create:
            self.create([{"name": name} for name in to_create])
            tags = self.search([("name", "in", list(names))]).read(["name"])

        return {item["name"]: item["id"] for item in tags}
