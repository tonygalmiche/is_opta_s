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

    is_initiales      = fields.Char('Initiales pour Chrono')
    is_compte_general = fields.Char('Compte général')
    is_dynacase_ids   = fields.Many2many('is.dynacase', 'res_users_dynacase_rel', 'doc_id', 'dynacase_id', 'Ids Dynacase', readonly=True)


    @api.model
    def create(self, vals):
        #TODO : Cela permet de désactiver l'envoi du mail d'invitation lors de la création d'un utilisateur
        user = super(ResUsers, self.with_context(no_reset_password=True)).create(vals)
        return user
