# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import Warning
import datetime
import codecs
import unicodedata
import base64
#import csv, cStringIO


def s(txt):
    if type(txt)!=unicode:
        txt = unicode(txt,'utf-8#')
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore')
    return txt


class is_export_compta(models.Model):
    _name='is.export.compta'
    _description = "Export Compta"
    _order='name desc'

    name               = fields.Char(u"N°Folio"      , readonly=True)
    journal = fields.Selection([
        ('VE', 'Ventes'),
        ('AC', 'Achats'),
    ], 'Journal', default='VE',required=True)
    date_debut         = fields.Date(u"Date de début",required=True)
    date_fin           = fields.Date(u"Date de fin"  ,required=True)
    file_ids           = fields.Many2many('ir.attachment', 'is_export_compta_attachment_rel', 'doc_id', 'file_id', u'Fichiers')
    ligne_ids          = fields.One2many('is.export.compta.ligne', 'export_compta_id', u'Lignes')
    _defaults = {
    }


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('is.export.compta')
        res = super(is_export_compta, self).create(vals)
        return res




    @api.multi
    def generer_lignes_action(self):
        cr,uid,context = self.env.args
        for obj in self:
            user = self.env['res.users'].browse(uid)
            company  = user.company_id
            obj.ligne_ids.unlink()
            if obj.journal=='VE':
                journal=company.is_journal_vente
                sql="""
                    SELECT  
                        aml.date,
                        aa.code, 
                        rp.is_compte_auxilaire_client,
                        rp.name,
                        ai.number,
                        sum(aml.credit)-sum(aml.debit)
                    FROM account_move_line aml left outer join account_invoice ai        on aml.move_id=ai.move_id
                                               inner join account_account aa             on aml.account_id=aa.id
                                               left outer join res_partner rp            on aml.partner_id=rp.id
                                               inner join account_journal aj             on aml.journal_id=aj.id
                    WHERE 
                        aj.code='FAC' and
                        aml.date>='"""+str(obj.date_debut)+"""' and
                        aml.date<='"""+str(obj.date_fin)+"""' 

                    GROUP BY
                        aml.date,
                        aa.code, 
                        rp.is_compte_auxilaire_client,
                        ai.number,
                        rp.name
                """
                cr.execute(sql)
                ct=0
                for row in cr.fetchall():
                    ct=ct+1
                    date_facture = row[0]
                    general      = row[1]
                    auxilaire    = row[2] or ''
                    if general[0:3]!='411':
                        auxilaire=''
                    libelle      = row[3] or ''
                    reference    = row[4] or ''
                    montant=row[5]
                    sens='C'
                    if montant<0:
                        sens='D'
                        montant=-montant
                    vals={
                        'export_compta_id': obj.id,
                        'journal'         : journal,
                        'ligne'           : ct,
                        'date_facture'    : date_facture,
                        'general'         : general,
                        'auxilaire'       : auxilaire,
                        'sens'            : sens,
                        'montant'         : montant,
                        'libelle'         : libelle,
                        'reference'       : reference,
                    }
                    self.env['is.export.compta.ligne'].create(vals)

            if obj.journal=='AC':
                journal=company.is_journal_achat
                frais = self.env['is.frais'].search([
                    ('date_creation','>=',obj.date_debut),
                    ('date_creation','<=',obj.date_fin),
                    ('state','=','valide'),
                ],order='date_creation')
                ct=0
                for f in frais:
                    for lig in f.ligne_ids:
                        ct=ct+1

                        #** Ligne TTC ******************************************
                        general=''
                        auxilaire=''
                        if lig.partner_id:
                            if lig.refacturable=='non':
                                general   = lig.partner_id.property_account_payable_id.code
                                auxilaire = lig.partner_id.is_compte_auxilaire_fournisseur or ''
                            else:
                                general   = lig.partner_id.property_account_payable_id.code
                                auxilaire = lig.partner_id.is_compte_auxilaire_fournisseur or ''
                        else:
                            general=f.createur_id.is_compte_general or ''
                        sens='C'
                        montant=lig.montant_ttc
                        libelle=lig.product_id.name
                        reference=f.chrono_long
                        vals={
                            'export_compta_id': obj.id,
                            'journal'         : journal,
                            'ligne'           : ct,
                            'date_facture'    : f.date_creation,
                            'general'         : general,
                            'auxilaire'       : auxilaire,
                            'sens'            : sens,
                            'montant'         : montant,
                            'libelle'         : libelle,
                            'reference'       : reference,
                        }
                        self.env['is.export.compta.ligne'].create(vals)
                        #*******************************************************

                        #** Ligne HT *******************************************
                        if lig.partner_id:
                            if lig.refacturable=='non':
                                general   = lig.product_id.property_account_expense_id.code or ''
                            else:
                                general   = lig.product_id.property_account_income_id.code or ''
                        else:
                            general=f.createur_id.is_compte_general or ''


                        vals['general']   = general
                        vals['auxilaire'] = ''
                        montant=lig.montant_ttc-lig.montant_tva
                        vals['montant'] = montant
                        vals['sens']    = 'D'
                        self.env['is.export.compta.ligne'].create(vals)
                        #*******************************************************

                        #** Ligne TVA ******************************************
                        if lig.montant_tva:
                            general='445xxx'
                            for tax in lig.product_id.supplier_taxes_id:
                                general=tax.account_id.code
                            vals['general']   = general
                            vals['montant'] = lig.montant_tva
                            self.env['is.export.compta.ligne'].create(vals)
                        #*******************************************************

            self.generer_fichier_action()


    def generer_fichier_action(self):
        cr=self._cr
        for obj in self:
            name='export-compta.csv'
            model='is.export.compta'
            attachments = self.env['ir.attachment'].search([('res_model','=',model),('res_id','=',obj.id),('name','=',name)])
            attachments.unlink()
            dest     = '/tmp/'+name
            f = codecs.open(dest,'wb',encoding='utf-8')

            f.write("DATE;JOURNAL;GENERAL;AUXILIAIRE;SENS;MONTANT;LIBELLE;REFERENCE\r\n")
            for row in obj.ligne_ids:
                montant='%0.2f' % row.montant
                date=row.date_facture
                date=date.strftime('%d%m%Y')
                f.write(date+';')
                f.write(obj.journal+';')
                f.write(row.general+';')
                f.write(row.auxilaire+';')
                f.write(row.sens+';')
                f.write(montant+';')
                f.write(row.libelle+';')
                f.write(row.reference)
                f.write('\r\n')
            f.close()
            r = open(dest,'rb').read()
            r=base64.b64encode(r)
            vals = {
                'name':        name,
                'datas_fname': name,
                'type':        'binary',
                'res_model':   model,
                'res_id':      obj.id,
                'datas':       r,
            }
            attachment = self.env['ir.attachment'].create(vals)
            obj.file_ids=[(6,0,[attachment.id])]


class is_export_compta_ligne(models.Model):
    _name = 'is.export.compta.ligne'
    _description = u"Lignes d'export en compta"
    _order='ligne,id'

    export_compta_id = fields.Many2one('is.export.compta', 'Export Compta', required=True, ondelete='cascade')
    ligne            = fields.Integer("Ligne")
    date_facture     = fields.Date("Date")
    journal          = fields.Char("Journal")
    general          = fields.Char("Compte général")
    auxilaire        = fields.Char("Compte auxilaire")
    sens             = fields.Char("Sens")
    montant          = fields.Float("Montant")
    libelle          = fields.Char("Libéllé")
    reference        = fields.Char("Référence")







