from odoo import fields, models

class RequestInstallmentImage(models.Model):
    _name = 'request.installment.image'
    _description = 'Images'

    request_installment_order_id = fields.Many2one('request.installment.order', ondelete='cascade')
    image = fields.Binary(required=True, attachment=True)