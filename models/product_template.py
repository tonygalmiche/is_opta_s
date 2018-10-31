# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = "product.template"


    is_type_intervenant = fields.Selection([
            ('consultant'   , 'Consultant'),
            ('co-traitant'  , 'Co-traitant'),
            ('sous-traitant', 'Sous-Traitant'),
        ], u"Type d'intervenant",)
    is_consultant_id = fields.Many2one('res.users', "Consultant associé")
