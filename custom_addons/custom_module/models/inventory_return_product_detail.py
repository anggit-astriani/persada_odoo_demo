from odoo import models, fields, api

class InventoryReturnProductDetail(models.Model):
    _name = 'inventory.return.product.detail'
    _rec_name = 'code_product'

    return_id = fields.Many2one('stock.picking', string='Return', domain="[('picking_type_id.code','=','incoming')]", required=True, readonly=True)
    original_delivery_id = fields.Many2one('stock.picking', string='Delivery', domain="[('picking_type_id.code','=','outgoing')]", required=True)
    # receipt_id = fields.Many2one('inventory.receipt.product.detail', string='Receipt', required=True)
    product_id = fields.Many2one('product.product', string='Product')
    code_product = fields.Many2one('inventory.receipt.product.detail', string='Code Product', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')

    @api.onchange('return_id')
    def _onchange_return_id(self):
        """Isi sale_id dan warehouse_id otomatis saat receipt dipilih"""
        for rec in self:
            if rec.return_id:
                # rec.sale_id = rec.delivery_id.sale_id
                rec.warehouse_id = rec.return_id.picking_type_id.warehouse_id

    def create_from_delivery_detail(self, delivery_detail_ids, return_picking_id):
        """Method untuk membuat return detail dari delivery detail"""
        return_details = []
        
        for delivery_detail_id in delivery_detail_ids:
            delivery_detail = self.env['inventory.delivery.product.detail'].browse(delivery_detail_id)
            
            # Buat return detail
            return_detail_vals = {
                'return_id': return_picking_id,
                'original_delivery_id': delivery_detail.delivery_id.id,
                'code_product': delivery_detail.receipt_code_product.id,
                'product_id': delivery_detail.product_id.id,
                'warehouse_id': delivery_detail.warehouse_id.id,
            }
            
            return_detail = self.create(return_detail_vals)
            return_details.append(return_detail.id)
            
            # Reset delivery_id pada receipt product detail
            if delivery_detail.receipt_code_product:
                delivery_detail.receipt_code_product.write({'delivery_id': False})
            
            # Mark delivery detail sebagai returned
            delivery_detail.write({
                'is_returned': True,
                'return_id': return_picking_id
            })
        
        return return_details
    