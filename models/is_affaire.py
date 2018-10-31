# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class IsTypeIntervention(models.Model):
    _name = 'is.type.intervention'
    _description = "Type d'intervention"
    _order = 'name'

    name = fields.Char("Type d'intervention", required=True, index=True)


class IsSecteur(models.Model):
    _name = 'is.secteur'
    _description = "Secteur"
    _order = 'name'

    name = fields.Char("Secteur", required=True, index=True)


class IsTypeOffre(models.Model):
    _name = 'is.type.offre'
    _description = "Type d'offre"
    _order = 'name'

    name = fields.Char("Type d'offre", required=True, index=True)


class IsCause(models.Model):
    _name = 'is.cause'
    _description = "Cause"
    _order = 'name'

    name = fields.Char("Cause", required=True, index=True)


class IsAffaireVenduePar(models.Model):
    _name = 'is.affaire.vendue.par'
    _description = u"Affaire vendue par"
    _order='user_id'

    affaire_id  = fields.Many2one('is.affaire', 'Affaire vendu par', required=True, ondelete='cascade')
    user_id     = fields.Many2one('res.users', "Affaire vendue par")
    repartition = fields.Integer("% répartition CA vendu")
    commentaire = fields.Char("Commentaire")
 


class IsAffaireTauxJournalier(models.Model):
    _name = 'is.affaire.taux.journalier'
    _description = u"Affaire Taux Journalier"

    affaire_id  = fields.Many2one('is.affaire', 'Affaire', required=True, ondelete='cascade')
    unite       = fields.Selection([
            ('heure'        , 'Heure'),
            ('demie_journee', '1/2 journée'),
            ('journee'      , 'Journée'),
            ('forfait'      , 'Forfait')
        ], u"Unité",)
    montant = fields.Float("Montant intervention", digits=(14,2))
    commentaire = fields.Char("Commentaire")


    @api.multi
    def name_get(self):
        result = []
        for obj in self:
            x=str(obj.montant) + '€ / ' + str(obj.unite)
            if obj.commentaire:
                x+=' - ' + str(obj.commentaire)
        result.append((obj.id, x))
        return result


    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        ids = []
        if name:
            ids = self._search([('commentaire', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid)
        else:
            ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(ids).name_get()


class IsAffaireForfaitJour(models.Model):
    _name = 'is.affaire.forfait.jour'
    _description = u"Affaire Forfait frais jour"

    affaire_id  = fields.Many2one('is.affaire', 'Affaire', required=True, ondelete='cascade')
    montant     = fields.Integer("Forfait frais jour")
    nb_jours    = fields.Integer("Nombre de jours (si forfait jour)")
    commentaire = fields.Char("Commentaire")


    @api.multi
    def name_get(self):
        result = []
        for obj in self:
            txt=str(obj.montant)+'€'
            if obj.commentaire:
                txt=txt+' - '+obj.commentaire
            result.append((obj.id, txt))
        return result


    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(ids).name_get()


#class IsAffairePartenaire(models.Model):
#    _name = 'is.affaire.partenaire'
#    _description = u"Partenaires liés à l'affaire"

#    affaire_id  = fields.Many2one('is.affaire', 'Affaire', required=True, ondelete='cascade')
#    type_partenaire = fields.Selection([
#            ('co-traitant'  , 'Co-traitant'),
#            ('sous-traitant', 'Sous-Traitant'),
#        ], "Type de partenaire",)
#    partenaire_id = fields.Many2one('res.partner', "Partenaire", domain=[('supplier','=',True)])
#    commentaire   = fields.Char("Commentaire")


class IsAffaireIntervenant(models.Model):
    _name = 'is.affaire.intervenant'
    _description = u"Intervenants liés à l'affaire"


    @api.depends('intervenant_id')
    def _compute(self):
        for obj in self:
            obj.type_intervenant=obj.intervenant_id.is_type_intervenant


    affaire_id  = fields.Many2one('is.affaire', 'Affaire', required=True, ondelete='cascade')
    intervenant_id = fields.Many2one('product.product', "Intervenant", domain=[('is_type_intervenant','!=',False)], required=True)
    type_intervenant = fields.Selection([
            ('consultant'   , 'Consultant'),
            ('co-traitant'  , 'Co-traitant'),
            ('sous-traitant', 'Sous-Traitant'),
        ], "Type d'intervenant", compute='_compute', readonly=True, store=True)
    commentaire   = fields.Char("Commentaire")


    @api.multi
    def name_get(self):
        result = []
        for obj in self:
            name=str(obj.intervenant_id.name)
            result.append((obj.id, name))
        return result


    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(ids).name_get()





class IsAffairePhase(models.Model):
    _name = 'is.affaire.phase'
    _description = u"Phases des Affaires"
    _order='name'


    def _compute(self):
        for obj in self:
            activites=self.env['is.activite'].search([('phase_activite_id.affaire_phase_id', '=', obj.id)])
            realise=0
            for act in activites:
                realise+=act.total_facturable
            obj.montant_realise=realise

            sous_phases=self.env['is.affaire.phase.activite'].search([('affaire_phase_id', '=', obj.id)])
            vendu=0
            for o in sous_phases:
                vendu+=o.total_vendu
            obj.total_vendu=vendu
            obj.montant_restant=obj.total_vendu-realise


    affaire_id      = fields.Many2one('is.affaire', 'Affaire', required=True, ondelete='cascade')
    name            = fields.Char("Phases")
    total_vendu     = fields.Float("Total vendu"    , digits=(14,2), compute='_compute', readonly=True, store=False)
    montant_realise = fields.Float("Montant réalisé", digits=(14,2), compute='_compute', readonly=True, store=False)
    montant_restant = fields.Float("Montant restant", digits=(14,2), compute='_compute', readonly=True, store=False)



class IsAffairePhaseActivite(models.Model):
    _name = 'is.affaire.phase.activite'
    _description = u"Sous-Phases"
    _order='name'


    @api.depends('montant_vendu','nb_unites')
    def _compute(self):
        for obj in self:
            obj.total_vendu=obj.montant_vendu*obj.nb_unites


    def _compute_realise(self):
        for obj in self:
            activites=self.env['is.activite'].search([('phase_activite_id', '=', obj.id)])
            realise=0
            for act in activites:
                realise+=act.total_facturable
            obj.montant_realise=realise
            obj.montant_restant=obj.total_vendu-realise


    affaire_id       = fields.Many2one('is.affaire', 'Affaire'      , required=True, ondelete='cascade')
    affaire_phase_id = fields.Many2one('is.affaire.phase', 'Phase')
    name             = fields.Char("Sous-phase", required=True)
    montant_vendu    = fields.Float("Montant vendu unitaire" , digits=(14,2))
    nb_unites        = fields.Float("Nombre d'unités vendues", digits=(14,2))
    total_vendu      = fields.Float("Total vendu"            , digits=(14,2), compute='_compute'        , readonly=True, store=True)
    montant_realise  = fields.Float("Montant réalisé"        , digits=(14,2), compute='_compute_realise', readonly=True, store=False)
    montant_restant  = fields.Float("Montant restant"        , digits=(14,2), compute='_compute_realise', readonly=True, store=False)


    @api.multi
    def acceder_activites_action(self, vals):
        for obj in self:
            res= {
                'name': 'Activités de la phase '+str(obj.name),
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'is.activite',
                'type': 'ir.actions.act_window',
                'domain': [['phase_activite_id','=',obj.id]],
            }
            return res


    @api.multi
    def creation_activite_action(self, vals):
        for obj in self:
            res= {
                'name': 'Activité',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'is.activite',
                'type': 'ir.actions.act_window',
                'context': {
                    'default_affaire_id'       : obj.affaire_id.id,
                    'default_phase_activite_id': obj.id,
                }
            }
            return res







class IsAffaire(models.Model):
    _name = 'is.affaire'
    _description = "Affaire"
    _order = 'name desc'


    @api.depends('date_creation')
    def _compute(self):
        for obj in self:
            if obj.date_creation:
                obj.annee_creation = str(obj.date_creation)[:4]
            obj.code_long=(obj.annee_creation or '')+'-'+(obj.name or '')


    @api.depends('intervenant_ids')
    def _compute_consultant_ids(self):
        for obj in self:
            obj.consultant_ids.unlink()
            ids=[]
            for row in obj.intervenant_ids:
                x=row.intervenant_id.is_consultant_id.id or False
                if x and x not in ids:
                    ids.append(x)
            print(ids)
            obj.consultant_ids=[(6,0,ids)]


        #'taxe_ids'          : ,
        #self.env['is.affaire.consultant.rel'].create(vals)


#'is_affaire_consultant_rel','affaire_id','consultant_id',


    name                 = fields.Char("Code affaire court", readonly=True, index=True)
    code_long            = fields.Char("Code affaire", compute='_compute', readonly=True, store=True)
    nature_affaire       = fields.Char("Nature de l'affaire"      , required=True)
    partner_id           = fields.Many2one('res.partner', "Client", required=True, index=True, domain=[('customer','=',True),('is_company','=',True)])
    type_intervention_id = fields.Many2one('is.type.intervention', "Type d'intervention")
    secteur_id           = fields.Many2one('is.secteur', "Secteur", help="Secteur ou Type de politique publique")
    type_offre_id        = fields.Many2one('is.type.offre', "Type d'offre")
    date_creation        = fields.Date("Date de création", default=fields.Date.today())
    annee_creation       = fields.Char("Année", compute='_compute', readonly=True, store=True)
    createur_id          = fields.Many2one('res.users', "Créateur", default=lambda self: self.env.user)
    ca_previsionnel      = fields.Integer("CA prévisionnel")
    fiscal_position_id   = fields.Many2one('account.fiscal.position', "Position fiscale")
    proposition_ids      = fields.Many2many('ir.attachment', 'is_affaire_propositions_rel', 'doc_id', 'file_id', 'Propositions commerciales')
    cause_id             = fields.Many2one('is.cause', "Cause si offre perdue")
    commentaire          = fields.Char("Commentaire si offre perdue")
    date_signature       = fields.Date("Date de signature de l'affaire")
    vendue_par_ids       = fields.One2many('is.affaire.vendue.par', 'affaire_id', u'Affaire vendue par')
    responsable_id       = fields.Many2one('res.users', "Responsable de l'affaire")

    nature_frais = fields.Selection([
            ('frais_inclus' , 'Frais inclus'),
            ('forfait'      , 'Forfait'),
            ('au_reel'      , 'Au réel'),
            ('reel_plafonne', 'Réel plafonné')
        ], u"Nature des frais",)
    forfait_jours_ids  = fields.One2many('is.affaire.forfait.jour', 'affaire_id', u' Forfait frais jour')

    correspondant_id = fields.Many2one('res.users', "Correspondant facturation")
    state                = fields.Selection([
            ('offre_en_cours', u'Offre en cours'),
            ('affaire_gagnee', u'Affaire gagnée'),
            ('affaire_soldee', u'Affaire soldée'),
            ('offre_perdue'  , u'Offre perdue')
        ], u"État", index=True, default='offre_en_cours')
    taux_ids           = fields.One2many('is.affaire.taux.journalier', 'affaire_id', u' Taux journalier')


    intervenant_ids    = fields.One2many('is.affaire.intervenant', 'affaire_id', u"Intervenants liés à l'affaire")
    consultant_ids     = fields.Many2many('res.users','is_affaire_consultant_rel','affaire_id','consultant_id', string="Consultants liées à cette affaire", compute='_compute_consultant_ids', readonly=True, store=True)

    convention_ids     = fields.Many2many('ir.attachment', 'is_affaire_convention_rel', 'doc_id', 'file_id', 'Conventions / Contrats')
    activer_phases     = fields.Boolean("Activer la gestion des phases", default=False)
    phase_ids          = fields.One2many('is.affaire.phase', 'affaire_id', u'Phases')
    activite_phase_ids = fields.One2many('is.affaire.phase.activite', 'affaire_id', u'Sous-phases')
    activite_ids       = fields.One2many('is.activite', 'affaire_id', u'Activités')
    frais_ids          = fields.One2many('is.frais'   , 'affaire_id', u'Frais')


    @api.multi
    def name_get(self):
        result = []
        for obj in self:
            result.append((obj.id, '['+str(obj.code_long)+'] '+str(obj.nature_affaire)+' ('+obj.partner_id.name+')'))
        return result


    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        ids = []
        if name:
            ids = self._search(['|','|',('code_long', 'ilike', name),('nature_affaire', 'ilike', name),('partner_id.name', 'ilike', name)] + args, limit=limit, access_rights_uid=name_get_uid)
        else:
            ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(ids).name_get()





    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('is.affaire')
        res = super(IsAffaire, self).create(vals)
        return res


    @api.multi
    def vers_affaire_gagnee(self, vals):
        for obj in self:
            obj.state='affaire_gagnee'

    @api.multi
    def vers_offre_en_cours(self, vals):
        for obj in self:
            obj.state='offre_en_cours'

    @api.multi
    def vers_offre_perdue(self, vals):
        for obj in self:
            obj.state='offre_perdue'

    @api.multi
    def vers_affaire_soldee(self, vals):
        for obj in self:
            obj.state='affaire_soldee'


    @api.multi
    def creation_activite(self, vals):
        for obj in self:
            res= {
                'name': 'Activité',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'is.activite',
                'type': 'ir.actions.act_window',
                'context': {'default_affaire_id': obj.id }
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
                'context': {'default_affaire_id': obj.id }
            }
            return res




