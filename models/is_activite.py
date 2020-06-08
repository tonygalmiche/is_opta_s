# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class IsActivite(models.Model):
    _name = 'is.activite'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Activité"
    _order = 'date_debut desc'


    @api.depends('tarification_id','nb_facturable')
    def _compute(self):
        for obj in self:
            if obj.tarification_id:
                obj.montant          = obj.tarification_id.montant
                total_facturable     = obj.montant*obj.nb_facturable
                obj.total_facturable = total_facturable
                #for line in obj.suivi_temps_ids:
                #    line.total_facturable_ligne1 = 123
                #    total_facturable = 0


    def _compute_nb_stagiaires(self):
        for obj in self:
            nb=0
            ct=0
            if obj.suivi_temps_ids:
                for line in obj.suivi_temps_ids:
                    if line.nb_stagiaires>0:
                        nb+=line.nb_stagiaires
                        ct+=1
                if ct>0:
                    nb=nb/ct
            obj.nb_stagiaires=nb


    @api.depends('intervenant_id')
    def _compute_product_id(self):
        for obj in self:
            obj.intervenant_product_id=obj.intervenant_id.intervenant_id.id


    @api.depends('affaire_id','affaire_id.responsable_id')
    def _compute_responsable_id(self):
        for obj in self:
            obj.responsable_id = obj.affaire_id.responsable_id.id


    def get_jours_consommes(self,act):
        jours_consommes=0
        unite = act.tarification_id.unite
        if unite=='journee':
            jours_consommes+=act.nb_facturable
        if unite=='demie_journee':
            jours_consommes+=act.nb_facturable/2
        if unite=='heure':
            jours_consommes+=act.nb_facturable/7
        #Pour les participants, il faut compter le nombre de lignes dans le suivi du temps
        if unite=='participant':
            jours_consommes+=len(act.suivi_temps_ids)
        return jours_consommes

    @api.depends('suivi_temps_ids','nb_facturable','tarification_id')
    def _compute_jours_consommes(self):
        for act in self:
            jours_consommes=self.get_jours_consommes(act)
            act.jours_consommes=jours_consommes


    def get_nb_realise_auto(self,act):
        nb_realise_auto=0
        unite = act.tarification_id.unite
        if unite=='journee':
            nb_realise_auto+=act.nb_facturable
        if unite=='demie_journee':
            nb_realise_auto+=act.nb_facturable/2
        if unite=='heure':
            nb_realise_auto+=act.nb_facturable/7
        #Pour les participants, il faut compter le nombre de lignes dans le suivi du temps
        if unite=='participant':
            nb_realise_auto+=len(act.suivi_temps_ids)
        return nb_realise_auto

    @api.depends('suivi_temps_ids','nb_facturable','tarification_id')
    def _compute_nb_realise_auto(self):
        for act in self:
            nb_realise_auto=self.get_nb_realise_auto(act)
            act.nb_realise_auto=nb_realise_auto


    @api.depends('affaire_id','tarification_id')
    def _compute_nb_realise_vsb(self):
        cr,uid,context = self.env.args
        user = self.env['res.users'].browse(uid)
        company  = user.company_id
        for obj in self:
            if company.is_interface=='sgp':
                obj.nb_realise_vsb = False
            else:
                obj.nb_realise_vsb = True


    @api.onchange('affaire_id')
    def onchange_affaire_id(self):
        self.partner_id = self.affaire_id.partner_id.id


    affaire_id             = fields.Many2one('is.affaire', 'Affaire', required=True,index=True)
    responsable_id         = fields.Many2one('res.users', "Responsable de l'affaire", compute='_compute_responsable_id', readonly=True, store=True)
    partner_id             = fields.Many2one('res.partner', "Client facturable", required=True, index=True, domain=[('customer','=',True)])
    phase_activite_id      = fields.Many2one('is.affaire.phase.activite', 'Sous-phase',index=True)
    nature_activite        = fields.Char("Nature de l'activité"     , required=True, index=True)
    date_debut             = fields.Date("Date de début de l'activité", required=True, index=True)
    dates_intervention     = fields.Char("Dates des jours d'intervention")
    intervenant_id         = fields.Many2one('is.affaire.intervenant', "Intervenant Affaire", required=True,index=True)
    intervenant_product_id = fields.Many2one('product.product', "Intervenant", compute='_compute_product_id', readonly=True, store=True)
    tarification_id        = fields.Many2one('is.affaire.taux.journalier', "Tarification")
    montant                = fields.Float("Montant unitaire", compute='_compute', readonly=True, store=True, digits=(14,2))

    nb_realise             = fields.Float("Nb unités réalisées"  , digits=(14,4))
    nb_realise_auto        = fields.Float("Nb unités réalisées (auto)", digits=(14,2), compute='_compute_nb_realise_auto', readonly=True, store=False)
    nb_realise_vsb         = fields.Boolean("Nb unités réalisées visibility", compute='_compute_nb_realise_vsb', readonly=True, store=False)

    nb_facturable          = fields.Float("Nb unités facturables", digits=(14,4))
    jours_consommes        = fields.Float("Nb jours consommés", digits=(14,2), compute='_compute_jours_consommes', readonly=True, store=True)
    total_facturable       = fields.Float("Total facturable", compute='_compute', readonly=True, store=True, digits=(14,2))
    nb_stagiaires          = fields.Float("Nombre de stagiaires calculé", compute='_compute_nb_stagiaires', readonly=True, store=False, digits=(14,1))
    facture_sur_accompte   = fields.Boolean("Facture sur acompte")
    non_facturable         = fields.Boolean("Activité non facturable", default=False, help="Si cette case est cochée, cette activité ne sera pas proposée à la facturation")
    point_cle              = fields.Text("Points clés de l'activité réalisée")
    suivi_temps_ids        = fields.One2many('is.suivi.temps', 'activite_id', u'Suivi du temps')
    frais_ids              = fields.One2many('is.frais', 'activite_id', u'Frais')
    pieces_jointes_ids     = fields.Many2many('ir.attachment', 'is_activite_pieces_jointes_rel', 'doc_id', 'file_id', u'Pièces jointes')
    invoice_id             = fields.Many2one('account.invoice', "Facture",index=True, copy=False)
    state                  = fields.Selection([
            ('brouillon', u'Brouillon'),
            ('diffuse'  , u'Diffusé'),
            ('valide'   , u'Validé'),
        ], u"État", index=True, default='brouillon')
    is_dynacase_ids = fields.Many2many('is.dynacase', 'is_activite_dynacase_rel', 'doc_id', 'dynacase_id', 'Ids Dynacase', readonly=True)
    active          = fields.Boolean("Activité active", default=True)


    @api.multi
    def write(self,vals):
        for obj in self:
            if obj.state=='diffuse' and 'state' not in vals:
                #** Envoi d'un courriel a l'intervenant si modification ********
                if obj.intervenant_id.intervenant_id.is_type_intervenant == 'consultant':
                    subject=u'[Activité] '+obj.nature_activite+u' Modifiée'
                    email_to=obj.intervenant_id.intervenant_id.is_consultant_id.email
                    if not email_to:
                        print(obj.intervenant_id,obj.intervenant_id.intervenant_id,obj.intervenant_id.intervenant_id.is_type_intervenant)
                        raise Warning(u"Mail de l'intervenant non configuré pour ")
                    user  = self.env['res.users'].browse(self._uid)
                    email_from = user.email
                    if not email_from:
                        raise Warning(u"Votre mail n'est pas configuré")
                    nom   = user.name
                    if email_from!=email_to:
                        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        url=base_url+u'/web#id='+str(obj.id)+u'&view_type=form&model='+self._name
                        body_html=u"""
                            <p>Bonjour,</p>
                            <p>Pour information, """+nom+""" vient de modifier votre activité <a href='"""+url+"""'>"""+obj.nature_activite+"""</a>.</p>
                        """
                        self.envoi_mail(email_from,email_to,subject,body_html)
                #***************************************************************

