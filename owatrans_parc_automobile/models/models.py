# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo.exceptions import Warning, ValidationError
from datetime import datetime , timedelta
from dateutil.relativedelta import relativedelta

STATE = [
			('open', 'En cours'), 
			('toclose', 'A cloturer'), 
			('closed', 'Terminé')
		]


class TypeMacaron(models.Model):
	_name = 'owatrans.type_macaron'
	name = fields.Char(string="Type macaron")


class Macaron(models.Model):
	_name = 'owatrans.macaron'
	_inherits = {'fleet.vehicle.cost': 'cost_id'}
	name = fields.Char()
	type_macaron = fields.Many2one('owatrans.type_macaron',ondelete='cascade',string='Type macaron')
	date_creation = fields.Date(string = "Fait le" , required = True ,  default=fields.Date.context_today)
	date_expiration = fields.Date(string = "Expire le" ,required = True)
	reference = fields.Char(string = "Référence")
	libelle = fields.Char(string = "Libellé")
	#vehicule_attribue = fields.Many2one('fleet.vehicle' ,string = 'Véhicule')
	state = fields.Selection(STATE,
                              'Status', default='open', readonly=True, help='etat du macaron ',
                              copy=False)
	days_left = fields.Integer(compute='_compute_days_left',string="Warning date")
	#montant = fields.Float(string="Montant en (FCFA)")
	cost_id = fields.Many2one('fleet.vehicle.cost', 'Cost', required=True, ondelete='cascade')
	cost_amount = fields.Float(related='cost_id.amount', string='Amount', store=True)


	@api.onchange('date_creation','date_expiration')
	def _onchange_creation_date(self):
		date_creation = self.date_creation
		date_expiration = self.date_expiration
		if(date_creation and date_expiration) and (date_creation > date_expiration):
			self.date_expiration = ""
			raise Warning(_("la date de création doit etre antérieure à la date d'expiration "))

	


	"""@api.model
	def create(self,vals):
		start_date = fields.Date.from_string(vals['date_creation'])
		end_date = fields.Date.from_string(vals['date_expiration'])
		if end_date <= start_date:
			raise UserError(_("La date d'expiration saisie n'est pas valide "))
		return super(Macaron,self).create(vals)
    """
    
	"""@api.multi
	def write(self,vals):
		if vals.has_key('date_creation') and vals.has_key('date_expiration'):
			start_date = fields.Date.from_string(vals['date_creation'])
			end_date = fields.Date.from_string(vals['date_expiration'])
			if end_date <= start_date : 
				raise UserError(_("la date d'expiration saisie n'est pas valide"))
			return super(Macaron,self).write(vals)"""
    

	@api.multi
	def cloturer(self):
		for record in self:
			record.state = 'closed'


	@api.multi
	def renouveler_macaron(self):
		assert len(self.ids) == 1, "cette operation ne pourra etre execute pour un seul macaron a la fois"
		for record in self:
			start_date = fields.Date.from_string(record.date_creation)
			end_date = fields.Date.from_string(record.date_expiration)
			diff_date = (end_date - start_date)
			default = {
						'date_creation': fields.Date.to_string(end_date + relativedelta(days=1)),
						'date_expiration' : fields.Date.to_string(end_date + diff_date),
			}
			new_id = record.copy(default).id
			return {
					'name':_("Renouveler le contrat des macaronss"),
					'view_mode': 'form',
					'view_id': self.env.ref('owatrans_parc_automobile.owatrans_macaron_view_form').id,
					'view_type': 'tree , form ',
					'res_model': 'owatrans.macaron',
					'type' :'ir.actions.act_window',
					'domain': '[]',
					'res_id': new_id,
					'context':{'active_id':new_id},
			}



	
	@api.depends('date_expiration','state')
	def _compute_days_left(self):
		"""retourne un dictionnaire d'entiers dont chaque entier correspond a letat d'un macaron
		si le macaron a pour state open et que la date expiration est inferieure ou egal la date actuelle on retourne 0
		si le state du macaron est closed retourne -1 
		sinon retourner le nbre de jours avant lexpiration du macaron"""
		for record in self:
			if (record.date_expiration and (record.state == 'open' or record.state == 'toclose')):
				today = fields.Date.from_string(fields.Date.today())
				renew_date = fields.Date.from_string(record.date_expiration)
				diff_time = (renew_date - today).days
				record.days_left = diff_time > 0 and diff_time or 0
			else:
				record.days_left = -1

	def send_email(self,subject,email_to,message):

		values = {
					'subject': subject,
					'body_html': message,
					'email_to': email_to,

		}
		mail_obj = self.env['mail.mail']
		msg_id = mail_obj.create(values)
		if msg_id:
			mail_obj.send([msg_id])
		return True


	@api.model
	def scheduler_manage_macaron_expiration(self):
		# cette methode est appele par un cron 
		# elle gere l'expiration des macarons avec la possibilite d'envoyer un message 30 jous avant l'expiration
		date_today = fields.Date.from_string(fields.Date.context_today(self))
		print date_today
		date_limite = fields.Date.to_string(date_today + relativedelta(days=+30))
		#date_limite = fields.Date.from_string()
		macarons = self.search([('state', '=', 'open'),('date_expiration','<',date_limite)])
		users = self.env['res.users'].search([('active','=',True)])
		#Vehicule = self.env['fleet.vehicle']
		message = ""
		if macarons:
			for user in users:
				if user.has_group('hr.group_hr_manager'):
					for macaron in macarons:
						#print macaron.vehicule_attribue.name
						print macaron.vehicle_id.name

						#nb days
						nb_days = (fields.Date.from_string(macaron.date_expiration) - date_today).days
						if nb_days > 0 :	
							message += macaron.type_macaron.name+ " de la voiture d'immatriculation "+ macaron.vehicle_id.license_plate+" expire dans "+str(nb_days)+" jours \n"
							print message
					if message :
						self.send_email("Alerte",user.partner_id.email,message)
						return macarons.write({'state': 'toclose'})
					return True


	@api.model 
	def run_scheduler(self):
		self.scheduler_manage_macaron_expiration()

