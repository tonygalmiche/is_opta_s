# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class IsDynacase(models.Model):
    _name = 'is.dynacase'
    _description = "Dynacase (pour import dynacase dans odoo)"
    _order = 'name'

    name  = fields.Char("id Dynacase", required=True, index=True)
    title = fields.Char("title Dynacase")


class ResUsers(models.Model):
    _inherit = 'res.users'


    @api.depends('is_nb_jours','is_salaire_an')
    def _compute_is_salaire_jour(self):
        for obj in self:
            is_salaire_jour = 0
            if obj.is_salaire_an>0 and obj.is_nb_jours>0:
                is_salaire_jour = float(obj.is_salaire_an/obj.is_nb_jours)
            obj.is_salaire_jour=is_salaire_jour
            print(obj,is_salaire_jour)


    is_initiales      = fields.Char('Initiales pour Chrono')
    is_compte_general = fields.Char('Compte général')
    is_dynacase_ids   = fields.Many2many('is.dynacase', 'res_users_dynacase_rel', 'doc_id', 'dynacase_id', 'Ids Dynacase', readonly=True)

    is_nb_jours        = fields.Integer('Nombre de jours travaillables par an')
    is_salaire_an      = fields.Integer('Salaire brut chargé par an')
    is_salaire_jour      = fields.Float('Salaire journalier', digits=(14,2), compute='_compute_is_salaire_jour', readonly=True, store=True)


    @api.model
    def create(self, vals):
        #TODO : Cela permet de désactiver l'envoi du mail d'invitation lors de la création d'un utilisateur
        user = super(ResUsers, self.with_context(no_reset_password=True)).create(vals)
        return user
