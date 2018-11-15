# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class IsSuiviTemps(models.Model):
    _name = 'is.suivi.temps'
    _description = "Suivi du temps"
    _order = 'date_activite desc'


    @api.depends('aller_heure_depart','aller_heure_arrivee','retour_heure_depart','retour_heure_arrivee')
    def _compute(self):
        for obj in self:
            tps=obj.aller_heure_arrivee-obj.aller_heure_depart+obj.retour_heure_arrivee-obj.retour_heure_depart
            obj.temps_deplacement=tps


    @api.depends('activite_id')
    def _compute_affaire_id(self):
        for obj in self:
            obj.affaire_id=obj.activite_id.affaire_id.id


    activite_id          = fields.Many2one('is.activite', 'Activité', required=True)
    affaire_id           = fields.Many2one('is.affaire', compute='_compute_affaire_id', readonly=True, store=True)
    type_activite        = fields.Selection([
            ('formation'  , u'Formation'),
            ('conseil'    , u'Conseil'),
            ('audit'      , u'Audit'),
            ('back-office', u'Back Office non facturable'),
        ], u"Type d'activité", required=True)
    date_activite        = fields.Date("Date", index=True, required=True) # default=lambda self: self._get_date_activite()
    nb_stagiaires        = fields.Integer("Nombre de stagiaires")
    nb_heures            = fields.Float("Nombre d'heures par jour", required=True)
    realise_st           = fields.Selection([
            ('oui', u'Oui'),
            ('non', u'Non'),
        ], u"Réalisé en sous-traitance",default='non')
    aller_heure_depart   = fields.Float("Aller - Heure de départ")
    aller_heure_arrivee  = fields.Float("Aller - Heure d'arrivée")
    retour_heure_depart  = fields.Float("Retour - Heure de départ")
    retour_heure_arrivee = fields.Float("Retour - Heure d'arrivée")
    temps_deplacement    = fields.Float("Temps de déplacement", compute='_compute', readonly=True, store=True)
    detail_activite      = fields.Text("Détail des activités réalisées")


    @api.multi
    def name_get(self):
        result = []
        for obj in self:
            result.append((obj.id, '['+str(obj.date_activite)+'] '+str(obj.activite_id.nature_activite)))
        return result


    @api.multi
    def copie_suivi_temps_action(self, vals):
        for obj in self:
            obj.copy()



    @api.multi
    def acceder_suivi_temps_action(self):
        for obj in self:
            res= {
                'name': 'Suivi du temps',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'is.suivi.temps',
                'res_id': obj.id,
                'type': 'ir.actions.act_window',
            }
            return res







