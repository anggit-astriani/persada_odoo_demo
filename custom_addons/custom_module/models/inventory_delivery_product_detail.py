from odoo import models, fields, api
from odoo.exceptions import ValidationError

class InventoryDeliveryProductDetail(models.Model):
    _name = 'inventory.delivery.product.detail'

    receipt_id = fields.Many2one('stock.picking', string='Receipt', related='receipt_code_product.receipt_id', store=True)
    delivery_id = fields.Many2one('stock.picking', string='Delivery', domain="[('picking_type_id.code','=','outgoing')]", readonly=True)
    receipt_code_product = fields.Many2one('inventory.receipt.product.detail', string='Code Product', domain="[('delivery_id','=',False), ('warehouse_id','=',warehouse_id)]", required=True)
    code_product = fields.Char('Code Product', related='receipt_code_product.code_product', store=True, readonly=True)
    allowed_product_ids = fields.Many2many(
        'product.product',
        string='Allowed Products',
        # compute='_compute_allowed_products',
        store=False,
    )
    product_id = fields.Many2one('product.product', string='Product', required=True)
    # purchase_id = fields.Many2one('purchase.order', string='Purchase Order')
    sale_id = fields.Many2one('sale.order', string='Sales Order')
    warehouse_id = fields.Many2one('stock.warehouse', string='Werehouse')
    is_returned = fields.Boolean('Is Returned', default=False, help="Indicates if this product has been returned")
    return_id = fields.Many2one('stock.picking', string='Return', domain="[('picking_type_id.code','=','incoming')]", readonly=True, compute="_compute_return_id", store=True)


    @api.onchange('delivery_id')
    def _onchange_delivery_id(self):
        """Isi sale_id dan warehouse_id otomatis saat receipt dipilih"""
        for rec in self:
            if rec.delivery_id:
                # rec.sale_id = rec.delivery_id.sale_id
                rec.warehouse_id = rec.delivery_id.picking_type_id.warehouse_id

    @api.depends('delivery_id')
    def _compute_return_id(self):
        for rec in self:
            if rec.delivery_id:
                return_pickings = self.env['stock.picking'].search([
                    ('return_id', '=', rec.delivery_id.id),
                    ('picking_type_id.code', '=', 'incoming')
                ], limit=1)
                rec.return_id = return_pickings.id if return_pickings else False
                rec.is_returned = bool(return_pickings)


    @api.model
    def create(self, vals):
        """Isi otomatis delivery_id, sale_id, dan warehouse_id saat create"""
        parent_id = vals.get('delivery_id') or self._context.get('default_delivery_id')
        if parent_id:
            picking = self.env['stock.picking'].browse(parent_id)
            if picking:
                if not vals.get('delivery_id'):
                    vals['delivery_id'] = picking.id
                # if not vals.get('sale_id') and picking.sale_id:
                #     vals['sale_id'] = picking.sale_id.id
                if not vals.get('warehouse_id') and picking.picking_type_id.warehouse_id:
                    vals['warehouse_id'] = picking.picking_type_id.warehouse_id.id

        record = super().create(vals)
        # Update delivery_id di InventoryReceiptProductDetail
        if record.delivery_id and record.receipt_code_product:
            record.receipt_code_product.delivery_id = record.delivery_id
        return record
    
    def write(self, vals):
        """Update delivery_id di receipt jika ada perubahan"""
        res = super().write(vals)
        for rec in self:
            delivery = vals.get('delivery_id') or rec.delivery_id
            receipt = vals.get('receipt_code_product') or rec.receipt_code_product
            if delivery and receipt:
                receipt.delivery_id = delivery
        return res
    
    def unlink(self):
        """Sebelum delete, reset delivery_id di receipt menjadi null"""
        for rec in self:
            if rec.receipt_code_product:
                rec.receipt_code_product.delivery_id = False
        return super().unlink()
    
    @api.onchange('product_id', 'warehouse_id')
    def _onchange_product_id(self):
        """
        Filter receipt_code_product berdasarkan product_id dan warehouse_id
        """
        domain = [('delivery_id', '=', False)]
        if self.product_id:
            domain.append(('product_id', '=', self.product_id.id))
        if self.warehouse_id:
            domain.append(('warehouse_id', '=', self.warehouse_id.id))
        return {'domain': {'receipt_code_product': domain}}

    
    # def action_return_product(self):
    #     """Open wizard untuk return product dari delivery ini"""
    #     return {
    #         'name': 'Return Product',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'inventory.return.product.wizard',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'active_id': self.delivery_id.id,
    #             'default_delivery_id': self.delivery_id.id,
    #         }
    #     }
    
    # def action_return_product(self):
    #     """Method untuk mengembalikan product ke inventory"""
    #     for rec in self:
    #         if not rec.is_returned:
    #             # Reset delivery_id pada receipt product detail agar bisa digunakan kembali
    #             if rec.receipt_code_product:
    #                 rec.receipt_code_product.write({'delivery_id': False})
                
    #             # Mark sebagai returned
    #             rec.write({'is_returned': True})
        
    #     return True