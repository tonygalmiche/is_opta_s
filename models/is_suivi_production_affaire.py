# -*- coding: utf-8 -*-

from openerp import tools
from openerp import models,fields,api
from openerp.tools.translate import _


#TODO : Colonne privée sur le salaire



class IsSuiviProductionAffaire(models.Model):
    _description = "Suivi de production par affaire"
    _name = 'is.suivi.production.affaire'


    createur_id = fields.Many2one('res.users', "Créateur", default=lambda self: self.env.user, readonly=True)
    date_debut  = fields.Date("Date de début", required=True)
    date_fin    = fields.Date("Date de fin"  , required=True)
    affaire_id  = fields.Many2one('is.affaire', 'Affaire')
    regroupement_par = fields.Selection([
            ('affaire'   , 'Affaire'),
            ('consultant', 'Consultant'),
        ], u" Regroupement par",default='affaire',required=True)
    line_ids = fields.One2many('is.suivi.production.affaire.line', 'suivi_id', u'Lignes')


    @api.multi
    def name_get(self):
        result = []
        for obj in self:
            result.append((obj.id, str(obj.date_debut)))
        return result


    @api.multi
    def analyse_action(self):
        cr , uid, context = self.env.args
        for obj in self:
            obj.line_ids.unlink()
            lines={}


            #** Recherche des salaires *****************************************
            users = self.env['res.users'].search([('is_salaire_jour', '>', 0)])
            salaires={}
            for user in users:
                salaires[user.id]=user.is_salaire_jour
            #*******************************************************************


            #** Correspondances user => article ********************************
            users = self.env['res.users'].search([])
            user2article={}
            for user in users:
                products = self.env['product.template'].search([('is_consultant_id','=',user.id)])
                for product in products:
                    user2article[user.id]=product.id
            #*******************************************************************


            #** Correspondances sous-traite (partner) => article ***************
            products = self.env['product.template'].search([('is_type_intervenant','=','sous-traitant')])
            partner2article={}
            for product in products:
                partners = self.env['res.partner'].search([('name','=',product.name)])
                for partner in partners:
                    partner2article[partner.id]=product.id
            #*******************************************************************


            #** ca_brut_facturable et nb_jours_declares ************************
            champ = 'ia.affaire_id'
            if obj.regroupement_par=='consultant':
                champ = 'pt.id'
            SQL="""
                select """+champ+""",pt.is_consultant_id,sum(ia.total_facturable),sum(ia.nb_facturable)
                from is_activite ia inner join is_affaire_intervenant iai on ia.intervenant_id=iai.id 
                                    inner join product_product pp on iai.intervenant_id=pp.id
                                    inner join product_template pt on pp.product_tmpl_id=pt.id
                where 
                    
                    ia.date_debut>='"""+str(obj.date_debut)+"""' and
                    ia.date_debut<='"""+str(obj.date_fin)+"""' and
                    ia.active='t'
            """
            if obj.affaire_id:
                SQL=SQL+" and ia.affaire_id="""+str(obj.affaire_id.id)+" "
            SQL=SQL+"group by "+champ+",pt.is_consultant_id"
            cr.execute(SQL)
            result = cr.fetchall()
            ca_brut_facturable = 0
            nb_jours_declares  = 0
            cout_salarial      = 0
            for row in result:
                key = row[0]
                if key not in lines:
                    lines[key]={}
                    lines[key]['ca_brut_facturable'] = 0
                    lines[key]['nb_jours_declares']  = 0
                    lines[key]['cout_salarial']      = 0
                lines[key]['ca_brut_facturable'] += (row[2] or 0)
                lines[key]['nb_jours_declares']  += (row[3] or 0)
                lines[key]['cout_salarial'] += (row[3] or 0) * salaires.get(row[1],0)
            #*******************************************************************


            #** frais_a_deduire ************************************************
            champ = 'affaire_id'
            if obj.regroupement_par=='consultant':
                champ = 'createur_id'
            SQL="""
                select """+champ+""",sum(total_refacturable),sum(total_frais)
                from is_frais
                where 
                    date_creation>='"""+str(obj.date_debut)+"""' and
                    date_creation<='"""+str(obj.date_fin)+"""'
            """
            if obj.affaire_id:
                SQL=SQL+" and affaire_id="""+str(obj.affaire_id.id)+" "
            SQL=SQL+"group by "+champ
            cr.execute(SQL)
            result = cr.fetchall()
            frais_a_deduire = 0
            for row in result:
                key = row[0]
                if obj.regroupement_par=='consultant':
                    key = user2article.get(row[0])
                if key:
                    frais_a_deduire = (row[2] or 0) - (row[1] or 0)
                    if key not in lines:
                        lines[key]={}
                    lines[key]['frais_a_deduire'] = frais_a_deduire
            #*******************************************************************


            #** sous_traitance *************************************************
            champ = 'affaire_id'
            if obj.regroupement_par=='consultant':
                champ = 'sous_traitant_id'
            SQL="""
                select """+champ+""",sum(montant_ht),sum(frais)
                from is_facture_st
                where 
                    date_facture>='"""+str(obj.date_debut)+"""' and
                    date_facture<='"""+str(obj.date_fin)+"""'
            """
            if obj.affaire_id:
                SQL=SQL+" and affaire_id="""+str(obj.affaire_id.id)+" "
            SQL=SQL+"group by "+champ
            cr.execute(SQL)
            result = cr.fetchall()
            sous_traitance = 0
            for row in result:
                key = row[0]
                if obj.regroupement_par=='consultant':
                    key = partner2article.get(row[0])
                sous_traitance = row[1] or 0
                if key not in lines:
                    lines[key]={}
                if 'frais_a_deduire' not in lines[key]:
                    lines[key]['frais_a_deduire']=0
                lines[key]['frais_a_deduire']+=(row[2] or 0)
                lines[key]['sous_traitance']=sous_traitance
            #*******************************************************************


            #** ca_facture_2a *************************************************
            champ = 'ia.affaire_id'
            if obj.regroupement_par=='consultant':
                champ = 'pt.id'
            SQL="""
                select """+champ+""",sum(ail.price_subtotal),sum(ia.nb_facturable)
                from account_invoice_line ail inner join is_activite ia on ail.is_activite_id=ia.id
                                              inner join account_invoice ai on ail.invoice_id=ai.id
                                              inner join product_product  pp on ail.product_id=pp.id
                                              inner join product_template pt on pp.product_tmpl_id=pt.id
                where
                    ai.date_invoice>='"""+str(obj.date_debut)+"""' and
                    ai.date_invoice<='"""+str(obj.date_fin)+"""' and 
                    ia.active='t' and
                    ai.state not in ('cancel','draft') and
                    pt.is_type_intervenant is not null
            """
            if obj.affaire_id:
                SQL=SQL+" and affaire_id="""+str(obj.affaire_id.id)+" "
            SQL=SQL+"group by "+champ
            cr.execute(SQL)
            result = cr.fetchall()
            ca_facture_2a     = 0
            nb_jours_factures = 0
            for row in result:
                key = row[0]
                ca_facture_2a     = row[1] or 0
                nb_jours_factures = row[2] or 0
                if key not in lines:
                    lines[key]={}
                lines[key]['ca_facture_2a']     = ca_facture_2a
                lines[key]['nb_jours_factures'] = nb_jours_factures
            #*******************************************************************


            #** Création des lignes ********************************************
            for line in lines:
                mbp = lines[line].get('ca_facture_2a',0) - lines[line].get('frais_a_deduire',0) - lines[line].get('sous_traitance',0) - lines[line].get('cout_salarial',0)
                affaire_id    = False
                consultant_id = False
                if obj.regroupement_par=='affaire':
                    affaire_id = line
                if obj.regroupement_par=='consultant':
                    consultant_id = line
                vals={
                    'suivi_id'          : obj.id,
                    'affaire_id'        : affaire_id, 
                    'consultant_id'     : consultant_id, 
                    'ca_facture_2a'     : lines[line].get('ca_facture_2a',0), 
                    'ca_brut_facturable': lines[line].get('ca_brut_facturable',0), 
                    'nb_jours_declares' : lines[line].get('nb_jours_declares',0), 
                    'nb_jours_factures' : lines[line].get('nb_jours_factures',0), 
                    'frais_a_deduire'   : lines[line].get('frais_a_deduire',0), 
                    'sous_traitance'    : lines[line].get('sous_traitance',0), 
                    'cout_salarial'     : lines[line].get('cout_salarial',0), 
                    'mbp'               : mbp, 
                }
                self.env['is.suivi.production.affaire.line'].create(vals)
            #*******************************************************************

            res= {
                'name': 'Suivi de production par affaire',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'is.suivi.production.affaire.line',
                'type': 'ir.actions.act_window',
                'domain': [['suivi_id','=',obj.id]],
                'limit': 1000,
            }
            return res


