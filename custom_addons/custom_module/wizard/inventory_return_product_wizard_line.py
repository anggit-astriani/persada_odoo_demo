from odoo import models, fields

class InventoryReturnProductWizardLine(models.TransientModel):
    _name = 'inventory.return.product.wizard.line'
    _description = 'Return Product Line'

    wizard_id = fields.Many2one('inventory.return.product.wizard', required=True)
    detail_id = fields.Many2one('inventory.delivery.product.detail', string="Detail Product", required=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    code_product = fields.Char('Code Product', readonly=True)
    select = fields.Boolean('Return?')
