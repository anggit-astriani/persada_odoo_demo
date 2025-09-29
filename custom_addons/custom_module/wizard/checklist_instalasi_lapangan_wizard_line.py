from odoo import models, fields, api

class ChecklistInstalasiLapanganWizardLine(models.TransientModel):
    _name = 'checklist.instalasi.lapangan.wizard.line'
    _description = 'Checklist Instalasi Lapangan Wizard Line'
    _rec_name = 'product_id'

    wizard_id = fields.Many2one('checklist.instalasi.lapangan.wizard', string='Wizard', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    demand = fields.Float(string='Demand', readonly=True)
    uom_id = fields.Many2one('uom.uom', string="UOM", readonly=True)
    quantity = fields.Float(string='Quantity', readonly=True)

    # def action_checklist_instalasi(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Checklist Instalasi Image',
    #         'res_model': 'checklist.instalasi.lapangan.image',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('custom_module.checklist_instalasi_lapangan_image_form_view').id,
    #         'target': 'current',  # atau 'current' jika ingin di halaman yang sama
    #         'context': {
    #             'default_checklist_instalasi_lapangan_id': self.checklist_id.id,
    #             'default_checklist_instalasi_product_id': self.product_id.id,
    #         },
    #     }