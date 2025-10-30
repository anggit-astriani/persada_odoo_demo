from odoo import models, fields, api

class InventoryReceiptProductDetail(models.Model):
    _name = 'inventory.receipt.product.detail'  # Nama model untuk detail produk receipt
    _rec_name = 'code_product'  # Field yang digunakan sebagai display name di tree/form view

    # Relasi dengan stock.picking dan data lain
    receipt_id = fields.Many2one(
        'stock.picking', 
        string='Receipt', 
        domain="[('picking_type_id.code','=','incoming')]"  # Hanya picking type incoming
    )
    code_product = fields.Char('Code Product', required=True)  # Kode unik produk di receipt
    product_id = fields.Many2one('product.product', string='Product', required=True)  # Produk yang diterima
    purchase_id = fields.Many2one('purchase.order', string='Purchase Order')  # PO terkait
    warehouse_id = fields.Many2one('stock.warehouse', string='Werehouse')  # Warehouse tempat receipt
    delivery_id = fields.Many2one(
        'stock.picking', 
        string='Delivery', 
        domain="[('picking_type_id.code','=','outgoing')]"  # Hanya picking type outgoing
    )

    # Onchange saat memilih receipt
    @api.onchange('receipt_id')
    def _onchange_receipt_id(self):
        """Isi otomatis purchase_id, warehouse_id, dan set domain product sesuai move.line receipt"""
        if self.receipt_id:
            self.purchase_id = self.receipt_id.purchase_id  # Isi PO otomatis
            self.warehouse_id = self.receipt_id.picking_type_id.warehouse_id  # Isi warehouse otomatis
            # Ambil hanya produk yang muncul di move_ids_without_package
            products = self.receipt_id.move_ids_without_package.product_id
            return {
                'domain': {'product_id': [('id', 'in', products.ids)]}  # Batasi product_id sesuai receipt
            }

    # ==========================
    # Override create untuk auto isi fields
    # ==========================
    @api.model
    def create(self, vals):
        """Isi otomatis receipt_id, purchase_id, dan warehouse_id saat create record"""
        # Ambil parent_id dari vals atau context
        parent_id = vals.get('receipt_id') or self._context.get('default_receipt_id')
        if parent_id:
            picking = self.env['stock.picking'].browse(parent_id)  # Ambil record picking
            if picking:
                # Isi receipt_id jika belum ada di vals
                if not vals.get('receipt_id'):
                    vals['receipt_id'] = picking.id
                # Isi purchase_id jika belum ada
                if not vals.get('purchase_id') and picking.purchase_id:
                    vals['purchase_id'] = picking.purchase_id.id
                # Isi warehouse_id jika belum ada
                if not vals.get('warehouse_id') and picking.picking_type_id.warehouse_id:
                    vals['warehouse_id'] = picking.picking_type_id.warehouse_id.id

        return super().create(vals)  # Panggil method create asli