Macaron()


class Vehicule(models.Model):
	_name="fleet.vehicle"
	_inherit = "fleet.vehicle"
	status = fields.Selection([
							  ('disponible',"disponible"),
							  ('en_mission',"en mission"),
							  ('en_panne',"en panne"),
							  ('reserve',"réservé")
							  ], string="Disponibilé" , default="disponible")


"""class fleet_inventaire(models.Model):
	_name = "fleet.inventaire"
	cout = fields.Float(string = "cout")
	date = fields.Datetime(string = "Date")
	description = fields.Char(string = "Description")
	vehicule = fields.Many2one("fleet.vehicle")"""


"""class fleet_prevision_maintenance(models.Model):
	_name = "fleet.prevision_maintenance"
	date = fields.Date(string = "Date")
	description = fields.Char(string = "Description")"""


"""class fleet_bon_essence(models.Model):
	_name = "fleet.bon_essence"
	prix_unitaire = fields.Float(string="prix unitaire")
	quantite = fields.Float(string = "quantité")"""

class CoordonneesGps(models.Model):
	_name = "owatrans.gps"
	name = fields.Char()
	latitude = fields.Float(string="Latitue")
	longitude = fields.Float(String="Longitude")

CoordonneesGps()


class MaintenanceVehicule(models.Model):
	_name = 'owatrans.maintenance.vehicule'
	_inherit = 'fleet.vehicle.log.services'
	name = fields.Char()

MaintenanceVehicule()

