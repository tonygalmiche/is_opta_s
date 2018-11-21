# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class IsCompteBanque(models.Model):
    _name = 'is.compte.banque'
    _description = u"Compte Banquaire"
    _order='name'

    company_id  = fields.Many2one('res.company', 'Société', required=True, ondelete='cascade')
    name        = fields.Char("Compte", required=True)
    banque      = fields.Char("Banque")


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_fax               = fields.Char("Fax")
    is_num_formation     = fields.Char("Numéro de déclaration d'activité de formation")
    is_compte_banque_ids = fields.One2many('is.compte.banque', 'company_id', u'Comptes bancaires')
    is_mail_facture      = fields.Char("Mail diffusion facture")
    is_mail_frais        = fields.Char("Mail diffusion frais")

