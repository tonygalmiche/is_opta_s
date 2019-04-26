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


class is_export_compta_ana(models.Model):
    _name='is.export.compta.ana'
    _description = "Export Compta Analytique"
    _order='name desc'

    name               = fields.Char(u"N°Folio", readonly=True)
    journal = fields.Selection([
        ('VE', 'Ventes'),
        ('AC', 'Achats'),
    ], 'Journal', default='VE',required=True)
    date_debut         = fields.Date(u"Date de début",required=True)
    date_fin           = fields.Date(u"Date de fin"  ,required=True)
    file_ids           = fields.Many2many('ir.attachment', 'is_export_compta_ana_attachment_rel', 'doc_id', 'file_id', u'Fichiers')
    ligne_ids          = fields.One2many('is.export.compta.ana.ligne', 'export_compta_id', u'Lignes')
    _defaults = {
    }


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('is.export.compta.ana')
        res = super(is_export_compta_ana, self).create(vals)
        return res


    @api.multi
    def ajout_ligne(self,id,journal,ct,type_ecriture,date_facture,compte_general,compte_auxilaire,sens,montant,piece,axe1,axe2,libelle,partner_id,anomalie,frais_id=False,product_id=False,consultant_id=False):
        vals={
            'export_compta_id': id,
            'ligne'           : ct,
            'type_ecriture'   : type_ecriture,
            'date_facture'    : date_facture,
            'journal'         : journal,
            'general'         : compte_general,
            'auxilaire'       : compte_auxilaire,
            'sens'            : sens,
            'montant'         : montant,
            'libelle'         : libelle,
            'reference'       : piece,
            'partner_id'      : partner_id,
            'axe1'            : axe1,
            'axe2'            : axe2,
            'anomalie'        : ', '.join(anomalie),
            'frais_id'        : frais_id,
            'product_id'      : product_id,
            'consultant_id'   : consultant_id,
        }
        self.env['is.export.compta.ana.ligne'].create(vals)


    @api.multi
    def generer_lignes_action(self):
        cr,uid,context = self.env.args
        for obj in self:
            user = self.env['res.users'].browse(uid)
            company  = user.company_id
            obj.ligne_ids.unlink()


            if obj.journal=='AC':
                journal=company.is_journal_achat
                ct=0
                frais=self.env['is.frais'].search([
                        ('date_creation', '>=', obj.date_debut),
                        ('date_creation', '<=', obj.date_fin),
                        ('state'       , '=', 'valide'),
                    ])
                for f in frais:
                    frais_id = f.id

                    #** Recherche du client ************************************
                    client=f.affaire_id.partner_id.name
                    #***********************************************************


                    #** Type d'activité ****************************************
                    types={
                        'formation': 1000,
                        'conseil'  : 2000,
                        'divers'   : 9000,
                    }
                    type_activite = types[f.type_activite]
                    #***********************************************************


                    for l in f.ligne_ids:
                        product_id = l.product_id.id

                        #** Recherche du compte général ************************
                        compte_general=''
                        if l.refacturable!='oui':
                            compte_general = l.product_id.property_account_expense_id.code
                        else:
                            compte_general = '467100'
                        if not compte_general:
                            anomalie.append("Compte non trouvé pour ce type de dépense")
                        #*******************************************************





                        #** Ligne HT *******************************************
                        anomalie=[]
                        ct=ct+1
                        compte_auxilaire=''
                        montant = l.montant_ttc-l.montant_tva
                        piece = f.chrono_long
                        if l.refacturable!='oui':
                            libelle = l.product_id.name
                        else:
                            libelle = client
                        partner_id = l.partner_id.id
                        axe1=''
                        axe2=''
                        self.ajout_ligne(obj.id,journal,ct,'G',f.date_creation,compte_general,compte_auxilaire,'D',montant,piece,axe1,axe2,libelle,partner_id,anomalie,frais_id,product_id)
                        #*******************************************************


                        #** Ligne Axe1 *****************************************
                        anomalie=[]
                        ct=ct+1
                        axe1 = type_activite
                        axe2 = ''
                        self.ajout_ligne(obj.id,journal,ct,'A1',f.date_creation,compte_general,compte_auxilaire,'D',montant,piece,axe1,axe2,libelle,partner_id,anomalie,frais_id,product_id)
                        #*******************************************************


                        #** Ligne Axe2 *****************************************
                        anomalie=[]
                        products=self.env['product.product'].search([
                                ('is_consultant_id', '=', f.createur_id.id),
                            ])
                        axe1=''
                        axe2=''
                        consultant_id=False
                        for product in  products:
                            consultant_id=product.id
                            axe2 = product.is_code_analytique
                        if not axe2:
                            anomalie=["Code analytique de l'article associé au consultant non défini"]
                        self.ajout_ligne(obj.id,journal,ct,'A2',f.date_creation,compte_general,compte_auxilaire,'D',montant,piece,axe1,axe2,libelle,partner_id,anomalie,frais_id,product_id,consultant_id)
                        #*******************************************************


                        #** Ligne TVA déductible *******************************
                        anomalie=[]
                        if l.refacturable!='oui':
                            compte_general = '445660'
                            montant        = l.montant_tva
                            libelle        = l.product_id.name
                            axe1 = ''
                            axe2 = ''
                            if montant:
                                self.ajout_ligne(obj.id,journal,ct,'G',f.date_creation,compte_general,compte_auxilaire,'D',montant,piece,axe1,axe2,libelle,partner_id,anomalie,frais_id,product_id)
                        #*******************************************************


                        #** Ligne TTC ******************************************
                        anomalie=[]
                        compte_auxilaire = ''
                        compte_general   = ''
                        effectuee_par = l.effectuee_par_id.name
                        if effectuee_par == 'OPTA-S':
                            compte_general   = '401000'
                            compte_auxilaire=l.partner_id.is_compte_auxilaire_fournisseur
                            if not compte_auxilaire:
                                anomalie.append("Compte auxilaire non trouvé pour ce fournisseur")
                        if effectuee_par == 'CONSULTANT':
                            compte_general = f.createur_id.partner_id.property_account_payable_id.code
                        if effectuee_par == 'CAISSE OPTA-S':
                            compte_general = '531000'
                        if effectuee_par == 'ESPECES_ASSOCIE':
                            compte_general = '455111'
                        montant = l.montant_ttc
                        libelle = l.product_id.name
                        axe1    = ''
                        axe2    = ''
                        self.ajout_ligne(obj.id,journal,ct,'G',f.date_creation,compte_general,compte_auxilaire,'C',montant,piece,axe1,axe2,libelle,partner_id,anomalie,frais_id,product_id)
                        #*******************************************************


            if obj.journal=='VE':
                journal=company.is_journal_vente


                invoices=self.env['account.invoice'].search([
                        ('date_invoice', '>=', obj.date_debut),
                        ('date_invoice', '<=', obj.date_fin),
                        ('state'       , 'in', ['open','paid']),
                    ])

                ct=0
                for invoice in invoices:
                    #** Ligne G Total TTC au débit *****************************
                    ct=ct+1
                    auxilaire=invoice.partner_id.is_compte_auxilaire_client
                    anomalie=''
                    if not auxilaire:
                        anomalie='Compte auxilaire non défini pour ce client'
                    vals={
                        'export_compta_id': obj.id,
                        'ligne'           : ct,
                        'type_ecriture'   : 'G',
                        'date_facture'    : invoice.date_invoice,
                        'journal'         : journal,
                        'general'         : '411000',
                        'auxilaire'       : auxilaire,
                        'sens'            : 'D',
                        'montant'         : invoice.amount_total,
                        'libelle'         : invoice.partner_id.name,
                        'reference'       : invoice.number,
                        'invoice_id'      : invoice.id,
                        'partner_id'      : invoice.partner_id.id,
                        'anomalie'        : anomalie,
                    }
                    self.env['is.export.compta.ana.ligne'].create(vals)
                    #***********************************************************


                    for line in invoice.invoice_line_ids:
                        if not line.is_frais_id:
                            #** Lignes G des activités HT **********************
                            ct=ct+1
                            vals={
                                'export_compta_id': obj.id,
                                'ligne'           : ct,
                                'type_ecriture'   : 'G',
                                'date_facture'    : invoice.date_invoice,
                                'journal'         : journal,
                                'general'         : line.account_id.code,
                                'sens'            : 'C',
                                'montant'         : line.price_subtotal,
                                'libelle'         : invoice.partner_id.name,
                                'reference'       : invoice.number,
                                'invoice_id'      : invoice.id,
                                'partner_id'      : invoice.partner_id.id,
                            }
                            self.env['is.export.compta.ana.ligne'].create(vals)
                            #***************************************************

                            #** Lignes A1 des activités HT *********************
                            ct=ct+1
                            #axe1=line.account_id.is_code_analytique
                            axe1 = invoice.fiscal_position_id.is_code_analytique or '2000'
                            anomalie=''
                            if not axe1:
                                anomalie='Code analytique non défini pour ce compte général'
                            vals={
                                'export_compta_id': obj.id,
                                'ligne'           : ct,
                                'type_ecriture'   : 'A1',
                                'date_facture'    : invoice.date_invoice,
                                'journal'         : journal,
                                'general'         : line.account_id.code,
                                'sens'            : 'C',
                                'montant'         : line.price_subtotal,
                                'libelle'         : invoice.partner_id.name,
                                'reference'       : invoice.number,
                                'invoice_id'      : invoice.id,
                                'partner_id'      : invoice.partner_id.id,
                                'activite_id'     : line.is_activite_id.id,
                                'account_id'      : line.account_id.id,
                                'axe1'            : axe1,
                                'anomalie'        : anomalie,
                            }
                            self.env['is.export.compta.ana.ligne'].create(vals)
                            #***************************************************


                            #** Lignes A2 des activités HT *********************
                            ct=ct+1
                            consultant = line.is_activite_id.intervenant_id.intervenant_id
                            axe2=consultant.is_code_analytique
                            anomalie=''
                            if not axe2:
                                anomalie='Code analytique non défini pour le consultant de cette activité'
                            vals={
                                'export_compta_id': obj.id,
                                'ligne'           : ct,
                                'type_ecriture'   : 'A2',
                                'date_facture'    : invoice.date_invoice,
                                'journal'         : journal,
                                'general'         : line.account_id.code,
                                'sens'            : 'C',
                                'montant'         : line.price_subtotal,
                                'libelle'         : invoice.partner_id.name,
                                'reference'       : invoice.number,
                                'invoice_id'      : invoice.id,
                                'partner_id'      : invoice.partner_id.id,
                                'activite_id'     : line.is_activite_id.id,
                                'consultant_id'   : consultant.id,
                                'axe2'            : axe2,
                                'anomalie'        : anomalie,
                            }
                            self.env['is.export.compta.ana.ligne'].create(vals)
                            #***************************************************


                    #** Frais refacturés ***************************************
                    comptes_au_forfait=['791000','791100','791110']
                    refacture=0
                    for line in invoice.invoice_line_ids:
                        if line.is_frais_id and line.account_id.code not in comptes_au_forfait:
                            refacture+=line.price_subtotal
                    if refacture:
                        ct=ct+1
                        vals={
                            'export_compta_id': obj.id,
                            'ligne'           : ct,
                            'type_ecriture'   : 'G',
                            'date_facture'    : invoice.date_invoice,
                            'journal'         : journal,
                            'general'         : line.account_id.code,
                            'sens'            : 'C',
                            'montant'         : refacture,
                            'libelle'         : invoice.partner_id.name,
                            'reference'       : invoice.number,
                            'invoice_id'      : invoice.id,
                            'partner_id'      : invoice.partner_id.id,
                        }
                        print('Frais refacturés',invoice.number)
                        self.env['is.export.compta.ana.ligne'].create(vals)
                    #***********************************************************


                    #** Frais au forfait ***************************************
                    frais_forfait={}
                    general=''
                    axe1=''
                    for line in invoice.invoice_line_ids:
                        if line.is_frais_id and line.account_id.code in comptes_au_forfait:
                            general=line.account_id.code
                            axe1=line.account_id.is_code_analytique
                            axe2=line.is_activite_id.intervenant_id.intervenant_id.is_code_analytique
                            if axe2 not in frais_forfait:
                                frais_forfait[axe2]=0
                            frais_forfait[axe2]=+line.price_subtotal
                    for axe2 in frais_forfait:
                        ct=ct+1
                        vals={
                            'export_compta_id': obj.id,
                            'ligne'           : ct+9000,
                            'type_ecriture'   : 'G',
                            'date_facture'    : invoice.date_invoice,
                            'journal'         : journal,
                            'general'         : general,
                            'sens'            : 'C',
                            'montant'         : frais_forfait[axe2],
                            'libelle'         : invoice.partner_id.name,
                            'reference'       : invoice.number,
                            'invoice_id'      : invoice.id,
                            'partner_id'      : invoice.partner_id.id,
                        }
                        self.env['is.export.compta.ana.ligne'].create(vals)
                        ct=ct+1
                        vals['ligne']         = ct+1000
                        vals['type_ecriture'] = 'A1'
                        vals['axe1']          = axe1
                        vals['axe2']          = ''
                        self.env['is.export.compta.ana.ligne'].create(vals)
                        ct=ct+1
                        vals['ligne']         = ct+1000
                        vals['type_ecriture'] = 'A2'
                        vals['axe1']          = ''
                        vals['axe2']          = axe2
                        self.env['is.export.compta.ana.ligne'].create(vals)


                    #** Ligne G pour la TVA ************************************
                    for line in invoice.tax_line_ids:
                        if line.amount_total:
                            ct=ct+1
                            vals={
                                'export_compta_id': obj.id,
                                'ligne'           : ct,
                                'type_ecriture'   : 'G',
                                'date_facture'    : invoice.date_invoice,
                                'journal'         : journal,
                                'general'         : line.account_id.code,
                                'auxilaire'       : '',
                                'sens'            : 'C',
                                'montant'         : line.amount_total,
                                'libelle'         : invoice.partner_id.name,
                                'reference'       : invoice.number,
                                'invoice_id'      : invoice.id,
                                'partner_id'      : invoice.partner_id.id,
                                'anomalie'        : '',
                            }
                            self.env['is.export.compta.ana.ligne'].create(vals)
                    #***********************************************************

            self.generer_fichier_action()


    def generer_fichier_action(self):
        cr=self._cr
        for obj in self:
            name='export-compta-ana.csv'
            model='is.export.compta.ana'
            attachments = self.env['ir.attachment'].search([('res_model','=',model),('res_id','=',obj.id),('name','=',name)])
            attachments.unlink()
            dest     = '/tmp/'+name
            f = codecs.open(dest,'wb',encoding='utf-8')

            f.write("TYPE;DATE;JOURNAL;GENERAL;AUXILIAIRE;SENS;MONTANT;LIBELLE;REFERENCE;AXE1;AXE2\r\n")
            for row in obj.ligne_ids:
                montant='%0.2f' % row.montant
                date=row.date_facture
                date=date.strftime('%d%m%Y')
                f.write(row.type_ecriture+';')
                f.write(date+';')
                f.write(row.journal+';')
                f.write(row.general+';')
                f.write((row.auxilaire or '')+';')
                f.write(row.sens+';')
                f.write(montant+';')
                f.write(row.libelle+';')
                f.write(row.reference+';')
                f.write((row.axe1 or '')+';')
                f.write((row.axe2 or ''))
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
    _name = 'is.export.compta.ana.ligne'
    _description = u"Lignes d'export en compta analytique"
    _order='ligne,id'

    export_compta_id = fields.Many2one('is.export.compta.ana', 'Export Compta Analytique', required=True, ondelete='cascade')
    ligne            = fields.Integer("Ligne")
    type_ecriture    = fields.Char("Type d'écriture")
    date_facture     = fields.Date("Date")
    journal          = fields.Char("Journal")
    general          = fields.Char("Compte général")
    auxilaire        = fields.Char("Compte auxilaire")
    sens             = fields.Char("Sens")
    montant          = fields.Float("Montant")
    libelle          = fields.Char("Libéllé")
    reference        = fields.Char("N°Pièce")
    axe1             = fields.Char("Axe 1 activités")
    axe2             = fields.Char("Axe 2 consultants")
    invoice_id       = fields.Many2one('account.invoice', "Facture", readonly=True)
    partner_id       = fields.Many2one('res.partner', "Client/Fournisseur", readonly=True)
    activite_id      = fields.Many2one('is.activite', "Activité", readonly=True)
    frais_id         = fields.Many2one('is.frais', "Frais", readonly=True)
    product_id       = fields.Many2one('product.product', "Article", readonly=True)
    consultant_id    = fields.Many2one('product.product', "Consultant", readonly=True)
    account_id       = fields.Many2one('account.account', "Compte", readonly=True)
    anomalie         = fields.Char("Anomalie", readonly=True)



