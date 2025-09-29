from odoo import models, fields, api

class ChecklistInstalasiLapanganImage(models.Model):
    _name = 'checklist.instalasi.lapangan.image'
    _description = 'Checklist Instalasi Lapangan Image'
    _rec_name = 'checklist_instalasi_product_id'

    checklist_instalasi_product_id = fields.Many2one('checklist.instalasi.product', string='Checklist Instalasi Product', readonly=True)
    checklist_instalasi_lapangan_id = fields.Many2one('checklist.instalasi.lapangan', string='Delivery Order', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    image = fields.Binary(string='Image')
    image1 = fields.Binary(string='Image')
    image2 = fields.Binary(string='Image')
    image3 = fields.Binary(string='Image')
    information = fields.Text(string='Information')

    product_criteria_ids = fields.One2many(
        'checklist.instalasi.product.criteria',
        'checklist_instalasi_product_id',
        string='Product Criteria',
        compute='_compute_product_criteria',
        store=False
    )

    @api.depends('checklist_instalasi_product_id')
    def _compute_product_criteria(self):
        for record in self:
            if record.checklist_instalasi_product_id:
                record.product_criteria_ids = self.env['checklist.instalasi.product.criteria'].search([
                    ('checklist_instalasi_product_id', '=', record.checklist_instalasi_product_id.id)
                ])
            else:
                record.product_criteria_ids = False