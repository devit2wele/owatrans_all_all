# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

STATUS = [
			('draft','En brouillon'),
			('confirm',"Confirmé"),
			('impute' , 'Imputé'),
			('traite' , 'Traité'),
			#('rejete',"Rejeté"),
			#('termine',"Terminé"),
			#('a_traiter','A traiter'),
			#('a_corriger','A corriger'),
			#('imputation_executee' , 'Imputation exécutée'),
		 ]
CONFIDENTIALITE = [
					('confidentiel','Confidentiel'),
					('public','Public'),
					('secret','Secret'),
					('restreint','Restreint'),
				  ]
TYPE_EXPEDITEUR = [ 
					('administration_publique','Administration publique'),
					('entreprise_privee','Entreprise privée'),
					('particulier','Particulier'),
				  ]

NIVEAU_PRIORITE = [
					('normal','Normal'),
					('urgent','Urgent'),
					('faible','Faible'),
					('tres_urgent','Très urgent'),
				  ]

ETAT = [
			('a_imputer',"A imputer"),
			('a_traiter',"A traiter"),
			('a_corriger',"A corriger"),
			#('impute',"imputé"),
	   ]

TRAITEMENT = [
				('accepte',"Accepté"),
				('non_accepte',"Non accepté"),
				('re_impute',"Reimputer"),
			 ]
CONTROLE = [
				('accepte',"Accepté"),
				('rejete',"Rejeté"),
		   ]

class OwatransNatureCourrier(models.Model):
	_name = 'owatrans.nature.courrier'
	name = fields.Char()

class OwatransCourrierArrive(models.Model):
	_name = 'owatrans.courrier.arrive'
	_rec_name = 'numero_ordre'
	nature_courrier = fields.Many2one('owatrans.nature.courrier' , string='Nature du courrier' , required = True)
	type_expediteur = fields.Selection(TYPE_EXPEDITEUR,"Type d'expéditeur",default='administration_publique' , required = True)
	expediteur = fields.Many2one('res.partner' , string = 'Expéditeur' , required = True)
	objet_courrier = fields.Text('Objet du courrier' , required = True)
	degre_confidentialite = fields.Selection(CONFIDENTIALITE,"Degré de confidentialité",default='public')
	niveau_priorite = fields.Selection(NIVEAU_PRIORITE,"Niveau de priorité",default='normal')
	date_enregistrement = fields.Date("Date d'enregistrement du courrier",default=fields.Date.context_today)
	date_du_courrier = fields.Date("Date du courrier" , required = True)
	date_de_reception = fields.Date("Date de reception du courrier" , required = True)
	numero_ordre = fields.Char(string = "Numéro d'ordre")
	files = fields.Many2many('ir.attachment',string='Joindre des fichiers')
	destinataire_interne = fields.Many2one('hr.department',string='Destinataire interne' , required = True)
	state = fields.Selection(STATUS,'Etat',default="draft" , readonly=True)
	imputations_ids = fields.One2many('owatrans.imputations','courrier_arrive_id',"Imputations")
	enregistre_par = fields.Many2one('hr.employee' , string = "Enregistré par")
	

	@api.model
	def default_get(self,fields):
		res = super(OwatransCourrierArrive , self).default_get(fields)
		current_user = self.env['hr.employee']\
						   .search([
						   			('user_id','=',self.env.user.id),
						   			] , limit = 1)
		res.update({
						'enregistre_par':current_user.id,
			})

		return res


	@api.model
	def create(self,vals):
		vals['numero_ordre'] = self.env['ir.sequence'].next_by_code('owatrans.courrier.arrive')
		return super(OwatransCourrierArrive,self).create(vals)

	@api.multi
	def confirm(self):
		for record in self:
			record.state = 'confirm'

	@api.multi
	def annuler(self):
		for record in self:
			if record.state == 'confirm':
				record.state = 'draft'
			if record.state == 'impute':
				record.state = 'confirm'

	@api.multi
	def imputer(self):
		for record in self:
			if not record.imputations_ids:
				raise UserError(_("Veuillez cliquer sur modifier d'abord et imputer le courrier à au moins un agent"))
			else:
				for line in record.imputations_ids:
					line.write({'state':'impute'})
			record.state = 'impute'

		res = self.env['ir.actions.act_window'].for_xml_id('bureau_ordre','action_enregistre_courrier')
		return res

	@api.multi
	def executer(self):
		for record in self:
			record.state = 'traite'
			




class OwatransTypeImputation(models.Model):
	_name = 'owatrans.type_imputation'
	name = fields.Char()

