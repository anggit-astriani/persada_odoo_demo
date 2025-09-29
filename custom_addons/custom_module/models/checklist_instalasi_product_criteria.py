from odoo import models, fields, api

class ChecklistInstalasiProductCriteria(models.Model):
    _name = 'checklist.instalasi.product.criteria'
    _description = 'Checklist Instalasi Product Criteria'
    _rec_name = 'criteria'

    checklist_instalasi_product_id = fields.Many2one('checklist.instalasi.product', string='Checklist Instalasi Product')
    criteria = fields.Char(string='Criteria')
    information = fields.Text(string='Information')
    sequence = fields.Integer(string='Sequence')