#            total_facturable = obj.total_facturable
#            for line in obj.suivi_temps_ids:
#                print(line,total_facturable)
#                line.total_facturable_ligne1 = total_facturable
#                total_facturable = 0

        res = super(IsActivite, self).write(vals)
        return res


    @api.multi
    def name_get(self):
        result = []
        for obj in self:
            result.append((obj.id, '['+str(obj.affaire_id.name)+'] '+str(obj.nature_activite)))
        return result


    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        ids = []
        if name:
            ids = self._search(['|',('affaire_id.name', 'ilike', name),('nature_activite', 'ilike', name)] + args, limit=limit, access_rights_uid=name_get_uid)
        else:
            ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(ids).name_get()


    @api.multi
    def envoi_mail(self, email_from,email_to,subject,body_html):
        for obj in self:
            vals={
                'email_from'    : email_from, 
                'email_to'      : email_to, 
                #'email_cc'      : email_from,
                'subject'       : subject,
                'body'          : body_html, 
                'body_html'     : body_html, 
                'model'         : self._name,
                'res_id'        : obj.id,
                'notification'  : True,
                'message_type'  : 'comment',
            }
            email=self.env['mail.mail'].create(vals)
            if email:
                self.env['mail.mail'].send(email)


    @api.multi
    def vers_diffuse(self, vals):
        for obj in self:
            subject=u'[Activité] '+obj.nature_activite+u' Diffusé'
            email_to=obj.affaire_id.responsable_id.email
            if not email_to:
                raise Warning(u"Mail du responsable de l'affaire non configuré")
            user  = self.env['res.users'].browse(self._uid)
            email_from = user.email
            if not email_from:
                raise Warning(u"Votre mail n'est pas configuré")
            nom   = user.name
            if email_from!=email_to:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                url=base_url+u'/web#id='+str(obj.id)+u'&view_type=form&model='+self._name
                body_html=u"""
                    <p>Bonjour,</p>
                    <p>"""+nom+""" vient de passer l'activité <a href='"""+url+"""'>"""+obj.nature_activite+"""</a> à l'état 'Diffusé'.</p>
                    <p>Merci d'en prendre connaissance.</p>
                """
                self.envoi_mail(email_from,email_to,subject,body_html)
            obj.state='diffuse'


    @api.multi
    def vers_valide(self, vals):
        for obj in self:
            obj.state='valide'


    @api.multi
    def vers_brouillon(self, vals):
        for obj in self:
            obj.sudo().state='brouillon'

    @api.multi
    def acceder_activite_action(self, vals):
        for obj in self:
            res= {
                'name': 'Activité',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'is.activite',
                'res_id': obj.id,
                'type': 'ir.actions.act_window',
            }
            return res






    @api.multi
    def creation_frais(self, vals):
        for obj in self:
            res= {
                'name': 'Frais',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'is.frais',
                'type': 'ir.actions.act_window',
                'context': {
                    'default_affaire_id' : obj.affaire_id.id,
                    'default_activite_id': obj.id,
                }
            }
            return res



