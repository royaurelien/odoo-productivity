# pylint: disable = C0103

import itertools
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


def prepare_tags(vals_list, keys, mode="value"):
    """
    mode 'value': [{'key 1': 'a', 'key 2': 'b']}, ...] => [{'tags': ['a', 'b']}, ...]
    mode 'key': [{'key 3': 1.0, 'key 4': None]}, ...] => [{'tags': ['key 3']}, ...]
    """

    def apply(vals):
        vals.setdefault("tags", [])
        if mode == "value":
            tags = [v for k, v in vals.items() if v and k in keys]
        else:
            tags = [k for k, v in vals.items() if v and k in keys]
        vals["tags"] += tags

        return vals

    return list(map(apply, vals_list))


def extract_tags(vals_list):
    """
    [{'tags': ['a', 'b']}, {'tags': ['b', 'c']}]
        => ['a', 'b', 'c']
    """

    def search(vals):
        return vals.get("tags", [])

    return set(itertools.chain(*map(search, vals_list)))


def set_tags(vals_list, mapping):
    """
    [{'tags': ['a', 'b']}, {'tags': ['b', 'c']}]
        => [{'tag_ids': [6, False, [1,2]]}, {'tag_ids': [6, False, [2,3]]}]
    """

    def apply(vals: dict):
        names = vals.pop("tags")
        if not names:
            return vals

        tags = [mapping.get(k) for k in names]
        tags = list(filter(bool, tags))
        vals["tag_ids"] = [(6, False, tags)] if tags else False
        return vals

    return list(map(apply, vals_list))


def extract(vals_list, key, default=False):
    """
    [{'key': 'a'}, {'key': 'a'}, {'key': False}] => ['a']
    """

    def search(vals):
        return vals.get(key, default)

    return list(set(filter(bool, map(search, vals_list))))


def set_parents(vals_list, mapping):
    def apply(vals: dict):
        vals["parent_id"] = mapping.get(vals["Flux"], False)
        return vals

    return list(map(apply, vals_list))


READ_SHEETS = [
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
READ_KEYS = [
    "Atelier",
    "Atelier sur Paramétrage avancé",
    "Rédaction FD",
    "Développement niveau 1",
    "Développement Expert",
    "Tests",
]


TIME_kEYS = [
    "Atelier sur Paramétrage avancé",
    "Développement niveau 1",
    "Développement Expert",
    "Rédaction FD",
]


class ImportProjectTasks(models.TransientModel):
    _inherit = "import.project.tasks"

    template = fields.Selection(
        selection_add=[("gap2", "GAP v2")],
        default="gap2",
        ondelete={"gap2": "set default"},
    )

    subject_and_flux = fields.Boolean(
        default=False,
    )
    tags_times = fields.Boolean(
        default=False,
    )
    use_subtasks = fields.Boolean(
        default=False,
    )

    @api.model
    def _read_items(self, workbook):
        def _sum(vals, keys=READ_KEYS):
            items = [vals[name] for name in vals.keys() if name in keys]
            return sum(filter(lambda x: isinstance(x, float), items))

        items = []
        for sheet_name in READ_SHEETS:
            sheet = workbook[sheet_name]
            headers = [str(cell.value) for cell in sheet[2]]

            for row in sheet:
                res = dict(zip(headers, (cell.value for cell in row)))
                if not res.get("Choix") == "Keep":
                    continue

                res["Total"] = _sum(res)

                if not res["Total"]:
                    continue

                items.append(res)
        return items

    def parse_gap2(self, workbook):
        items = []
        search_tags = []

        if self.subject_and_flux:
            search_tags.append("subject_and_flux")

        if self.tags_times:
            search_tags.append("times")

        Tags = self.env["project.tags"].sudo()
        Task = self.env["project.task"].sudo()

        items = self._read_items(workbook)

        if "subject_and_flux" in search_tags:
            items = prepare_tags(items, ["Sujet", "Flux"], "value")

        if "times" in search_tags:
            items = prepare_tags(items, TIME_kEYS, "key")

        # Extract and set tags
        names = extract_tags(items)
        if names:
            mapping = Tags.search_or_create(names)
            items = set_tags(items, mapping)

        if self.use_subtasks:
            names = extract(items, "Flux")
            parents = [{"name": name, "flux": "master"} for name in names]
            records = Task.create_from_import(
                parents, self.project_id.id, self.import_filename
            )

            mapping = {item["name"]: item["id"] for item in records.read(["name"])}
            items = set_parents(items, mapping)

        tasks = list(map(Task._prepare_from_gap2, items))

        return tasks
