# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class IsGoogleAgendaCategorie(models.Model):
    _name='is.google.agenda.categorie'
    _description = "Catégorie Google Agenda"
    _order='name'

    name = fields.Char(u"Catégorie Google Agenda",required=1)


class IsGoogleAgenda(models.Model):
    _name='is.google.agenda'
    _description = "Evénements Google Agenda "
    _order='date_debut desc'

    user_id          = fields.Many2one('res.users', u'Utilisateur',index=1)
    date_debut       = fields.Datetime(u"Date début",index=1)
    date_fin         = fields.Datetime(u"Date fin",index=1)
    duree            = fields.Float(u"Durée")
    temps_disponible = fields.Boolean(u"Temps disponible",index=1,default=False)
    event_id         = fields.Char(u"Id Event Google Agenda",index=1)
    intitule         = fields.Char(u"Intitulé",index=1)
    categorie_id     = fields.Many2one('is.google.agenda.categorie', u'Catégorie',index=1)




    @api.model
    def actualiser_action(self, *args, **kwargs):
        if not self.env.user._is_admin():
            raise AccessDenied()

        print('#### actualiser_action')
        self.env['res.users'].search([]).actualiser_google_agenda_action()

        #self.env['ir.attachment']._file_gc()
        #self._gc_transient_models()
        #self._gc_user_logs()
        return True

