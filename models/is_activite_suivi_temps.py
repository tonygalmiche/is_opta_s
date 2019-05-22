# -*- coding: utf-8 -*-

from openerp import tools
from openerp import models,fields,api
from openerp.tools.translate import _


class IsActiviteSuiviTemps(models.Model):
    _description = "Suivi du temps par activité"
    _name = 'is.activite.suivi.temps'
    _order='id desc'
    _auto = False

    affaire_id             = fields.Many2one('is.affaire', 'Affaire')
    partner_id             = fields.Many2one('res.partner', "Client facturable")
    phase_activite_id      = fields.Many2one('is.affaire.phase.activite', 'Sous-phase')
    nature_activite        = fields.Char("Nature de l'activité" )
    dates_intervention     = fields.Char("Dates des jours d'intervention")
    intervenant_product_id = fields.Many2one('product.product', "Intervenant")
    #montant                = fields.Float("Montant unitaire")
    #nb_realise             = fields.Float("Nb unités réalisées")
    #nb_facturable          = fields.Float("Nb unités facturables")
    #total_facturable       = fields.Float("Total facturable")
    invoice_id             = fields.Many2one('account.invoice', "Facture")
    point_cle              = fields.Text("Points clés de l'activité réalisée")
    state                  = fields.Selection([
            ('brouillon', u'Brouillon'),
            ('diffuse'  , u'Diffusé'),
            ('valide'   , u'Validé'),
        ], u"État")

    type_activite        = fields.Selection([
            ('formation'  , u'Formation'),
            ('conseil'    , u'Conseil'),
            ('audit'      , u'Audit'),
            ('back-office', u'Back Office non facturable'),
        ], u"Type d'activité")
    date_activite        = fields.Date("Date intervention")
    mois_activite        = fields.Date("Mois intervention")
    nb_stagiaires        = fields.Integer("Nombre de stagiaires")
    nb_heures            = fields.Float("Nombre d'heures")
    realise_st           = fields.Selection([
            ('oui', u'Oui'),
            ('non', u'Non'),
        ], u"Réalisé en sous-traitance")
    temps_deplacement    = fields.Float("Tps déplacement")
    detail_activite      = fields.Text("Détail des activités réalisées")

    def init(self):
        cr , uid, context = self.env.args
        tools.drop_view_if_exists(cr, 'is_activite_suivi_temps')
        cr.execute("""
            CREATE OR REPLACE view is_activite_suivi_temps AS (
                select
                    ist.id,
                    ia.affaire_id,
                    ia.partner_id,
                    ia.phase_activite_id,
                    ia.nature_activite,
                    ia.dates_intervention,
                    ia.intervenant_product_id,
                    ia.invoice_id,
                    ia.point_cle,
                    ia.state,
                    ist.type_activite,
                    ist.date_activite,
                    to_char(ist.date_activite,'YYYY-MM') mois_activite,
                    ist.nb_stagiaires,
                    ist.nb_heures,
                    ist.realise_st,
                    ist.temps_deplacement,
                    ist.detail_activite
                from is_activite ia inner join is_suivi_temps ist on ia.id=ist.activite_id
            )
        """)

