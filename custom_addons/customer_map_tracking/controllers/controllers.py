# -*- coding: utf-8 -*-
# from odoo import http


# class CustomerMapTracking(http.Controller):
#     @http.route('/customer_map_tracking/customer_map_tracking', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/customer_map_tracking/customer_map_tracking/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('customer_map_tracking.listing', {
#             'root': '/customer_map_tracking/customer_map_tracking',
#             'objects': http.request.env['customer_map_tracking.customer_map_tracking'].search([]),
#         })

#     @http.route('/customer_map_tracking/customer_map_tracking/objects/<model("customer_map_tracking.customer_map_tracking"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('customer_map_tracking.object', {
#             'object': obj
#         })

