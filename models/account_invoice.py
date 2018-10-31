# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

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


                #res=self.env['account.invoice.line'].product_id_change(product_id, uom_id, quantite, name, invoice_type, partner_id, fiscal_position)

                vals={
                    'invoice_id': obj.id,
                    'product_id': act.intervenant_id.intervenant_id.id,
                    'name'      : act.nature_activite,
                    'price_unit': 12.34,
                    'account_id': account_id,
                }
                print(vals)
                self.env['account.invoice.line'].create(vals)