class ReservationVehicule(models.Model):
	_name="owatrans.reservation"
	vehicule = fields.Many2one('fleet.vehicle',string="Vehicule")
	chauffeur = fields.Many2one('hr.employee',string="Chauffeur",ondelete='cascade')
	date_debut = fields.Datetime("date de debut" ,required = True , default=fields.Date.context_today)
	date_fin = fields.Datetime("date de fin")
	state = fields.Selection([
								('draft',"Brouillon"),
								('done',"Terminée")] , string="Etat",default="draft")
	#accompagnateur = 


	@api.multi
	def reserver(self):
		for record in self:
			record.state = 'done'
			record.vehicule.write({'state':'reserve'})
			#update vehicule and chauffeur state

	@api.multi 
	def annuler(self):
		for record in self:
			record.state = 'draft'
			record.vehicule.write({'state':'disponible'})
  


ReservationVehicule()

class ObjectifMission(models.Model):
	_name ="owatrans.objectif.mission"
	name = fields.Char("Libellé")

class Mission(models.Model):
	_name="owatrans.mission"
	numero_mission = fields.Char("Numero de la mission")
	vehicule = fields.Many2one('fleet.vehicle',string="Vehicule diponible",ondelete='cascade' , domain="[('status','=','disponible')]")
	objectif = fields.Many2one('owatrans.objectif.mission')#fields.Char("Objectif")
	date_debut = fields.Datetime("Date de debut" , required = True ,default=fields.Date.context_today)
	date_fin = fields.Datetime("Date de fin")
	chauffeur = fields.Many2one("hr.employee",string="Chauffeur disponible" ,ondelete='cascade')
	#accompagnateur_ids = fields.One2many('hr.employee','accompagnateur')
	kilo_depart = fields.Float(string="Kilométrage de départ")
	kilo_retour = fields.Float(string="Kilométrage de retour")
	lieu_depart = fields.Char(string="Lieu de départ")
	lieu_arrive = fields.Char(string="Lieu d'arrivé")
	temps_parcouru = fields.Char(string="Temps parcourus dans la mission" , compute='_compute_temps_parcouru',store=True)
	kilo_parcouru =  fields.Char(string = "Kilometrage parcourus dans la mission" ,compute='_compute_kilo_parcouru')
	state = fields.Selection([
							 ('open',"Brouillon"),
							 ('in_progress',"En cours"),
							 ('done',"Terminée")
							 ], string="Etat", default='open')
	trajet = fields.Text(string="Trajet")
	#equipe_mission = fields.One2many('owatrans.missionnaire','missionnaire_id','Equipe de la mission')
	#lettre_mission = fields.Many2many('ir.attachment' ,string="Joindre la lettre de mission")

	"""@api.onchange('kilo_retour')
	def _onchange_kilo_retour(self):
		self.env['fleet.vehicle']"""

	@api.model
	def create(self,vals):
		vals['numero_mission'] = self.env['ir.sequence'].next_by_code('owatrans.mission')
		"""self.env['owatrans.reservation'].create({
			'vehicule':vals['vehicule'],
			'chauffeur':vals['chauffeur'],
			'date_debut':vals['date_debut'],
			'date_fin':vals['date_fin']
			})"""
		return super(Mission,self).create(vals)


	@api.multi
	def write(self,vals):
		return super(Mission,self).write(vals)

	@api.onchange('kilo_depart','kilo_retour','kilo_parcouru')
	def _onchange_kilo_depart_retour_parcouru(self):
		kilo_depart = float(self.kilo_depart)
		kilo_retour = float(self.kilo_retour)
		kilo_parcouru = float(self.kilo_parcouru)
		if(kilo_depart and kilo_retour) and (kilo_depart > kilo_retour):
			Warning(_("le kilomètrage de départ ne doit pas etre supérieur au kilomètrage d'arrivée"))
		elif kilo_depart > 0 and kilo_retour > 0 and (kilo_retour - kilo_depart) != kilo_parcouru:
			self.kilo_parcouru = kilo_retour - kilo_depart
		elif kilo_parcouru > 0 and kilo_depart > 0 and (kilo_parcouru + kilo_depart) != kilo_retour:
			self.kilo_retour = kilo_parcouru + kilo_depart
		elif kilo_parcouru > 0 and kilo_retour > 0 and (kilo_retour - kilo_parcouru) != kilo_depart:
			self.kilo_depart = kilo_retour - kilo_parcouru 

	@api.depends('date_debut','date_fin')
	def _compute_temps_parcouru(self):
		FORMAT = '%Y-%m-%d %H:%M:%S'
		date_debut , heure_debut = self.date_debut.split(' ')[0] , self.date_debut.split(' ')[1]
		if self.date_fin:
			date_fin , heure_fin = self.date_fin.split(' ')[0] , self.date_fin.split(' ')[1]
			duree_mission = datetime.strptime(self.date_fin , FORMAT) - datetime.strptime(self.date_debut,FORMAT)
			#duree_mission is a timedelta after this substraction
			days , seconds = duree_mission.days , duree_mission.seconds
			hours , seconds = seconds / 3600 , seconds % 3600
			minutes , seconds = seconds / 60 , seconds % 60 
			#raise UserError(_(str(str(days) + ' ' + str(seconds))))
			self.temps_parcouru = " %d Jours %d Heures %d Minutes %d Secondes " %(days,hours,minutes,seconds)
			


	@api.depends('kilo_depart','kilo_retour')
	def _compute_kilo_parcouru(self):
		if self.kilo_depart and self.kilo_retour:
			self.kilo_parcouru = self.kilo_retour - self.kilo_depart

		



	"""@api.model
	def create(self,vals):
		#v={}
		#v['date_debut'] = vals['date_debut']
		#v['date_fin'] = vals['date_fin']
		#v['vehicule'] = vals['vehicule']
		#v['chauffeur'] = vals['chauffeur']
		#v['state'] = 'draft'
		#vehicule = self.env['fleet.vehicle'].browse(vals['vehicule'])
		#vehicule.write({'status':'en_mission'})
		#self.env['owatrans.reservation'].create(v)
		#vals['status'] = 'disponible'
		return super(Mission,self).create(vals)"""

	@api.multi
	def write(self,vals):
		if vals.has_key('kilo_retour') and vals['kilo_retour']:
			self.vehicule.write({'odometer' : vals['kilo_retour']})
		return super(Mission, self).write(vals)


	@api.multi
	def commencer(self):
		for record in self:
			record.state = 'in_progress'
			record.chauffeur.write({'status':'indisponible'})
			record.vehicule.write({'status' :'en_mission'})

	@api.multi
	def terminer(self):
		for record in self:
			record.state = 'done'
			record.vehicule.write({'status' :'disponible'})
			record.chauffeur.write({'status' :'disponible'})
			#record.vehicule.status='disponible'
	@api.multi
	def annuler(self):
		for record in self:
			record.state='open'
			record.vehicule.write({'status':'disponible'})
			record.chauffeur.write({'status':'disponible'})


class Employee(models.Model):
	_name="hr.employee"
	_inherit = "hr.employee"
	status = fields.Selection([
							  ('disponible',"Disponible"),
							  ('indisponible',"Indisponible")
							  ],string = "Disponibilité", default="disponible")
	#missionnaire_id = fields.Many2one('owatrans.mission', string='missionnaire',ondelete='cascade')
	est_chauffeur = fields.Selection([('oui',"OUI"),('non',"NON")],string="Est -il chauffeur ?", default="non")
	numero_permis = fields.Char('Numero permis', size=128)
	type_permis = fields.Char('Type permis')
	date_expiration_permis = fields.Date(string = "Date d'expiration du permis")
	#accompagnateur = fields.Many2one('hr.employee', string="")

"""class Missionnaire(models.Model):
	_name = 'owatrans.missionnaire'
	missionnaire_id = fields.Many2one('hr.employee',string="missionnaire" , ondelete='cascade')
	lettre_mission = fields.Many2many('ir.attachment' ,string="Joindre la lettre de mission")"""