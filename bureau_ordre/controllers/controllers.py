# -*- coding: utf-8 -*-
from odoo import http

# class BureauOrdre(http.Controller):
#     @http.route('/bureau_ordre/bureau_ordre/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bureau_ordre/bureau_ordre/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bureau_ordre.listing', {
#             'root': '/bureau_ordre/bureau_ordre',
#             'objects': http.request.env['bureau_ordre.bureau_ordre'].search([]),
#         })

#     @http.route('/bureau_ordre/bureau_ordre/objects/<model("bureau_ordre.bureau_ordre"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bureau_ordre.object', {
#             'object': obj
#         })