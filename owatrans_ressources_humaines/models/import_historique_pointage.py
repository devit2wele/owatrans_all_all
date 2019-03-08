# -*- coding: utf-8 -*-
from datetime import datetime
import base64
import xlrd

from odoo import models, _,fields, api, exceptions
from odoo.exceptions import UserError, ValidationError
from datetime import date
from odoo import tools
from odoo.exceptions import UserError


STATES = [
    ('draft', 'Brouillon'),
    ('confirmer', 'Importé'),
    ('annuler', 'Annulé'),
]

TYPE_POINTAGE = [
    ('RECEPTION', 'Réception'),
]

CORRESPONDANCE = {
    0 : 'date_heure',
    1 : 'type_pointage',
    2 : 'card_number',
}


from xlrd import open_workbook


class ImportHistoriquePointage(models.Model):
    _name = 'owatrans.import.historique.pointage'
    _description = 'IMPORT Historique Pointage'

    @api.onchange('data')
    def import_pointage_manuel_template(self):
        pointage_manuels = []
        if self.data:
            file_data = self.data.decode('base64')
            wb = open_workbook(file_contents=file_data)
            sh = wb.sheet_by_index(0)
            for i in range(sh.nrows):
                if i == 0:
                    continue
                line = {
                    'date_heure': sh.cell_value(rowx=i, colx=0),
                    'type_pointage': sh.cell_value(rowx=i, colx=1),
                    'card_number': int(sh.cell_value(rowx=i, colx=2)),
                }
                if type(line['date_heure']) == float:
                    serial = float(line['date_heure'])
                    seconds = (serial - 25569) * 86400.0
                    line['date_heure'] = str(datetime.utcfromtimestamp(seconds))
                pointage_manuels.append((0, 0, line))
            self.historique_pointage_line = pointage_manuels


    name = fields.Char(string="Titre", required=True)
    description = fields.Text()
    datetime = fields.Datetime(readonly=True, string='Date import')
    nombre_de_lignes_importes = fields.Integer(readonly=True)
    user_import = fields.Many2one('res.users', string="User", readonly=True)
    state = fields.Selection(STATES, default='draft', readonly=True)

    filename = fields.Char('File Name')
    data = fields.Binary('Import PO')

    historique_pointage_line = fields.One2many('pointage.manuel.template', 'pointage_manuel_id', string='Historique Pointage', required=True)

    @api.model
    def default_get(self, fields):    
        res = super(ImportHistoriquePointage, self).default_get(fields)        
        if 'user_import' in fields:        
            res.update({
                'user_import' : self.env.user.id,

            })    
        return res

    @api.multi
    def clear_line(self):
        self.historique_pointage_line = False
        self.data = False


    @api.multi
    def action_confirmer(self):
        
        if not self.historique_pointage_line:
            raise UserError(_("(re)charger le fichier d'import"))
        
        else:
            pointage_manuel = {}
            nombre_de_lignes_importes = 0
            self.datetime = datetime.today()
            for line in self.historique_pointage_line:
                if line.card_number:
                    pointage_manuel = {
                        'card_number': line.card_number,
                        'employee': line.employee.id,
                        'date_heure': line.date_heure,
                        'type_pointage': line.type_pointage,
                        'datetime_import': self.datetime,
                    }

                    pointage_manuel = self.env['pointage.manuel'].create(pointage_manuel)
                    nombre_de_lignes_importes += 1
            
            self.nombre_de_lignes_importes = nombre_de_lignes_importes
            self.state = 'confirmer'
    
    @api.multi
    def action_annuler(self):
        self.state = 'annuler'

    @api.multi
    def action_reset_to_draft(self):
        self.state = 'draft'


    @api.multi
    def action_roll_back(self):
        if self.datetime:
            self.env['pointage.manuel'].search([('datetime_import', '=',self.datetime)]).unlink()
            self.state = 'draft'
        else:
            raise UserError(_("Roll back échoué"))

    @api.multi
    def unlink(self):
        if self.state != 'draft':
            raise UserError(_('Peut pas supprimer un import en état %s.')% self.state)
        return super(ImportHistoriquePointage, self).unlink()

    
class PointageManuelTemplate(models.Model):
    
    _name = 'pointage.manuel.template'
    _description = 'Pointage Manuel Template'
    
    employee = fields.Many2one('hr.employee', string='Employee', required=True, compute='_compute_employee')
    card_number = fields.Integer(string='N° Carte', store=True, required=True)
    type_pointage = fields.Selection(TYPE_POINTAGE, string='Type de pointage', defaut='reception', required=True)
    date_heure = fields.Datetime(string='Date heure', required=True)

    pointage_manuel_id = fields.Many2one('owatrans.import.historique.pointage', string='Pointage Manuel')

    @api.one
    @api.depends('card_number')
    def _compute_employee(self):
        if self.card_number:
            self.employee = self.env['hr.employee'].search([('card_number', '=', int(self.card_number))], limit=1)