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
    is_siege_sociale     = fields.Char("Siège sociale")
    is_num_formation     = fields.Char("Numéro de déclaration d'activité de formation")
    is_compte_banque_ids = fields.One2many('is.compte.banque', 'company_id', u'Comptes bancaires')
    is_mail_facture      = fields.Char("Mail diffusion facture")
    is_mail_frais        = fields.Char("Mail diffusion frais")
    is_journal_achat     = fields.Char("Journal des achats", default='ACB')
    is_journal_vente     = fields.Char("Journal des ventes", default='VEB')
    is_interface         = fields.Selection([
            ('opta-s', u'Opta-S'),
            ('sgp'   , u'SGP'),
        ], u"Interface", default='opta-s', help=u"Utilisé en particulier pour la gestion du champ 'Nb unités réalisées' des activités")

