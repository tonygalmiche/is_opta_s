# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import datetime



class IsSuiviTempsSimplifieWizard(models.TransientModel):
    _name = 'is.suivi.temps.simplifie.wizard'
    _description = u'Interface pour la saisie simplifiée du temps'


    @api.multi
    def _get_date_lundi(self):
        date = datetime.date.today()
        jour = date.weekday()
        date = date - datetime.timedelta(days=jour) 
        return date
 

    intervenant_id = fields.Many2one('res.users', "Intervenant", required=True, default=lambda self: self.env.user)
    date_semaine   = fields.Date("Lundi de la semaine à saisir" , required=True, default=lambda self: self._get_date_lundi())


    @api.multi
    def interface_simplifiee(self):
        for obj in self:
            date_semaine = obj.date_semaine
            jour = date_semaine.weekday()
            date_semaine = date_semaine - datetime.timedelta(days=jour) 
            affaires = self.env['is.affaire'].search([('state', '=', 'affaire_gagnee')])
            ids=[]
            for affaire in affaires:
                intervenants = affaire.intervenant_ids
                for intervenant in intervenants:
                    if obj.intervenant_id == intervenant.intervenant_id.is_consultant_id:
                        activites = self.env['is.activite'].search([('affaire_id', '=', affaire.id),('state','=','brouillon')])
                        for activite in activites:
                            if activite.intervenant_id == intervenant:
                                suivis = self.env['is.suivi.temps'].search([('activite_id', '=', activite.id),('date_activite','=',date_semaine)])
                                suivi = False
                                for s in suivis:
                                    suivi = s
                                if not suivi:
                                    vals={
                                        'activite_id'  : activite.id,
                                        'affaire_id'   : affaire.id,
                                        'type_activite': 'formation',
                                        'date_activite': date_semaine,
                                    }
                                    suivi = self.env['is.suivi.temps'].create(vals)
                                ids.append(suivi.id)
            if ids:
                return {
                    'name': u'Suivi du temps '+obj.intervenant_id.name,
                    'view_mode': 'tree',
                    'view_type': 'form',
                    'res_model': 'is.suivi.temps',
                    'type': 'ir.actions.act_window',
                    'view_id': self.env.ref('is_opta_s.is_suivi_temps_simplifie_tree').id,
                    'domain': [
                        ('id','in',ids),
                    ],
                    'limit': 1000,
                }


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


    @api.depends('activite_id')
    def _compute_intervenant_id(self):
        for obj in self:
            obj.intervenant_product_id=obj.activite_id.intervenant_product_id.id

    @api.depends('nb_stagiaires','nb_heures')
    def _compute_total_heures(self):
        for obj in self:
            obj.total_heures = obj.nb_stagiaires * obj.nb_heures


    @api.depends('activite_id','activite_id.total_facturable')
    def _compute_total_facturable(self):
        for obj in self:
            obj.total_facturable = obj.activite_id.total_facturable


    activite_id            = fields.Many2one('is.activite', 'Activité', required=True)
    #intervenant_id         = fields.Many2one('is.affaire.intervenant', "Intervenant Affaire", compute='_compute_intervenant_id', readonly=True, store=True)
    intervenant_product_id = fields.Many2one('product.product', "Intervenant", compute='_compute_intervenant_id', readonly=True, store=True)

    affaire_id           = fields.Many2one('is.affaire', "Affaire", compute='_compute_affaire_id', readonly=True, store=True)
    type_activite        = fields.Selection([
            ('formation'  , u'Formation'),
            ('conseil'    , u'Conseil'),
            ('audit'      , u'Audit'),
            ('back-office', u'Back Office non facturable'),
        ], u"Type d'activité", required=True)
    date_activite        = fields.Date("Date", index=True, required=True) # default=lambda self: self._get_date_activite()
    nb_stagiaires        = fields.Integer("Nombre de stagiaires")
    nb_heures            = fields.Float("Nombre d'heures par jour", required=False)
    total_heures         = fields.Float("Total des heures", compute='_compute_total_heures'    , readonly=True, store=True)
    total_facturable     = fields.Float("Total facturable", compute='_compute_total_facturable', readonly=True, store=True, digits=(14,2))
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







