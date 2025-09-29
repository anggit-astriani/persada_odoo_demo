from odoo import models, fields, api

class ChecklistInstalasiLapangan(models.Model):
    _name = 'checklist.instalasi.lapangan'
    _description = 'Checklist Instalasi Lapangan Image'
    _rec_name = 'delivery_id'

    delivery_id = fields.Many2one('stock.picking', string='Delivery', domain="[('picking_type_id.code','=','outgoing')]", required=True, readonly=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, readonly=True)
    officer_id = fields.Many2one('res.partner', string='Officer', domain=[('is_company', '=', False)])
    latitude = fields.Char(string='Latitude')
    longitude = fields.Char(string='Longitude')
    information = fields.Text(string='Information')
    product_line_ids = fields.One2many('checklist.instalasi.lapangan.line', 'checklist_id', string="Products")
    image_line_ids = fields.One2many(
        'checklist.instalasi.lapangan.image',
        'checklist_instalasi_lapangan_id',
        string='Checklist Instalasi Lapangan Images'
    )

    @api.onchange('delivery_id')
    def _onchange_delivery_id(self):
        if self.delivery_id and not self.product_line_ids:
            lines = []
            for move in self.delivery_id.move_ids:
                lines.append((0, 0, {
                    'product_id': move.product_id.id,
                    'demand': move.product_uom_qty,
                    'quantity': move.quantity,
                }))
            self.product_line_ids = lines


    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.delivery_id:
            lines = []
            for move in record.delivery_id.move_ids:
                lines.append((0, 0, {
                    'product_id': move.product_id.id,
                    'demand': move.product_uom_qty,
                    'quantity': move.quantity,
                }))
            record.product_line_ids = lines
        return record

