# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class IsTypeSociete(models.Model):
    _name = 'is.type.societe'
    _description = "Type de société"
    _order = 'name'

    name = fields.Char("Type de société", required=True, index=True)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_type_societe_id  = fields.Many2one('is.type.societe', 'Type de société')


