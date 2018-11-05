# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


def f0(number):
    return '{0:,.0f}'.format(number).replace(',', ' ').replace('.', ',')

def f2(number):
    return '{0:,.2f}'.format(number).replace(',', ' ').replace('.', ',')


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    is_dates_intervention = fields.Char("Dates d'intervention")
    is_activite_id        = fields.Many2one('is.activite', 'Activité')


class AccountInvoice(models.Model):
    _inherit = "account.invoice"


    is_affaire_id = fields.Many2one('is.affaire', 'Affaire')
    is_activites  = fields.Many2many('is.activite', 'is_account_invoice_activite_rel', 'invoice_id', 'activite_id')


    @api.multi
    def activites_vers_lignes_action(self, vals):
        for obj in self:
            print(obj)
            obj.invoice_line_ids.unlink()

            activites=self.env['is.activite'].search([('invoice_id', '=', obj.id)])
            for act in activites:
                print(act)
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


            obj.compute_taxes()




    @api.multi
    def get_invoice_line(self):
        for obj in self:

            html="""
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th class="text-left"><span>Description</span></th>
                                <th class="text-right"><span>Quantité</span></th>
                                <th class="text-right"><span>Prix unitaire</span></th>
                                <th class="text-right"><span>Montant HT</span></th>
                                <th class="text-right"><span>Montant TTC</span></th>
                            </tr>
                        </thead>
                        <tbody class="invoice_tbody">
            """

            for phase in obj.is_affaire_id.phase_ids:
                html+='<tr><td colspan="5" class="bg-200">' +phase.name+'</td></tr>'

                for sous_phase in obj.is_affaire_id.activite_phase_ids:
                    if sous_phase.affaire_phase_id.id==phase.id:
                        html+='<tr><td colspan="5" class="bg-100">' +sous_phase.name+'</td></tr>'

                        for line in obj.invoice_line_ids:
                            if line.is_activite_id.phase_activite_id.id==sous_phase.id:
                                html+='<tr>'
                                html+='<td class="text-left">' +line.name+'</td>'
                                html+='<td class="text-right">'+f2(line.quantity)+'</td>'
                                html+='<td class="text-right">'+f2(line.price_unit)+' €</td>'
                                html+='<td class="text-right">'+f2(line.price_subtotal)+' €</td>'
                                html+='<td class="text-right">'+f2(line.price_total)+' €</td>'
                                html+='</tr>'
            html+='</tbody>'
            html+='</table>'
            return html




#            html="""
#                    <table class="table table-sm">
#                        <thead>
#                            <tr>
#                                <th class="text-left"><span>Description</span></th>
#                                <th class="text-right"><span>Quantité</span></th>
#                                <th class="text-right"><span>Prix unitaire</span></th>
#                                <th class="text-right"><span>Montant HT</span></th>
#                            </tr>
#                        </thead>
#                        <tbody class="invoice_tbody">
#            """
#            for line in obj.invoice_line_ids:
#                html+='<tr>'
#                html+='<td class="text-left">' +line.name+'</td>'
#                html+='<td class="text-right">'+f2(line.quantity)+'</td>'
#                html+='<td class="text-right">'+f2(line.price_unit)+' €</td>'
#                html+='<td class="text-right">'+f2(line.price_subtotal)+' €</td>'
#                html+='</tr>'
#            html+='</tbody>'
#            html+='</table>'
#            return html




