# pylint: disable = C0103


import logging

from odoo import api, fields, models

from odoo.addons.project_task_import.utils import (
    extract,
    extract_tags,
    prepare_tags,
    set_key,
    set_parents,
    set_tags,
)

_logger = logging.getLogger(__name__)


DEFAULT_SHEETS = [
    "Référentiel",
    "Ventes",
    "Achats",
    "Logistique",
    "Production_Qualité",
    "Finance_Comptabilité",
    "Marketing_Emailing",
    "Site Web_eCommerce",
    "Productivité",
    "Ressources humaines",
    "Services",
    "Technique",
    "Reprise de données",
]
AGG_COLS = [
    "Atelier",
    "Atelier sur Paramétrage avancé",
    "Rédaction FD",
    "Développement niveau 1",
    "Développement Expert",
    "Tests",
]


TIME_KEYS = [
    "Atelier sur Paramétrage avancé",
    "Développement niveau 1",
    "Développement Expert",
    "Rédaction FD",
]

DEFAULT_PARENT_KEY = "Flux"
DEFAULT_TASK_NAME = "{data['Sujet']}: {data['Description précise fonctionnelle']}"


class ImportProjectTasks(models.TransientModel):
    _inherit = "import.project.tasks"

    template = fields.Selection(
        selection_add=[("gap2", "GAP v2")],
        default="gap2",
        ondelete={"gap2": "set default"},
    )

    subject_and_flux = fields.Boolean(
        default=False,
        string="Tags Sujet et flux",
    )
    tags_times = fields.Boolean(
        default=False,
        string="Tags Estimation",
    )

    @api.model
    def _get_default_parent_key(self):
        return DEFAULT_PARENT_KEY

    @api.model
    def _get_default_sheets(self):
        return ",".join(DEFAULT_SHEETS)

    @api.model
    def _get_default_task_name(self):
        return DEFAULT_TASK_NAME

    @api.onchange("template")
    def onchange_template(self):
        if not self.template:
            self.sheets_to_import = ""
            self.prefix = ""

        if self.template == "gap2":
            self.sheets_to_import = self._get_default_sheets()
            self.prefix = self._get_default_task_name()

    @api.onchange("template")
    def onchange_subtasks(self):
        if not self.use_subtasks:
            self.parent_key = ""

        if self.template == "gap2":
            self.parent_key = self._get_default_parent_key()

    @api.model
    def _read_items(self, workbook):
        sheets = self.sheets_to_import.split(",") or DEFAULT_SHEETS

        def _sum(vals, keys):
            items = [vals[name] for name in vals.keys() if name in keys]
            return sum(filter(lambda x: isinstance(x, float), items))

        items = []
        for sheet_name in sheets:
            sheet = workbook[sheet_name]
            headers = [str(cell.value) for cell in sheet[2]]

            for row in sheet:
                res = dict(zip(headers, (cell.value for cell in row)))
                if not res.get("Choix") == "Keep":
                    continue

                res["Total"] = _sum(res, AGG_COLS)

                if not res["Total"]:
                    continue

                items.append(res)
        return items

    def parse_gap2(self, workbook):
        Tags = self.env["project.tags"].sudo()
        Task = self.env["project.task"].sudo()
        items = []
        search_tags = []

        if self.subject_and_flux:
            search_tags.append("subject_and_flux")

        if self.tags_times:
            search_tags.append("times")

        items = self._read_items(workbook)

        if "subject_and_flux" in search_tags:
            items = prepare_tags(items, ["Sujet", "Flux"], "value")

        if "times" in search_tags:
            items = prepare_tags(items, TIME_KEYS, "key")

        # Extract and set tags
        names = extract_tags(items)
        if names:
            mapping = Tags.search_or_create(names)
            items = set_tags(items, mapping)

        # Prepare parent tasks
        if self.use_subtasks:
            names = extract(items, self.parent_key)
            parents = [{"name": name, "flux": "master"} for name in names]
            records = Task.create_from_import(
                parents, self.project_id.id, self.import_filename
            )

            mapping = {item["name"]: item["id"] for item in records.read(["name"])}
            items = set_parents(items, mapping, self.parent_key)

        items = set_key(items, "name", self.prefix)

        tasks = list(map(Task._prepare_from_gap2, items))

        return tasks