class IsSuiviProductionAffaireLine(models.Model):
    _description = "Lignes suivi de production par affaire"
    _name = 'is.suivi.production.affaire.line'
    _order = 'affaire_id'
    _rec_name = 'affaire_id'


    suivi_id           = fields.Many2one('is.suivi.production.affaire', 'Suivi', required=True,index=True, ondelete='cascade')
    affaire_id         = fields.Many2one('is.affaire', 'Affaire')
    consultant_id      = fields.Many2one('product.template', 'Consultant')
    ca_brut_facturable = fields.Float("CA brut facturable (1)"        , digits=(14,2))
    ca_facture_2a      = fields.Float("CA facturé (2a)"               , digits=(14,2))
    ca_facture_2b      = fields.Float("CA facturé (2b)"               , digits=(14,2)) # TODO : Gestion des accomptes à revoir
    frais_a_deduire    = fields.Float("Frais à déduire (3)"           , digits=(14,2))
    sous_traitance     = fields.Float("Sous-Traitance (4)"            , digits=(14,2))
    cout_salarial      = fields.Float("Coût salarial brut chargé (10)", digits=(14,2))
    mbp                = fields.Float("MBP (5)"                       , digits=(14,2))
    objetif_ca_net     = fields.Float("Objectif CA net (6)"           , digits=(14,2))
    ecart_objectif     = fields.Float("Ecart Objectif (7)"            , digits=(14,2))
    nb_jours_factures  = fields.Float("Nb jours facturés (8)"         , digits=(14,2))
    nb_jours_declares  = fields.Float("Nb jours déclarés (9)"         , digits=(14,2))



