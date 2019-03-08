# -*- coding: utf-8 -*-
import tempfile
import base64
import os
import xlrd
from xlrd import XLRDError
from odoo import models, fields, api, _
#from workalendar import *
from workalendar.africa import IvoryCoast as Senegal
import json
import hashlib
import base64
import time
import hmac
from hashlib import sha1
import workdays
import math
from time import gmtime, strftime
from workdays import networkdays
#from workdays import networkdays
#from workdays iImportError: No module named web_kanbanmport workday
from datetime import datetime, date, timedelta
import requests
from odoo.exceptions import Warning, ValidationError
from dateutil.relativedelta import relativedelta


class HrEmployee(models.Model):
    _name = 'hr.employee'
    _inherit = 'hr.employee'

    firstname = fields.Char(string='Prénom')
    card_number = fields.Integer(string='N° Carte', store=True)
    statut = fields.Char(string="Statut")
    categorie = fields.Many2one('owatrans_rh.categorie', string='Catégorie')
    remarques = fields.Text(string='Remarques')

class Categorie(models.Model):
    _name = 'owatrans_rh.categorie'

    name = fields.Char(string="Categorie")


class hr_contract(models.Model):
    _name = 'hr.contract'
    _inherit = 'hr.contract'
    


    @api.multi
    def send_mail_end_contract_employee(self):
        all_contracts = self.env['hr.contract'].search([])
        for contract in all_contracts:
            if contract.type_id and contract.type_id.name == 'CDD' and contract.date_end:
                date_end = datetime.strptime(contract.date_end, '%Y-%m-%d')
                if (date_end - relativedelta(months=2)).date()  == datetime.today().date():
                    # Find the e-mail template
                    template = self.env.ref('owatrans_ressources_humaines.email_template_reminder_end_contract_employee')
                    # Send out the e-mail template to the RH TEAM
                    self.env['mail.template'].browse(template.id).sudo().send_mail(contract.id)    
    

#HolidaysStaus
class hr_holidays(models.Model):
    _name = 'hr.holidays.status'
    _inherit = 'hr.holidays.status'

    delai_soumission = fields.Integer(string = "Délai de soumission(en jours)")

