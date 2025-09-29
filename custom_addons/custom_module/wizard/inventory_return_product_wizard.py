from odoo import models, fields, api

class InventoryReturnProductWizard(models.TransientModel):
    _name = 'inventory.return.product.wizard'
    _description = 'Wizard Return Product'

    delivery_id = fields.Many2one(
        'stock.picking',
        string='Delivery',
        required=True,
        readonly=True
    )
    line_ids = fields.One2many(
        'inventory.return.product.wizard.line',
        'wizard_id',
        string='Detail Products'
    )

    @api.model
    def default_get(self, fields_list):
        """Ambil data product detail yang belum direturn untuk delivery tertentu"""
        res = super().default_get(fields_list)
        delivery_id = self.env.context.get('active_id')
        if delivery_id:
            res['delivery_id'] = delivery_id
            details = self.env['inventory.delivery.product.detail'].search([
                ('delivery_id', '=', delivery_id),
                ('is_returned', '=', False)
            ])
            lines = []
            for d in details:
                lines.append((0, 0, {
                    'detail_id': d.id,
                    'product_id': d.product_id.id,
                    'code_product': d.code_product,
                    'select': False
                }))
            res['line_ids'] = lines
        return res

    def action_confirm(self):
        """Buat picking return dan update return_id"""
        StockPicking = self.env['stock.picking']
        for wizard in self:
            for line in wizard.line_ids.filtered('select'):
                detail = line.detail_id
                # Buat picking return
                picking_return = StockPicking.create({
                    'picking_type_id': wizard.delivery_id.picking_type_id.return_picking_type_id.id,
                    'location_id': wizard.delivery_id.location_dest_id.id,
                    'location_dest_id': wizard.delivery_id.location_id.id,
                    'origin': wizard.delivery_id.name,
                })
                # Buat move line
                picking_return.move_ids_without_package.create({
                    'picking_id': picking_return.id,
                    'product_id': detail.product_id.id,
                    'product_uom_qty': 1,
                    'product_uom': detail.product_id.uom_id.id,
                    'location_id': wizard.delivery_id.location_dest_id.id,
                    'location_dest_id': wizard.delivery_id.location_id.id,
                })
                # Update detail product
                detail.write({
                    'is_returned': True,
                    'return_id': picking_return.id
                })
        return {'type': 'ir.actions.act_window_close'}
