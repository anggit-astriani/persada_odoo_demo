from odoo import models, fields, api

class InventoryReturnProductDetail(models.Model):
    _name = 'inventory.return.product.detail'  # Nama model untuk detail return produk
    _rec_name = 'code_product'  # Field yang digunakan sebagai display name di tree/form view

    # ==========================
    # Relasi dengan stock.picking (return dan original delivery)
    # ==========================
    return_id = fields.Many2one(
        'stock.picking', 
        string='Return', 
        domain="[('picking_type_id.code','=','incoming')]",  # Hanya picking type incoming
        required=True, 
        readonly=True
    )
    original_delivery_id = fields.Many2one(
        'stock.picking', 
        string='Delivery', 
        domain="[('picking_type_id.code','=','outgoing')]",  # Hanya picking type outgoing
        required=True
    )

    # ==========================
    # Product dan kode product
    # ==========================
    # receipt_id = fields.Many2one('inventory.receipt.product.detail', string='Receipt', required=True)
    product_id = fields.Many2one('product.product', string='Product')  # Produk yang dikembalikan
    code_product = fields.Many2one(
        'inventory.receipt.product.detail', 
        string='Code Product', 
        required=True  # Menghubungkan dengan kode product dari receipt
    )
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')  # Warehouse asal produk

    # ==========================
    # Onchange untuk auto-update warehouse
    # ==========================
    @api.onchange('return_id')
    def _onchange_return_id(self):
        """Isi warehouse otomatis saat return picking dipilih"""
        for rec in self:
            if rec.return_id:
                # Ambil warehouse dari picking type return
                rec.warehouse_id = rec.return_id.picking_type_id.warehouse_id

    # ==========================
    # Method untuk membuat return detail dari delivery detail
    # ==========================
    def create_from_delivery_detail(self, delivery_detail_ids, return_picking_id):
        """Buat record inventory.return.product.detail dari detail delivery"""
        return_details = []  # Menyimpan id return detail yang dibuat
        
        for delivery_detail_id in delivery_detail_ids:
            # Ambil record delivery detail
            delivery_detail = self.env['inventory.delivery.product.detail'].browse(delivery_detail_id)
            
            # Siapkan values untuk return detail
            return_detail_vals = {
                'return_id': return_picking_id,  # Return picking
                'original_delivery_id': delivery_detail.delivery_id.id,  # Delivery asal
                'code_product': delivery_detail.receipt_code_product.id,  # Kode product dari receipt
                'product_id': delivery_detail.product_id.id,  # Produk
                'warehouse_id': delivery_detail.warehouse_id.id,  # Warehouse
            }
            
            # Buat return detail
            return_detail = self.create(return_detail_vals)
            return_details.append(return_detail.id)  # Simpan id return detail
            
            # Reset delivery_id pada receipt product (jika ada)
            if delivery_detail.receipt_code_product:
                delivery_detail.receipt_code_product.write({'delivery_id': False})
            
            # Tandai delivery detail sebagai sudah di-return
            delivery_detail.write({
                'is_returned': True,  # Flag bahwa detail sudah dikembalikan
                'return_id': return_picking_id  # Hubungkan dengan return picking
            })
        
        return return_details  # Kembalikan daftar ID return detail yang dibuat
