from odoo import models, fields, api

class ChecklistInstalasiProduct(models.Model):
    _name = 'checklist.instalasi.product'
    _description = 'Checklist Instalasi Product'
    _rec_name = 'title'

    product_id = fields.Many2one('product.product', string='Product')
    title = fields.Char('Title')
    sequence = fields.Integer(string='Sequence')