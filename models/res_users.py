# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import recurring_ical_events
import urllib.request
import icalendar
from datetime import datetime,timedelta,date
import logging
_logger = logging.getLogger(__name__)


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


    is_initiales          = fields.Char(u'Initiales pour Chrono')
    is_compte_general     = fields.Char(u'Compte général')
    is_google_agenda_ical = fields.Text(u'Adresse privée iCal Google Agenda')
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
        cr = self._cr
        _logger.info(u"Début du traitement actualiser_google_agenda_action")
        categories = self.env['is.google.agenda.categorie'].search([])
        now = date.today()
        start_date = now - timedelta(days=31) # 1 mois avant
        end_date   = now + timedelta(days=92) # 3 mois après
        for obj in self:
            filtre=[
                ('date_debut','>=',start_date),
                ('date_fin','<=',end_date),
                ('user_id','=',obj.id),
            ]
            self.env['is.google.agenda'].search(filtre).unlink()
            url = obj.is_google_agenda_ical
            if url:
                urls=url.split('\n')
                for url in urls:
                    _logger.info(obj.name+u' / '+url)

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
                                    if x.strip()[-1:]!='Z':
                                        x = x.strip()[:14]+'T060000Z\n'
                                line2.append(x)
                            line2=';'.join(line2)
                        if line[:6] == 'DTEND;':
                            t = line.split(';')
                            line2=[]
                            for x in t:
                                if x[:11] == 'VALUE=DATE:':
                                    if x.strip()[-1:]!='Z':
                                        x = x.strip()[:19]+'T060000Z\n'
                                line2.append(x)
                            line2=';'.join(line2)
                        if line[:8] == 'DTSTART;':
                            t = line.split(';')
                            line2=[]
                            for x in t:
                                if x[:11] == 'VALUE=DATE:':
                                    if x.strip()[-1:]!='Z':
                                        x = x.strip()[:19]+'T060000Z\n'
                                line2.append(x)
                            line2=';'.join(line2)
                        f2.write(line2)
                    f1.close()
                    f2.close()
                    url = 'file://'+filename2
                    ical_string = urllib.request.urlopen(url).read()
                    calendar = icalendar.Calendar.from_ical(ical_string)
                    events = recurring_ical_events.of(calendar).between(start_date, end_date)
                    for event in events:
                        start = event["DTSTART"].dt
                        duration = event["DTEND"].dt - event["DTSTART"].dt
                        summary = event["SUMMARY"]
                        date_debut = event["DTSTART"].dt
                        date_fin   =  event["DTEND"].dt
                        offset = -int(int(date_debut.strftime('%z'))/100)
                        date_debut_offset = date_debut + timedelta(hours=offset)
                        date_fin_offset   = date_fin   + timedelta(hours=offset)
                        duree = date_fin - date_debut
                        duree = duree.total_seconds()/3600
                        intitule = str(event["SUMMARY"])
                        categorie_id = False
                        for categorie in categories:
                            lg = len(categorie.name)
                            if intitule[:lg] == categorie.name:
                                categorie_id = categorie.id
                        if not categorie_id:
                            intitule=False
                        vals={
                            'user_id'         : obj.id,
                            'date_debut'      : date_debut_offset,
                            'date_fin'        : date_fin_offset,
                            'duree'           : duree,
                            'temps_disponible': False,
                            'event_id'        : str(event["UID"]),
                            'intitule'        : intitule,
                            'categorie_id'    : categorie_id,
                        }
                        doc=self.env['is.google.agenda'].create(vals)
        for obj in self:
            date_debut = start_date
            for i in range(1,125):
                if int(date_debut.strftime('%w'))!=0 and int(date_debut.strftime('%w'))!=6:
                    SQL="""
                        select to_char(date_debut,'YYYY-MM-DD'),sum(duree)
                        from is_google_agenda
                        where 
                            user_id="""+str(obj.id)+""" and
                            date_debut>='"""+str(date_debut)+""" 00:00:00' and
                            date_debut<='"""+str(date_debut)+""" 23:59:59'
                        group by to_char(date_debut,'YYYY-MM-DD')
                        order by to_char(date_debut,'YYYY-MM-DD')
                    """
                    cr.execute(SQL)
                    result = cr.fetchall()
                    temps_libre = 7
                    for row in result:
                        temps_libre = 7 - row[1]
                        if temps_libre<0:
                            temps_libre=0
                    vals={
                        'user_id'         : obj.id,
                        'date_debut'      : str(date_debut)+' 12:00:00',
                        'date_fin'        : str(date_debut)+' 12:00:00',
                        'duree'           : temps_libre,
                        'temps_disponible': True,
                        'event_id'        : False,
                        'intitule'        : 'Temps Disponible',
                        'categorie_id'    : False,
                    }
                    doc=self.env['is.google.agenda'].create(vals)
                date_debut = date_debut + timedelta(days=1)
        _logger.info(u"Fin du traitement actualiser_google_agenda_action")

