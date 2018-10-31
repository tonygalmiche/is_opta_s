# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class IsActivite(models.Model):
    _name = 'is.activite'
    _description = "Activité"
    _order = 'affaire_id,nature_activite'


    @api.depends('tarification_id','nb_facturable')
    def _compute(self):
        for obj in self:
            if obj.tarification_id:
                obj.montant=obj.tarification_id.montant
                obj.total_facturable=obj.montant*obj.nb_facturable


    affaire_id           = fields.Many2one('is.affaire', 'Affaire', required=True,index=True)
    phase_activite_id    = fields.Many2one('is.affaire.phase.activite', 'Sous-phase',index=True)
    nature_activite      = fields.Char("Nature de l'activité"     , required=True, index=True)
    date_debut           = fields.Date("Date de début de l'activité", required=True, index=True)
    dates_intervention   = fields.Char("Dates des jours d'intervention")

    #acteur_id            = fields.Many2one('res.users', "Acteur", default=lambda self: self.env.user)
    #sous_traitant_id     = fields.Many2one('res.partner', "Sous-traitant (ou co-traitant)", domain=[('supplier','=',True),('is_company','=',True)])
    intervenant_id        = fields.Many2one('is.affaire.intervenant', "Intervenant", required=True,index=True)

    tarification_id      = fields.Many2one('is.affaire.taux.journalier', "Tarification")
    montant              = fields.Float("Montant unitaire", compute='_compute', readonly=True, store=True, digits=(14,2))
    nb_realise           = fields.Float("Nb unités réalisées"  , digits=(14,2))
    nb_facturable        = fields.Float("Nb unités facturables", digits=(14,2))
    total_facturable     = fields.Float("Total facturable", compute='_compute', readonly=True, store=True, digits=(14,2))
    facture_sur_accompte = fields.Boolean("Facture sur acompte")
    point_cle            = fields.Text("Points clés de l'activité réalisée")
    suivi_temps_ids      = fields.One2many('is.suivi.temps', 'activite_id', u'Suivi du temps')
    frais_ids            = fields.One2many('is.frais', 'activite_id', u'Frais')
    invoice_id           = fields.Many2one('account.invoice', "Facture",index=True)
    state                = fields.Selection([
            ('brouillon', u'Brouillon'),
            ('diffuse'  , u'Diffusé'),
            ('valide'   , u'Validé'),
        ], u"État", index=True, default='brouillon')



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
    def vers_diffuse(self, vals):
        for obj in self:
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



