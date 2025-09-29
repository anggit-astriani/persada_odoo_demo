from odoo import models, fields

class RequestInstallmentOrderProduct(models.Model):
    _name = "request.installment.order.product"
    _description = "Request Installment Order Product"

    request_installment_order_id = fields.Many2one(
        "request.installment.order",
        string="Request Installment Order",
        required=True,
        ondelete="cascade"
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True
    )
    quantity = fields.Float(string="Quantity", default=1.0)
    description = fields.Text(string="Description")