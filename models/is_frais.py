# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class IsDepenseEffectueePar(models.Model):
    _name = 'is.depense.effectuee.par'
    _description = "Dépense effectuée par"
    _order = 'name'

    name = fields.Char("Dépense effectuée par", required=True, index=True)


class IsFraisLigne(models.Model):
    _name = 'is.frais.lignes'
    _description = "Frais"
    _order = 'id'

    frais_id           = fields.Many2one('is.frais', 'Frais', required=True, ondelete='cascade')
    partner_id         = fields.Many2one('res.partner', 'Fournisseur', domain=[('supplier','=',True),('is_company','=',True)])
    product_id         = fields.Many2one('product.product', 'Type de dépense', required=True, domain=[('is_type_intervenant','=',False)])
    effectuee_par_id   = fields.Many2one('is.depense.effectuee.par', 'Dépense effectuée par', required=True)
    montant_ttc        = fields.Float("Montant", digits=(14,2))
    montant_tva        = fields.Float("Montant TVA récupérable", digits=(14,2))
    refacturable       = fields.Selection([
            ('oui', u'Oui'),
            ('non', u'Non'),
        ], u"Refacturable", index=True, default='non')
    commentaire        = fields.Text("Commentaire")
    justificatif_joint = fields.Selection([
            ('oui', u'Oui'),
            ('non', u'Non'),
        ], u"Justificatif joint", index=True, default='oui')


    @api.multi
    def copie_frais_action(self, vals):
        for obj in self:
            obj.copy()


class IsFrais(models.Model):
    _name = 'is.frais'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Frais"
    _order = 'chrono desc'


    @api.depends('date_creation','createur_id','chrono')
    def compute_chrono(self):
        for obj in self:
            if obj.date_creation:
                obj.mois_creation  = str(obj.date_creation)[:7]
                obj.annee_creation = str(obj.date_creation)[:4]
            if obj.createur_id and obj.createur_id.is_initiales:
                obj.login=obj.createur_id.is_initiales.upper()
            obj.chrono_long=(obj.login or '')+'-'+(obj.mois_creation or '')+'-'+(obj.chrono or '')


    @api.depends('ligne_ids','nb_jours','montant_forfait')
    def _compute_total(self):
        for obj in self:
            total_consultant      = 0
            total_refacturable    = obj.nb_jours*obj.montant_forfait
            total_frais           = 0
            total_tva_recuperable = 0
            for l in obj.ligne_ids:
                if l.effectuee_par_id.name=='CONSULTANT':
                    total_consultant      += l.montant_ttc
                if l.refacturable=='oui':
                    total_refacturable    += l.montant_ttc
                total_frais           += l.montant_ttc
                total_tva_recuperable += l.montant_tva
            obj.total_consultant      = total_consultant
            obj.total_refacturable    = total_refacturable
            obj.total_frais           = total_frais
            obj.total_tva_recuperable = total_tva_recuperable


    @api.onchange('forfait_jour_id')
    def onchange_product(self):
        if self.forfait_jour_id:
            self.montant_forfait = self.forfait_jour_id.montant


    chrono           = fields.Char("Chrono", readonly=True, index=True)
    chrono_long      = fields.Char("Chrono long", compute='compute_chrono', readonly=True, store=True)
    createur_id      = fields.Many2one('res.users', "Créateur", required=True, default=lambda self: self.env.user)
    login            = fields.Char("Login" , compute='compute_chrono', readonly=True, store=True)
    date_creation    = fields.Date("Date de création", required=True, index=True, default=fields.Date.today())
    mois_creation    = fields.Char("Mois" , compute='compute_chrono', readonly=True, store=True)
    annee_creation   = fields.Char("Année", compute='compute_chrono', readonly=True, store=True)
    affaire_id       = fields.Many2one('is.affaire' , 'Affaire' , required=False)
    activite_id      = fields.Many2one('is.activite', 'Activite', required=True)
    type_activite    = fields.Selection([
            ('formation', u'Formation'),
            ('conseil'  , u'Conseil'),
            ('divers'   , u'Divers'),
        ], u"Type d'activité", index=True, required=True)
    frais_forfait    = fields.Boolean("Frais au forfait",default=False)
    nb_jours         = fields.Float("Nb jours (si frais au forfait)", digits=(14,2))
    forfait_jour_id  = fields.Many2one('is.affaire.forfait.jour', "Forfait jour de l'affaire")
    montant_forfait  = fields.Float("Montant forfait", digits=(14,2))
    parcours         = fields.Text("Parcours")
    dates            = fields.Char("Dates")
    ligne_ids        = fields.One2many('is.frais.lignes', 'frais_id', u'Lignes')
    justificatif_ids = fields.Many2many('ir.attachment', 'is_frais_justificatif_rel', 'doc_id', 'file_id', 'Justificatifs')
    total_consultant      = fields.Float("Total TTC Consultant à rembourser", digits=(14,2), compute='_compute_total', readonly=True, store=True)
    total_refacturable    = fields.Float("Total TTC refacturable"           , digits=(14,2), compute='_compute_total', readonly=True, store=True)
    total_frais           = fields.Float("Total TTC de tous les frais"      , digits=(14,2), compute='_compute_total', readonly=True, store=True)
    total_tva_recuperable = fields.Float("Total TVA récupérable"            , digits=(14,2), compute='_compute_total', readonly=True, store=True)
    state = fields.Selection([
            ('brouillon', u'Brouillon'),
            ('diffuse'  , u'Diffusé'),
            ('valide'   , u'Validé'),
        ], u"État", index=True, default='brouillon')
    is_dynacase_ids = fields.Many2many('is.dynacase', 'is_frais_dynacase_rel', 'doc_id', 'dynacase_id', 'Ids Dynacase', readonly=True)

    @api.model
    def create(self, vals):
        if 'activite_id' in vals:
            activite_id=vals['activite_id']
            affaire_id=self.env['is.activite'].browse(activite_id).affaire_id.id
            vals['affaire_id']=affaire_id
        vals['chrono'] = self.env['ir.sequence'].next_by_code('is.frais')
        res = super(IsFrais, self).create(vals)
        return res


    @api.multi
    def name_get(self):
        result = []
        for obj in self:
            result.append((obj.id, str(obj.login)+'-'+str(obj.mois_creation)+'-'+str(obj.chrono)))
        return result


    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        ids = []
        if name:
            ids = self._search(['|','|',('login', 'ilike', name),('mois_creation', 'ilike', name),('chrono', 'ilike', name)] + args, limit=limit, access_rights_uid=name_get_uid)
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
            subject=u'[Frais]['+obj.chrono_long+u'] '+obj.activite_id.nature_activite+u' Diffusé'
            user  = self.env.user
            email_to = user.company_id.is_mail_frais
            if not email_to:
                raise Warning(u"Mail diffusion frais de la société non configuré")
            email_from = user.email
            if not email_from:
                raise Warning(u"Votre mail n'est pas configuré")
            nom   = user.name
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url=base_url+u'/web#id='+str(obj.id)+u'&view_type=form&model='+self._name
            body_html=u"""
                <p>Bonjour,</p>
                <p>"""+nom+""" vient de passer la fiche de frais <a href='"""+url+"""'>"""+obj.activite_id.nature_activite+"""</a> à l'état 'Diffusé'.</p>
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
            obj.state='brouillon'


    @api.multi
    def acceder_frais_action(self, vals):
        for obj in self:
            res= {
                'name': 'Frais',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'is.frais',
                'res_id': obj.id,
                'type': 'ir.actions.act_window',
            }
            return res

