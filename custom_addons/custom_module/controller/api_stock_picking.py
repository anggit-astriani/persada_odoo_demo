from odoo import http
from odoo.http import request, Response
import json

class ApiStockPicking(http.Controller):

    @http.route('/api/delivery_orders', type='http', auth='none', methods=['GET'], csrf=False)
    def get_delivery_orders(self, **kwargs):
        """
        GET /api/delivery_orders
        """
        # Ambil semua stock.picking dengan operation type Delivery Orders
        # (bisa disesuaikan domainnya)
        domain = [
            ('picking_type_id.name', '=', 'Delivery Orders')  # filter sesuai operation type
        ]
        pickings = request.env['stock.picking'].sudo().search(domain)

        results = []
        for picking in pickings:
            results.append({
                'id': picking.id,
                'reference': picking.name,  # Saka/OUT/xxxx
                'from_location': picking.location_id.display_name,  # Saka/Stock
                'to_location': picking.location_dest_id.display_name,  # Partner/Customer
                'contact': picking.partner_id.display_name,  # Deco Addict / Azure Interior
                'scheduled_date': picking.scheduled_date.strftime('%Y-%m-%d %H:%M:%S') if picking.scheduled_date else None,
                'source_document': picking.origin,  # Return of Saka/IN/xxx
                'company': picking.company_id.name,  # Saka Sakti Inovasi
                'status': picking.state,  # draft / waiting / done / etc
            })

        headers = [('Content-Type', 'application/json')]
        return Response(json.dumps({'data': results}), headers=headers)