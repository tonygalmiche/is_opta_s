# -*- coding: utf-8 -*-

from openerp import tools
from openerp import models,fields,api
from openerp.tools.translate import _


class IsAffaireActivite(models.Model):
    _description = "Suivi activités par affaire"
    _name = 'is.affaire.activite'
    _order='id desc'
    _auto = False

    code_long              = fields.Char("Code affaire")
    nature_affaire         = fields.Char("Nature de l'affaire")
    type_intervention_id   = fields.Many2one('is.type.intervention', "Type d'intervention")
    secteur_id             = fields.Many2one('is.secteur', "Secteur")
    type_offre_id          = fields.Many2one('is.type.offre', "Type d'offre")
    annee_creation         = fields.Char("Année Création affaire")
    fiscal_position_id     = fields.Many2one('account.fiscal.position', "Position fiscale")
    responsable_id         = fields.Many2one('res.users', "Responsable de l'affaire")
    affaire_id             = fields.Many2one('is.affaire', 'Affaire')
    activite_id            = fields.Many2one('is.activite', 'Activité')
    partner_id             = fields.Many2one('res.partner', "Client facturable")
    nature_activite        = fields.Char("Nature de l'activité")
    date_debut             = fields.Date("Date de début de l'activité")
    annee_activite         = fields.Char("Année activité")
    annee_mois_activite    = fields.Char("Année-Mois activité")
    mois_activite          = fields.Char("Mois activité")
    intervenant_product_id = fields.Many2one('product.product', "Intervenant")
    montant                = fields.Float(u"Montant unitaire")
    nb_realise             = fields.Float(u"Nb unités réalisées")
    nb_facturable          = fields.Float(u"Nb unités facturables")
    jours_consommes        = fields.Float(u"Nb jours consommés")
    jours_realises         = fields.Float(u"Nb jours réalisés")
    total_facturable       = fields.Float(u"Total facturable")
    invoice_id             = fields.Many2one('account.invoice', "Facture")
    state                  = fields.Selection([
            ('brouillon', u'Brouillon'),
            ('diffuse'  , u'Diffusé'),
            ('valide'   , u'Validé'),
        ], u"État activité")





    def init(self):
        cr , uid, context = self.env.args
        tools.drop_view_if_exists(cr, 'is_affaire_activite')
        cr.execute("""
            CREATE OR REPLACE view is_affaire_activite AS (
                select 
                    act.id,
                    aff.code_long,
                    aff.nature_affaire,
                    aff.type_intervention_id,
                    aff.secteur_id,
                    aff.type_offre_id,
                    aff.annee_creation,
                    aff.fiscal_position_id,
                    aff.responsable_id,
                    act.affaire_id,
                    act.id activite_id,
                    act.partner_id,
                    act.nature_activite,
                    act.date_debut,
                    to_char(act.date_debut,'YYYY')    annee_activite,
                    to_char(act.date_debut,'YYYY-MM') annee_mois_activite,
                    to_char(act.date_debut,'MM')      mois_activite,
                    act.intervenant_product_id,
                    act.montant,
                    act.nb_realise,
                    act.nb_facturable,
                    act.jours_consommes,
                    act.jours_realises,
                    act.total_facturable,
                    act.invoice_id,
                    act.state
                from is_activite act inner join is_affaire aff on act.affaire_id=aff.id
                where act.active='t' 
            )
        """)

