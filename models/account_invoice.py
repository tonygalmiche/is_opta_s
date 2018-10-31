# -*- coding: utf-8 -*-
from odoo import api, fields, models, _



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



