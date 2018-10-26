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

    frais_id           = fields.Many2one('is.frais', 'Frais', required=True)
    partner_id         = fields.Many2one('res.partner', 'Fournisseur')
    product_id         = fields.Many2one('product.product', 'Type de dépense', required=True)
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


class IsFrais(models.Model):
    _name = 'is.frais'
    _description = "Frais"
    _order = 'chrono desc'


    @api.depends('date_creation','createur_id','chrono')
    def _compute(self):
        for obj in self:
            if obj.date_creation:
                obj.mois_creation  = str(obj.date_creation)[:7]
                obj.annee_creation = str(obj.date_creation)[:4]
            if obj.createur_id and obj.createur_id.is_initiales:
                obj.login=obj.createur_id.is_initiales.upper()
            obj.chrono_long=(obj.login or '')+'-'+(obj.mois_creation or '')+'-'+(obj.chrono or '')


    @api.onchange('forfait_jour_id')
    def onchange_product(self):
        if self.forfait_jour_id:
            self.montant_forfait = self.forfait_jour_id.montant


    chrono           = fields.Char("Chrono", readonly=True, index=True)
    chrono_long      = fields.Char("Chrono long", compute='_compute', readonly=True, store=True)
    createur_id      = fields.Many2one('res.users', "Créateur", required=True, default=lambda self: self.env.user)
    login            = fields.Char("Login" , compute='_compute', readonly=True, store=True)
    date_creation    = fields.Date("Date de création", required=True, index=True, default=fields.Date.today())
    mois_creation    = fields.Char("Mois" , compute='_compute', readonly=True, store=True)
    annee_creation   = fields.Char("Année", compute='_compute', readonly=True, store=True)
    activite_id      = fields.Many2one('is.activite', 'Activite', required=True)
    affaire_id       = fields.Many2one('is.affaire', 'Affaire', related='activite_id.affaire_id', readonly=True)
    type_activite    = fields.Selection([
            ('formation', u'Formation'),
            ('conseil'  , u'Conseil'),
            ('divers'   , u'Divers'),
        ], u"Type d'activité", index=True)
    frais_forfait    = fields.Boolean("Frais au forfait",default=False)
    nb_jours         = fields.Integer("Nb jours (si frais au forfait)")
    forfait_jour_id  = fields.Many2one('is.affaire.forfait.jour', "Forfait jour de l'affaire")
    montant_forfait  = fields.Float("Montant forfait", digits=(14,2))
    parcours         = fields.Text("Parcours")
    dates            = fields.Char("Dates")
    ligne_ids        = fields.One2many('is.frais.lignes', 'frais_id', u'Lignes')
    justificatif_ids = fields.Many2many('ir.attachment', 'is_frais_justificatif_rel', 'doc_id', 'file_id', 'Justificatifs')


    @api.model
    def create(self, vals):
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






