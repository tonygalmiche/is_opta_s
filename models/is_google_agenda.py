# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class IsGoogleAgendaCategorie(models.Model):
    _name='is.google.agenda.categorie'
    _description = "Catégorie Google Agenda"
    _order='name'

    name = fields.Char(u"Catégorie Google Agenda")


class IsGoogleAgenda(models.Model):
    _name='is.google.agenda'
    _description = "Evénements Google Agenda "
    _order='date_debut desc'

    user_id      = fields.Many2one('res.users', u'Utilisateur')
    date_debut   = fields.Datetime(u"Date début")
    date_fin     = fields.Datetime(u"Date fin")
    duree        = fields.Float(u"Durée")
    event_id     = fields.Char(u"Id Event Google Agenda")
    intitule     = fields.Char(u"Intitulé")
    categorie_id = fields.Many2one('is.google.agenda.categorie', u'Catégorie')


