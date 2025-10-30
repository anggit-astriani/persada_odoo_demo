from odoo import models, fields, api

class ChecklistInstalasiLapangan(models.Model):
    _name = 'checklist.instalasi.lapangan'
    _description = 'Checklist Instalasi Lapangan Image'
    _rec_name = 'delivery_id'

    delivery_id = fields.Many2one('stock.picking', string='Delivery', domain="[('picking_type_id.code','=','outgoing')]", required=True, readonly=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, readonly=True)
    officer_id = fields.Many2one('res.partner', string='Officer', domain=[('is_company', '=', False)])
    latitude = fields.Float(
        string='Latitude',
        digits=(16, 6),
        tracking=True,
        help='Latitude coordinate (manual entry)'
    )
    longitude = fields.Float(
        string='Longitude',
        digits=(16, 6),
        tracking=True,
        help='Latitude coordinate (manual entry)'
    )
    information = fields.Text(string='Information')
    product_line_ids = fields.One2many('checklist.instalasi.lapangan.line', 'checklist_id', string="Products")
    image_line_ids = fields.One2many(
        'checklist.instalasi.lapangan.image',
        'checklist_instalasi_lapangan_id',
        string='Checklist Instalasi Lapangan Images'
    )

    @api.onchange('delivery_id')
    def _onchange_delivery_id(self):
        # Jika user memilih delivery_id dan product_line_ids masih kosong
        if self.delivery_id and not self.product_line_ids:
            lines = []
            # Loop semua move line di delivery picking
            for move in self.delivery_id.move_ids:
                # Buat dictionary untuk setiap product line
                lines.append((0, 0, {
                    'product_id': move.product_id.id,   # Produk
                    'demand': move.product_uom_qty,     # Jumlah yang diminta / qty di picking
                    'quantity': move.quantity,          # Qty aktual
                }))
            # Assign product_line_ids ke hasil lines yang dibuat
            self.product_line_ids = lines


    @api.model
    def create(self, vals):
        record = super().create(vals)  # Buat record baru
        # Jika record memiliki delivery_id
        if record.delivery_id:
            lines = []
            # Loop semua move di delivery picking
            for move in record.delivery_id.move_ids:
                lines.append((0, 0, {
                    'product_id': move.product_id.id,
                    'demand': move.product_uom_qty,
                    'quantity': move.quantity,
                }))
            # Assign product_line_ids ke record baru
            record.product_line_ids = lines
        return record

