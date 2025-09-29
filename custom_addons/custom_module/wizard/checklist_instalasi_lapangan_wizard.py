from odoo import models, fields, api

class ChecklistInstalasiLapanganWizard(models.TransientModel):
    _name = 'checklist.instalasi.lapangan.wizard'
    _description = 'Wizard Checklist Instalasi Lapangan'
    _rec_name = 'delivery_id'

    delivery_id = fields.Many2one('stock.picking', string='Delivery Order', readonly=True)
    user_id = fields.Many2one('res.users', string='User', readonly=True)
    officer_id = fields.Many2one('res.partner', string='Officer', domain=[('is_company', '=', False)])
    latitude = fields.Char(string='Delivered Latitude')
    longitude = fields.Char(string='Delivered Longitude')
    information = fields.Text(string='Information')
    product_line_ids = fields.One2many('checklist.instalasi.lapangan.wizard.line', 'wizard_id', string="Products")

    def action_confirm(self):
        self.ensure_one()

        #  cek apakah record sudah ada
        exist = self.env['checklist.instalasi.lapangan'].search(
            [('delivery_id', '=', self.delivery_id.id)], limit=1
        )

        if exist:
            # sudah ada → redirect ke record lama
            return {
                'name': 'Checklist Instalasi Lapangan',
                'type': 'ir.actions.act_window',
                'res_model': 'checklist.instalasi.lapangan',
                'view_mode': 'form',
                'view_id': self.env.ref('custom_module.checklist_instalasi_lapangan_form_view').id,
                'res_id': exist.id,
                'target': 'current'
            }

        # jika tidak ada maka buat record baru
        checklist = self.env['checklist.instalasi.lapangan'].create({
            'delivery_id': self.delivery_id.id,
            'user_id': self.user_id.id,
            'officer_id': self.officer_id.id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'information': self.information
        })

        # line_vals = []
        # for line in self.product_line_ids:
        #     line_vals.append((0, 0, {
        #         'checklist_id': checklist.id,
        #         'product_id': line.product_id.id,
        #         'demand': line.demand,
        #         'quantity': line.quantity
        #     }))
        # checklist.product_line_ids = line_vals

        return {
            'name': 'Checklist Instalasi Lapangan',
            'type': 'ir.actions.act_window',
            'res_model': 'checklist.instalasi.lapangan',
            'view_mode': 'form',
            'view_id': self.env.ref('custom_module.checklist_instalasi_lapangan_form_view').id,
            'res_id': checklist.id,
            'target': 'current',
        }