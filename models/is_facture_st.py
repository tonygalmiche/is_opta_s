# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class IsFactureST(models.Model):
    _name = 'is.facture.st'
    _description = "Facture ST"
    _order = 'id'


    @api.depends('date_facture')
    def _compute(self):
        for obj in self:
            if obj.date_facture:
                obj.annee_facture = str(obj.date_facture)[:4]
                obj.mois_facture  = str(obj.date_facture)[5:7]


    name              = fields.Char("N°facture ST", required=True)
    sous_traitant_id  = fields.Many2one('res.partner', 'Sous-traitant', required=True)
    date_facture      = fields.Date("Date de la facture", required=True)
    mois_facture      = fields.Char("Mois" , compute='_compute', readonly=True, store=True)
    annee_facture     = fields.Char("Année", compute='_compute', readonly=True, store=True)
    description       = fields.Text("Description de la prestation", required=True)
    montant_ht        = fields.Float("Montant HT", digits=(14,2), required=True)
    frais             = fields.Float("Frais", digits=(14,2))
    client_id         = fields.Many2one('res.partner', "Client"  , required=True, index=True, domain=[('customer','=',True),('is_company','=',True)])
    affaire_id        = fields.Many2one('is.affaire', 'Affaire'  , required=True)
    activite_id       = fields.Many2one('is.activite', 'Activité', required=True)