class OwatransImputations(models.Model):
	_name = 'owatrans.imputations'
	name = fields.Char()
	type_imputation = fields.Many2one('owatrans.type_imputation' , string = "Type d'imputation" ,required = True)
	numero_ordre = fields.Char(string = "Numéro d'ordre")
	#date_limite = fields.Date(string = "Date limite")
	#heure_limite = fields.Char(string = "Heure limite")
	date_heure_debut = fields.Datetime(default=fields.Date.context_today)
	date_heure_limite = fields.Datetime(string = "Date et heure limite" ,required = True)
	impute_a = fields.Many2one('hr.employee' , string = "Imputé à", required = True  )
	impute_par = fields.Many2one('hr.employee' , string = "Imputé par ")
	#enregistre_par = fields.Many2one('hr.employee' , string = "Enregistré par")
	#state = fields.Selection(STATUS , 'status' , default = 'draft' , readonly = True)
	state = fields.Selection(ETAT , 'status' , default = 'a_traiter' , readonly = True)
	files = fields.Many2many('ir.attachment' , string = 'Joindre des fichiers')
	#pieces_justificatifs = fields.Many2many('ir.attachment' ,string = 'Joindre des fichiers')
	description = fields.Text(string = "Explication sur l'imputation " , size=1024)
	courrier_arrive_id = fields.Many2one('owatrans.courrier.arrive',"Courrier d'arrivé" , ondelete="cascade" , readonly=True)
	
	#----------------------------------
	nature_courrier = fields.Many2one('owatrans.nature.courrier' , string='Nature du courrier')
	type_expediteur = fields.Selection(TYPE_EXPEDITEUR,"Type d'expéditeur",default='administration_publique')
	expediteur = fields.Many2one('res.partner' , string = 'Expéditeur')
	objet_courrier = fields.Text('Objet du courrier')
	degre_confidentialite = fields.Selection(CONFIDENTIALITE,"Degré de confidentialité",default='public')
	niveau_priorite = fields.Selection(NIVEAU_PRIORITE,"Niveau de priorité",default='normal')
	date_enregistrement = fields.Date("Date d'enregistrement du courrier",default=fields.Date.context_today)
	date_du_courrier = fields.Date("Date du courrier")
	date_de_reception = fields.Date("Date de reception du courrier")
	files = fields.Many2many('ir.attachment',string='Joindre des fichiers')
	destinataire_interne = fields.Many2one('hr.department',string='Destinataire interne')
	#---------------------------Execution de l'imputation----------------------------
	explication_sur_execution = fields.Text(string = "Explication sur l'exécution de l'imputation" , size=1024)
	files_execution = fields.Many2many('ir.attachment',string='Joindre des fichiers')

	#----------------------Controle----------------------------------------#
	controle = fields.Selection(CONTROLE,"Acceptation du traitement de l'imputation",default='accepte')
	motif_rejet = fields.Text(string="Motif du rejet")


	@api.model
	def default_get(self,fields):
		res = super(OwatransImputations , self).default_get(fields)
		current_user = self.env['hr.employee']\
						   .search([
						   			('user_id','=',self.env.user.id),
						   			] , limit = 1)
		res.update({
						'impute_par':current_user.id,
			})

		return res

	@api.model
	def create(self,vals):
		courrier = self.env['owatrans.courrier.arrive'].browse(vals['courrier_arrive_id'])
		vals['numero_ordre'] = courrier.numero_ordre
		vals['nature_courrier'] = courrier.nature_courrier.id
		vals['type_expediteur'] = courrier.type_expediteur
		vals['expediteur'] = courrier.expediteur.id
		vals['objet_courrier'] = courrier.objet_courrier
		vals['degre_confidentialite'] = courrier.degre_confidentialite
		vals['niveau_priorite'] = courrier.niveau_priorite
		vals['date_enregistrement'] = courrier.date_enregistrement
		vals['date_du_courrier'] = courrier.date_du_courrier
		vals['date_de_reception'] = courrier.date_de_reception
		vals['files'] = courrier.files
		vals['destinataire_interne'] = courrier.destinataire_interne.id
		#vals['numero_ordre'] = self.env['ir.sequence'].next_by_code('owatrans.imputations')
		"""if not vals['type_imputation']:
			raise UserError(_("Veuillez selectionner le type d'imputation."))
		if not vals['impute_a']:
			raise UserError(_("Veuillez renseigner la personne qui doit exécuter l'imputation."))
		if not vals['date_heure_limite']:
			raise UserError(_("Veuillez renseigner la date et l'heure limite pour l'exécution de l'imputation."))"""
		return super(OwatransImputations,self).create(vals)

	"""@api.multi
	def write(self,vals):
		for record in self:
			if vals['controle'] == 'rejete':"""



	"""@api.multi
	def annuler(self):
		for record in self:
			if record.state == 'confirm':
				record.state = 'draft'
			if record.state == 'impute':
				record.state = 'confirm'"""
	
	"""@api.multi
	def confirmer(self):
		for record in self:
			record.state = 'confirm'
		#return self.write({'status':'confirm'})"""

	@api.multi
	def imputer(self):
		for record in self:
			if not record.type_imputation:
				raise UserError(_("Veuillez selectionner le type d'imputation."))
			if not record.impute_a:
				raise UserError(_("Veuillez renseigner la personne qui doit exécuter l'imputation."))
			if not record.date_heure_limite:
				raise UserError(_("Veuillez renseigner la date et l'heure limite pour l'exécution de l'imputation."))
			record.state = 'impute'

			"""current_user = self.env['hr.employee']\
							   .search([('user_id','=',self.env.user.id),],limit = 1)"""
		#return self.write({'impute_par':current_user.id})

	@api.multi
	def executer(self):
		for record in self:
			record.state = 'traite'
			record.courrier_arrive_id.state = 'traite'
		#return self.write({'status':'imputation_executee'})

	#def imputation_annuler(self,cr,uid,ids,context=None):

"""class OwatransExpediteur(models.Model):
	_name = "owatrans.expediteur"
	_inherit = "res.partner" 
	"""