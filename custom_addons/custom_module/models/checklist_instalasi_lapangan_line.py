from odoo import models, fields, api

class ChecklistInstalasiLapanganLine(models.Model):
    _name = 'checklist.instalasi.lapangan.line'
    _description = 'Checklist Instalasi Lapangan Line'

    checklist_id = fields.Many2one('checklist.instalasi.lapangan', string='Checklist Instalasi Lapangan')
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    demand = fields.Float(string='Demand', readonly=True)
    quantity = fields.Float(string='Quantity', readonly=True)
    # image_line_ids = fields.One2many(
    #     'checklist.instalasi.lapangan.image',
    #     'checklist_instalasi_lapangan_id',
    #     string='Checklist Instalasi Lapangan Images'
    # )

    _sql_constraints = [
        ('delivery_uniq',
        'unique(delivery_id)',
        'Checklist untuk Delivery Order ini sudah ada!'),
    ]

    def action_checklist_instalasi(self):
        self.ensure_one()

        # Cari semua checklist product berdasarkan product_id
        checklist_products = self.env['checklist.instalasi.product'].search([
            ('product_id', '=', self.product_id.id)
        ])

        created_records = []
        for checklist_product in checklist_products:
            # cek apakah record sudah ada
            existing_image = self.env['checklist.instalasi.lapangan.image'].search([
                ('checklist_instalasi_lapangan_id', '=', self.checklist_id.id),
                ('product_id', '=', self.product_id.id),
                ('checklist_instalasi_product_id', '=', checklist_product.id)
            ], limit=1)

            if existing_image:
                created_records.append(existing_image.id)
            else:
                image_record = self.env['checklist.instalasi.lapangan.image'].create({
                    'checklist_instalasi_lapangan_id': self.checklist_id.id,
                    'product_id': self.product_id.id,
                    'checklist_instalasi_product_id': checklist_product.id,
                    'information': '',
                    'image': False,
                })
                created_records.append(image_record.id)

        # Return dengan memanggil view yang akan digunakan (view_id)
        # untuk context ini mengirimkan data secara langsung ke model/view yang dituju
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Checklist Instalasi Image',
        #     'res_model': 'checklist.instalasi.lapangan.image',
        #     'view_mode': 'form',
        #     'res_id': created_records[0] if created_records else False,
        #     'view_id': self.env.ref('custom_module.checklist_instalasi_lapangan_image_form_view').id,
        #     'target': 'current',
        #     # 'context': {
        #     #     'default_checklist_instalasi_lapangan_id': self.checklist_id.id,
        #     #     'default_product_id': self.product_id.id
        #     # },
        # }

        # code ini digunakan untuk menampilkan record image dengan pager
        return {
            'type': 'ir.actions.act_window',
            'name': 'Checklist Instalasi Image',
            'res_model': 'checklist.instalasi.lapangan.image',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created_records)],
            'view_id': False,
            'target': 'current',
            'flags': {
                'pager': True,
                'action_buttons': True,
            },
        }
