# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


def f0(number):
    return '{0:,.0f}'.format(number).replace(',', ' ').replace('.', ',')

def f2(number):
    return '{0:,.2f}'.format(number).replace(',', ' ').replace('.', ',')


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    is_dates_intervention = fields.Char("Dates d'intervention")
    is_activite_id        = fields.Many2one('is.activite', 'Activité')
    is_frais_ligne_id     = fields.Many2one('is.frais.lignes', 'Ligne de frais')


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    is_affaire_id    = fields.Many2one('is.affaire', 'Affaire')
    is_activites     = fields.Many2many('is.activite', 'is_account_invoice_activite_rel', 'invoice_id', 'activite_id')
    is_phase         = fields.Boolean('Afficher les phases',default=True)
    is_intervenant   = fields.Boolean('Afficher les intervenants sur la facture')
    is_prix_unitaire = fields.Boolean('Afficher les quantités et prix unitaire sur la facture')


    @api.multi
    def activites_vers_lignes_action(self, vals):
        for obj in self:
            obj.invoice_line_ids.unlink()
            activites=self.env['is.activite'].search([('invoice_id', '=', obj.id)])
            for act in activites:
                act.invoice_id=False
            for act in obj.is_activites:
                act.invoice_id=obj.id
                account_id=act.intervenant_id.intervenant_id.property_account_income_id.id
                vals={
                    'invoice_id'           : obj.id,
                    'product_id'           : act.intervenant_id.intervenant_id.id,
                    'name'                 : ' ',
                    'price_unit'           : 0,
                    'account_id'           : account_id,
                    'is_dates_intervention': act.dates_intervention,
                    'is_activite_id'       : act.id,
                }
                line=self.env['account.invoice.line'].create(vals)
                line._onchange_product_id()
                line.quantity   = act.nb_facturable
                line.price_unit = act.montant
                line.name       = act.nature_activite

            for act in obj.is_activites:
                for frais in act.frais_ids:
                    for ligne in frais.ligne_ids:
                        account_id=ligne.product_id.property_account_income_id.id
                        if account_id==False:
                            raise Warning(u"Compte de revenu non renseigné pour l'article "+ligne.product_id.name)
                        vals={
                            'invoice_id'           : obj.id,
                            'product_id'           : ligne.product_id.id,
                            'name'                 : ligne.product_id.name,
                            'price_unit'           : 0,
                            'account_id'           : account_id,
                            'is_activite_id'       : act.id,
                            'is_frais_ligne_id'    : ligne.id,
                        }
                        line=self.env['account.invoice.line'].create(vals)
                        line._onchange_product_id()
                        line.quantity   = 1
                        line.price_unit = ligne.montant_ttc
            obj.compute_taxes()


    @api.multi
    def _add_tr(self,line):
        for obj in self:
            html='<tr>'
            html+='<td class="text-left">' +line.name+'</td>'
            if obj.is_intervenant:
                html+='<td class="text-left">'+line.is_activite_id.intervenant_id.intervenant_id.name+'</td>'
                html+='<td class="text-left">'+(line.is_activite_id.dates_intervention or '')+'</td>'

            if obj.is_prix_unitaire:
                html+='<td class="text-right">'+f2(line.quantity)+'</td>'
                html+='<td class="text-right">'+f2(line.price_unit)+' €</td>'
            html+='<td class="text-right">'+f2(line.price_subtotal)+' €</td>'
            html+='</tr>'
            return html


    @api.multi
    def get_invoice_line(self):
        for obj in self:
            colspan=3
            html="""
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th class="text-left"><span>Description</span></th>
            """
            if obj.is_intervenant:
                colspan+=2
                html+="""
                                <th class="text-left"><span>Intervenant</span></th>
                                <th class="text-left"><span>Date d'intervention</span></th>
            """
            if obj.is_prix_unitaire:
                colspan+=2
                html+="""
                                <th class="text-right"><span>Quantité</span></th>
                                <th class="text-right"><span>Prix unitaire</span></th>
            """
            html+="""
                                <th class="text-right"><span>Montant HT</span></th>
                            </tr>
                        </thead>
                        <tbody class="invoice_tbody">
            """


            if obj.is_phase:
                #Recherche des phases et sous-phases à afficher ****************
                phase_ids=[]
                sous_phase_ids=[]
                for phase in obj.is_affaire_id.phase_ids:
                    for sous_phase in obj.is_affaire_id.activite_phase_ids:
                        if sous_phase.affaire_phase_id.id==phase.id:
                            for line in obj.invoice_line_ids:
                                if line.is_activite_id.phase_activite_id.id==sous_phase.id:
                                    if phase not in phase_ids:
                                        phase_ids.append(phase)
                                    if sous_phase not in sous_phase_ids:
                                        sous_phase_ids.append(sous_phase)
                #***************************************************************
                for phase in phase_ids:
                    html+='<tr><td colspan="'+str(colspan)+'" class="bg-200">' +phase.name+'</td></tr>'
                    for sous_phase in sous_phase_ids:
                        if sous_phase.affaire_phase_id.id==phase.id:
                            html+='<tr><td colspan="'+str(colspan)+'" class="bg-100">' +sous_phase.name+'</td></tr>'
                            for line in obj.invoice_line_ids:
                                if line.is_activite_id.phase_activite_id.id==sous_phase.id:
                                    if line.is_frais_ligne_id.id==False:
                                        html+=self._add_tr(line)
            else:
                for line in obj.invoice_line_ids:
                    if line.is_frais_ligne_id.id==False:
                        html+=self._add_tr(line)



            html+='</tbody>'
            html+='</table>'
            return html





