from odoo import models, fields, api
from odoo.exceptions import ValidationError

class InventoryDeliveryProductDetail(models.Model):
    _name = 'inventory.delivery.product.detail'  # Model untuk detail produk saat delivery

    receipt_id = fields.Many2one(
        'stock.picking',
        string='Receipt',
        related='receipt_code_product.receipt_id',  # Otomatis ambil receipt dari code product
        store=True
    )
    delivery_id = fields.Many2one(
        'stock.picking',
        string='Delivery',
        domain="[('picking_type_id.code','=','outgoing')]",  # Hanya picking outgoing
        readonly=True
    )
    receipt_code_product = fields.Many2one(
        'inventory.receipt.product.detail',
        string='Code Product',
        domain="[('delivery_id','=',False), ('warehouse_id','=',warehouse_id)]",
        required=True
    )
    code_product = fields.Char(
        'Code Product',
        related='receipt_code_product.code_product',  # Ambil kode dari receipt_code_product
        store=True,
        readonly=True
    )
    allowed_product_ids = fields.Many2many(
        'product.product',
        string='Allowed Products',
        # compute='_compute_allowed_products',  # bisa digunakan untuk compute
        store=False,
    )
    product_id = fields.Many2one('product.product', string='Product', required=True)  # Produk yang dikirim
    sale_id = fields.Many2one('sale.order', string='Sales Order')  # Sales order terkait (opsional)
    warehouse_id = fields.Many2one('stock.warehouse', string='Werehouse')  # Warehouse asal
    is_returned = fields.Boolean(
        'Is Returned',
        default=False,
        help="Indicates if this product has been returned"  # Flag jika produk sudah di-return
    )
    return_id = fields.Many2one(
        'stock.picking',
        string='Return',
        domain="[('picking_type_id.code','=','incoming')]",  # Hanya return picking
        readonly=True,
        compute="_compute_return_id",  # Auto hitung return picking
        store=True
    )

    # ==========================
    # Onchange saat pilih delivery
    # ==========================
    @api.onchange('delivery_id')
    def _onchange_delivery_id(self):
        """Isi warehouse otomatis saat delivery dipilih"""
        for rec in self:
            if rec.delivery_id:
                # rec.sale_id = rec.delivery_id.sale_id  # Bisa aktifkan jika ingin auto isi sales order
                rec.warehouse_id = rec.delivery_id.picking_type_id.warehouse_id

    # ==========================
    # Compute return_id & is_returned
    # ==========================
    @api.depends('delivery_id')
    def _compute_return_id(self):
        for rec in self:
            if rec.delivery_id:
                # Cari picking return terkait dengan delivery
                return_pickings = self.env['stock.picking'].search([
                    ('return_id', '=', rec.delivery_id.id),
                    ('picking_type_id.code', '=', 'incoming')
                ], limit=1)
                rec.return_id = return_pickings.id if return_pickings else False
                rec.is_returned = bool(return_pickings)  # True jika ada return

    # ==========================
    # Override create
    # ==========================
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

    # ==========================
    # Override write
    # ==========================
    def write(self, vals):
        """Update delivery_id di receipt jika ada perubahan"""
        res = super().write(vals)
        for rec in self:
            delivery = vals.get('delivery_id') or rec.delivery_id
            receipt = vals.get('receipt_code_product') or rec.receipt_code_product
            if delivery and receipt:
                receipt.delivery_id = delivery  # Sync delivery_id ke receipt
        return res

    # ==========================
    # Override unlink
    # ==========================
    def unlink(self):
        """Sebelum delete, reset delivery_id di receipt menjadi null"""
        for rec in self:
            if rec.receipt_code_product:
                rec.receipt_code_product.delivery_id = False  # Reset delivery link
        return super().unlink()

    # ==========================
    # Onchange filter receipt_code_product berdasarkan product & warehouse
    # ==========================
    @api.onchange('product_id', 'warehouse_id')
    def _onchange_product_id(self):
        """
        Filter receipt_code_product yang masih available (belum dikirim) sesuai product dan warehouse
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