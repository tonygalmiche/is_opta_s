# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class IsDepenseEffectueePar(models.Model):
    _name = 'is.depense.effectuee.par'
    _description = "Dépense effectuée par"
    _order = 'name'

    name = fields.Char("Dépense effectuée par", required=True, index=True)


class IsFraisLigne(models.Model):
    _name = 'is.frais.lignes'
    _description = "Frais"
    _order = 'id'

    frais_id           = fields.Many2one('is.frais', 'Frais', required=True)
    partner_id         = fields.Many2one('res.partner', 'Fournisseur', required=True)
    product_id         = fields.Many2one('product.product', 'Type de dépense', required=True)
    effectuee_par_id   = fields.Many2one('is.depense.effectuee.par', 'Dépense effectuée par', required=True)
    montant_ttc        = fields.Float("Montant", digits=(14,2))
    montant_tva        = fields.Float("Montant TVA récupérable", digits=(14,2))
    refacturable       = fields.Selection([
            ('oui', u'Oui'),
            ('non', u'Non'),
        ], u"Refacturable", index=True, default='non')
    commentaire        = fields.Text("Commentaire")
    justificatif_joint = fields.Selection([
            ('oui', u'Oui'),
            ('non', u'Non'),
        ], u"Justificatif joint", index=True, default='oui')


class IsFrais(models.Model):
    _name = 'is.frais'
    _description = "Frais"
    _order = 'chrono desc'

    chrono           = fields.Char("Chrono", readonly=True, index=True)
    activite_id      = fields.Many2one('is.activite', 'Activite', required=True)
    affaire_id       = fields.Many2one('is.affaire', 'Affaire', related='activite_id.affaire_id', readonly=True)
    type_activite    = fields.Selection([
            ('formation', u'Formation'),
            ('conseil'  , u'Conseil'),
            ('divers'   , u'Divers'),
        ], u"Type d'activité", index=True)
    frais_forfait    = fields.Boolean("Frais au forfait",default=False)
    nb_jours         = fields.Integer("Nb jours (si frais au forfait)")
    forfait_jour_id  = fields.Many2one('is.affaire.forfait.jour', "Forfait jour de l'affaire")
    commentaire      = fields.Text("Commentaire frais au forfait", readonly=True)
    parcours         = fields.Text("Parcours")
    dates            = fields.Char("Dates")
    ligne_ids        = fields.One2many('is.frais.lignes', 'frais_id', u'Lignes')
    justificatif_ids = fields.Many2many('ir.attachment', 'is_frais_justificatif_rel', 'doc_id', 'file_id', 'Justificatifs')

    @api.model
    def create(self, vals):
        vals['chrono'] = self.env['ir.sequence'].next_by_code('is.frais')
        res = super(IsFrais, self).create(vals)
        return res

