# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp





class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    @api.multi
    def print_owatrans_quotation(self):
        self.write({'state': "sent"})
        return self.env['report'].get_action(self, 'supply_owatrans.report_owatranspurchasequotation')

    @api.multi
    def print_owatrans_po(self):
        return self.env['report'].get_action(self, 'supply_owatrans.report_owatranspurchaseorder')

    @api.multi
    def action_owatrans_send_rfq(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.context.get('send_rfq', False):
                template_id = ir_model_data.get_object_reference('supply_owatrans', 'email_template_edi_owatrans_purchase')[1]
            else:
                template_id = ir_model_data.get_object_reference('supply_owatrans', 'email_template_edi_owatrans_purchase_done')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'mark_rfq_as_sent': True,
        })

        # In the case of a RFQ or a PO, we want the "View..." button in line with the state of the
        # object. Therefore, we pass the model description in the context, in the language in which
        # the template is rendered.
        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_template(template.lang, ctx['default_model'], ctx['default_res_id'])

        self = self.with_context(lang=lang)
        if self.state in ['draft', 'sent']:
            ctx['model_description'] = _('Demande de Prix')
        else:
            ctx['model_description'] = _('Bon de Commande')

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    

class PurchaseOrderLine(models.Model):
    
    _inherit = 'purchase.order.line'

    


class ProductTemplate(models.Model):
    _inherit = 'product.template'


    @api.model
    def default_get(self, fields):    
        res = super(ProductTemplate, self).default_get(fields)                
        res.update({
            u'sale_ok' : False,
            u'type': u'product',
        })    
        return res



class ProductProduct(models.Model):
    _inherit = 'product.product'


class ProductCategory(models.Model):
    _inherit = "product.category"


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'