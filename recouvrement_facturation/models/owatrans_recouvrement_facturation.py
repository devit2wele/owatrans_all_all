# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, _



# ---------------------------------------------------------
# Recouvrement Facturation
# ---------------------------------------------------------
class RecouvrementFacturation(models.Model):
    _name = "owatrans.recouvrement.facturation"
    _description = "Owatrans Recouvrement Facturation"


    partner_id = fields.Many2one('res.partner', string='Client', required=True)
    date_depot = fields.Date(string='Date de dêpot')
    mode_paiement = fields.Many2one('mode.paiement', string='Mode de paiement')
    num_facture = fields.Char(string='N° Facture')
    delai = fields.Char(string='Delai')
    date_echeance = fields.Date(string='Date d\'écheance')
    currency_id = fields.Many2one('res.currency', 'Devise', required=True,\
        default=lambda self: self.env.user.company_id.currency_id.id)
    montant = fields.Monetary(string='Montant de facture', store=True)
    observation = fields.Text(string='Obeservation')

    @api.multi
    def send_mail_alert(self):
        today = datetime.now().date()

        all_orc = self.env['owatrans.recouvrement.facturation'].search([])

        for orc in all_orc:
            #Alerte Date Depot
            if orc.date_depot:
                    dt = datetime.strptime(orc.date_depot, '%Y-%m-%d').date()
                    diffenrence = today - dt
                    diffenrence_per_days = int(diffenrence.total_seconds()/86400)
                    if diffenrence_per_days == 2:
                        template = self.env.ref('recouvrement_facturation.email_template_alert_date_depot')
                        self.env['mail.template'].browse(template.id).sudo().send_mail(orc.id, force_send=True)

            #Alerte Date D'écheance
            if orc.date_echeance:
                    dt = datetime.strptime(orc.date_echeance, '%Y-%m-%d').date()
                    diffenrence = today - dt
                    diffenrence_per_days = int(diffenrence.total_seconds()/86400)
                    if diffenrence_per_days == 0:
                        template = self.env.ref('recouvrement_facturation.email_template_alert_date_echance')
                        self.env['mail.template'].browse(template.id).sudo().send_mail(orc.id, force_send=True)


class ModePaiement(models.Model):
    _name = "mode.paiement"
    _description = "Mode Paiement"

    name = fields.Char(string='Mode de Paiement')
