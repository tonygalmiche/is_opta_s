# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    is_initiales = fields.Char('Initiales pour Chrono')



