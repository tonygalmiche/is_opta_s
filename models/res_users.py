# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import recurring_ical_events
import urllib.request
import icalendar


#TODO : Mettre l'heure en UTC dans Odoo
#Supprimer ou mettre à jour les lignes => Surement plus rapide de tout supprimer
#Retrouer les bonnes catéroeies et ajouter le temps restant dans une journée



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


    is_initiales          = fields.Char(u'Initiales pour Chrono')
    is_compte_general     = fields.Char(u'Compte général')
    is_google_agenda_ical = fields.Char(u'Adresse privée iCal Google Agenda')
    is_dynacase_ids       = fields.Many2many('is.dynacase', 'res_users_dynacase_rel', 'doc_id', 'dynacase_id', 'Ids Dynacase', readonly=True)
    is_nb_jours           = fields.Integer('Nombre de jours travaillables par an')
    is_salaire_an         = fields.Integer('Salaire brut chargé par an')
    is_salaire_jour       = fields.Float('Salaire journalier', digits=(14,2), compute='_compute_is_salaire_jour', readonly=True, store=True)


    @api.model
    def create(self, vals):
        #TODO : Cela permet de désactiver l'envoi du mail d'invitation lors de la création d'un utilisateur
        user = super(ResUsers, self.with_context(no_reset_password=True)).create(vals)
        return user


    @api.multi
    def actualiser_google_agenda_action(self):
        for obj in self:
            url = obj.is_google_agenda_ical
            if url:
                print(obj,url)
                filename1 = '/tmp/google-agenda-'+str(obj.id)+'.tmp'
                filename2 = '/tmp/google-agenda-'+str(obj.id)+'.ics'
                urllib.request.urlretrieve(url, filename1)
                f1 = open(filename1)
                f2 = open(filename2,'w')
                lines = f1.readlines()
                line2=''
                for line in lines:
                    line2 = line


                    if line[:6] == 'RRULE:':
                        t = line.split(';')
                        line2=[]
                        for x in t:
                            if x[:6] == 'UNTIL=':
                                #print(line.strip(),x.strip())
                                if x.strip()[-1:]!='Z':
                                    x = x.strip()[:14]+'T060000Z\n'
                                    #print('v=',v)
                            line2.append(x)
                        line2=';'.join(line2)
                        print('-',line.strip())
                        print('*',line2.strip())


                    if line[:6] == 'DTEND;':
                        t = line.split(';')
                        line2=[]
                        for x in t:
                            if x[:11] == 'VALUE=DATE:':
                                #print(line.strip(),x.strip())
                                #DTEND;VALUE=DATE:20100207
                                if x.strip()[-1:]!='Z':
                                    x = x.strip()[:19]+'T060000Z\n'
                                    #print('v=',v)
                            line2.append(x)
                        line2=';'.join(line2)


                    #DTSTART;VALUE=DATE:20120119
                    if line[:8] == 'DTSTART;':
                        t = line.split(';')
                        line2=[]
                        for x in t:
                            if x[:11] == 'VALUE=DATE:':
                                #print(line.strip(),x.strip())
                                #DTEND;VALUE=DATE:20100207
                                if x.strip()[-1:]!='Z':
                                    x = x.strip()[:19]+'T060000Z\n'
                                    #print('v=',v)
                            line2.append(x)
                        line2=';'.join(line2)




                    f2.write(line2)
                f1.close()
                f2.close()
                url = 'file://'+filename2
                start_date = (2019, 7, 1)
                end_date =   (2019, 9, 30)
                ical_string = urllib.request.urlopen(url).read()
                calendar = icalendar.Calendar.from_ical(ical_string)
                events = recurring_ical_events.of(calendar).between(start_date, end_date)
                for event in events:
                    start = event["DTSTART"].dt
                    duration = event["DTEND"].dt - event["DTSTART"].dt
                    summary = event["SUMMARY"]
                    #print("start {} duration {}".format(start, duration), summary, event["UID"])

                    vals={
                        'user_id'     : obj.id,
                        'date_debut'  : event["DTSTART"].dt,
                        'date_fin'    : event["DTEND"].dt,
                        #'duree'       : duration,
                        'event_id'    : str(event["UID"]),
                        'intitule'    : str(event["SUMMARY"]),
                        'categorie_id': False,
                    }
                    #print(vals)
                    doc=self.env['is.google.agenda'].create(vals)


#    user_id      = fields.Many2one('res.users', u'Utilisateur')
#    date_debut   = fields.Datetime(u"Date début")
#    date_fin     = fields.Datetime(u"Date fin")
#    duree        = fields.Float(u"Durée")
#    event_id     = fields.Char(u"Id Event Google Agenda")
#    intitule     = fields.Char(u"Intitulé")
#    categorie_id = fields.Many2one('is.google.agenda.categorie', u'Catégorie')











