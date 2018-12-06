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
        ('VEB' , 'Ventes'),
        ('ACB' , 'Achats'),
    ], 'Journal', default='VEB')
    date_debut         = fields.Date(u"Date de début")
    date_fin           = fields.Date(u"Date de fin")
    facture_debut_id   = fields.Many2one('account.invoice', u"Facture début", required=True, domain=[('state','in',['open','paid'])])
    facture_fin_id     = fields.Many2one('account.invoice', u"Facture fin"  , required=True, domain=[('state','in',['open','paid'])])
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
    def action_generer_fichier(self):
        for obj in self:
            ct=0
            for row in obj.ligne_ids:
                if not row.account_id.id:
                    ct=ct+1
            if ct:
                raise Warning('Compte non renseigné sur '+str(ct)+' lignes')
            #** Ajout des lignes en 512000
            if obj.journal=='BQ':
                account_id = self.env['account.account'].search([('code','=','512000')])[0].id
                self.env['is.export.compta.ligne'].search([('export_compta_id','=',obj.id),('account_id','=',account_id)]).unlink()
                for row in obj.ligne_ids:
                    vals={
                        'export_compta_id'  : obj.id,
                        'ligne'             : row.ligne,
                        'date_facture'      : row.date_facture,
                        'account_id'        : account_id,
                        'libelle'           : row.libelle,
                        'libelle_piece'     : row.libelle_piece,
                        'journal'           : obj.journal,
                        'debit'             : row.credit,
                        'credit'            : row.debit,
                        'devise'            : u'EUR',
                    }
                    self.env['is.export.compta.ligne'].create(vals)
            self.generer_fichier()


    @api.multi
    def generer_lignes_action(self):
        cr=self._cr
        for obj in self:
            obj.ligne_ids.unlink()


            if obj.journal=='VEB':
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
                    WHERE aj.code='FAC'
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
                libelle      = row[3] or ''
                reference    = row[4] or ''
                montant=row[5]
                sens='C'
                if montant<0:
                    sens='D'
                    montant=-montant
                vals={
                    'export_compta_id': obj.id,
                    'journal'         : obj.journal,
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
            self.generer_fichier()


    def generer_fichier(self):
        cr=self._cr
        for obj in self:
            name='export-compta.csv'
            model='is.export.compta'
            attachments = self.env['ir.attachment'].search([('res_model','=',model),('res_id','=',obj.id),('name','=',name)])
            attachments.unlink()
            dest     = '/tmp/'+name
            f = codecs.open(dest,'wb',encoding='utf-8')
            for row in obj.ligne_ids:
                montant='%0.2f' % row.montant
                date=row.date_facture
                date=date.strftime('%d%m%Y')
                f.write('"'+date+'";')
                f.write('"'+obj.journal+'";')
                f.write('"'+row.general+'";')
                f.write('"'+row.auxilaire+'";')
                f.write('"'+row.sens+'";')
                f.write('"'+montant+'";')
                f.write('"'+row.libelle+'";')
                f.write('"'+row.reference+'"')
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







