from odoo import models, fields, api

class InventoryReceiptProductDetail(models.Model):
    _name = 'inventory.receipt.product.detail'
    _rec_name = 'code_product'

    receipt_id = fields.Many2one('stock.picking', string='Receipt', domain="[('picking_type_id.code','=','incoming')]")
    code_product = fields.Char('Code Product', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    purchase_id = fields.Many2one('purchase.order', string='Purchase Order')
    warehouse_id = fields.Many2one('stock.warehouse', string='Werehouse')
    delivery_id = fields.Many2one('stock.picking', string='Delivery', domain="[('picking_type_id.code','=','outgoing')]")

    @api.onchange('receipt_id')
    def _onchange_receipt_id(self):
        """Isi header & domain produk yg benar-benar ada di receipt"""
        if self.receipt_id:
            self.purchase_id = self.receipt_id.purchase_id
            self.warehouse_id = self.receipt_id.picking_type_id.warehouse_id
            # ambil produk yg muncul di move.line (hasil scan / detailed op)
            products = self.receipt_id.move_ids_without_package.product_id
            return {'domain': {'product_id': [('id', 'in', products.ids)]}}

    @api.model
    def create(self, vals):
        """Isi otomatis receipt_id, purchase_id, dan warehouse_id saat create"""
        parent_id = vals.get('receipt_id') or self._context.get('default_receipt_id')
        if parent_id:
            picking = self.env['stock.picking'].browse(parent_id)
            if picking:
                if not vals.get('receipt_id'):
                    vals['receipt_id'] = picking.id
                if not vals.get('purchase_id') and picking.purchase_id:
                    vals['purchase_id'] = picking.purchase_id.id
                if not vals.get('warehouse_id') and picking.picking_type_id.warehouse_id:
                    vals['warehouse_id'] = picking.picking_type_id.warehouse_id.id

        return super().create(vals)