#Holidays
class hr_holidays(models.Model):
    _name = 'hr.holidays'
    _inherit = 'hr.holidays'

    color = fields.Integer(string = 'Color')

    max_leaves = fields.Float(compute='_compute_user_left_days', string='Maximum Allowed', help='This value is given by the sum of all holidays requests with a positive value.')
    leaves_taken = fields.Float(compute='_compute_user_left_days', string='Leaves Already Taken', help='This value is given by the sum of all holidays requests with a negative value.')
    remaining_leaves = fields.Float(compute='_compute_user_left_days', string='Remaining Leaves', help='Maximum Leaves Allowed - Leaves Already Taken')
    
    date_retraite = fields.Date(string='End Date', readonly=True, compute='_compute_date_retraite')
    
    def _compute_user_left_days(self):
        employee_id = self.env.context.get('employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1).id
        if employee_id:
            res = self.env['hr.holidays.status'].get_days(employee_id)
        else:
            res = {sid: {'max_leaves':0, 'leaves_taken':0, 'remaining_leaves':0} for sid in self.ids}
        for record in self.env['hr.holidays.status']:
            record.leaves_taken = res[record.id]['leaves_taken']
            record.remaining_leaves = res[record.id]['remaining_leaves']
            record.max_leaves = res[record.id]['max_leaves']
            if 'virtual_remaining_leaves' in res[record.id]:
                record.virtual_remaining_leaves = res[record.id]['virtual_remaining_leaves']  

    #Exclude weekends and holidays from leaves
    def _get_number_of_days(self, date_from, date_to, employee_id): 
        holidays = []
        cal =  Senegal()

        #Récupérer les dates de jours fériés validés
        jour_ferie_ids =  self.env['owatrans_rh.ferie'].search([])
        
        if jour_ferie_ids:
            for jour_ferie_id in jour_ferie_ids:
               date_ferie = self.env['owatrans_rh.ferie'].search_read([['id','=',jour_ferie_id.id]], ['date'])[0]['date']
               holidays.append(datetime.strptime(date_ferie,'%Y-%m-%d').date())
        
        dtf = datetime.strptime(date_from,'%Y-%m-%d %H:%M:%S')
        dtt = datetime.strptime(date_to,'%Y-%m-%d %H:%M:%S')
        
        year1 = str(dtf).split("-")[0]
        year2 = str(dtt).split("-")[0]
        
        for i in cal.holidays(int(year1)):
            holidays.append(i[0])
        
        if (year1 != year2): 
            for i in cal.holidays(int(year2)):
                holidays.append(i[0])

        print 'holidays', holidays
        
        diff_day = networkdays(dtf.date(), dtt.date(), holidays, (6,))
        
        return diff_day


    #Override the onchange method to call function
    @api.onchange('date_to')
    def _onchange_date_to(self):
        """ Update the number_of_days. """
        date_from = self.date_from
        date_to = self.date_to

        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise Warning(_('The start date must be anterior to the end date.'))

        super(hr_holidays, self)._onchange_date_to()


    @api.onchange('date_from')
    def _onchange_date_from(self):
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        date_from = self.date_from
        date_to = self.date_to

        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise Warning(_('The start date must be anterior to the end date.'))

        super(hr_holidays, self)._onchange_date_from()


  
    # @api.model
    # def create(self, values):
        
    #     if values.get('state') and values['state'] not in ['draft', 'confirm','validation_sup','validation_drh', 'cancel'] and not self.env.user.has_group('base.group_user'):
    #         raise Warning(_('You cannot set a leave request as \'%s\'. Contact a human resource manager.') % values.get('state'))
        
    #     return super(hr_holidays, self).create(values)

    # @api.multi
    # def write(self, vals):

    #     if vals.get('state') and vals['state'] not in ['draft', 'confirm','refuse','validation_sup','validation_drh', 'cancel'] and not self.env.user.has_group('base.group_user'):
    #         raise Warning(_('You cannot set a leave request as \'%s\'. Contact a human resource manager.') % vals.get('state'))
        
    #     return super(hr_holidays, self).write(vals)


    @api.one
    @api.constrains('date_from')
    def _check_date_from(self):
        print 'test 1', 
        today = str(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        print 'date form test', self.date_from
        if self.date_from:
             date_from = datetime.strptime((self.date_from.split(' ')[0] + " 00:00:00"), "%Y-%m-%d %H:%M:%S")
             print 'date_from', date_from
             intervalle =super(hr_holidays, self)._get_number_of_days(today, str(date_from), self.employee_id.id)
             holiday_name = self.holiday_status_id.name
             delai_soumission = self.holiday_status_id.delai_soumission
             if int(intervalle) < delai_soumission :
                #raise ValidationError("Vous ne pouvez pas soumettre une demande de %s en moins de %s jours de la date prévue de départ"%(holiday_name, delai_soumission))
                raise ValidationError("Vous ne pouvez pas soumettre une demande de ce type de congés en moins de %s jours de la date prévue de départ" % (self.holiday_status_id.delai_soumission))

    
#JoursFériesLocaux
class JourFeriesLocaux(models.Model):
    _name = 'owatrans_rh.ferie'

    name = fields.Many2one('owatrans_rh.fete_locale', string ='Intitulé', required = True)
    date = fields.Date(string='Date', required = True)
    statut = fields.Selection([('provisoire', 'Provisoire'), ('confirme', 'Confirmé'), ('revolu', 'Révolu')], readonly = True, default = 'provisoire')
    observation = fields.Char(string  = 'Observation')
    
    @api.multi
    def validate(self, values): 
        return self.write({'statut': 'confirme'})

    def revolu(self):
        confirmed_ids = []
        print ("the job is done dave")
        self._cr.execute("select id, date from owatrans_rh_ferie where statut = 'confirme'")
        jour_ferie_ids = self._cr.dictfetchall()
        for jour_ferie_id in jour_ferie_ids:
            date_ferie = datetime.strptime(jour_ferie_id['date'], "%Y-%m-%d").date()
            if date_ferie < date.today():
               self._cr.execute("UPDATE owatrans_rh_ferie SET statut = 'revolu' where id = %d"%jour_ferie_id['id'])
        return True


class Fetelocale(models.Model):
    _name = 'owatrans_rh.fete_locale'
    name = fields.Char(string  = 'Intitulé', required = True)
    type_fete = fields.Selection([('fete_religieuse', u'Fête réligieuse'), ('decret', u'Décret'), ('autre', 'Autre')])