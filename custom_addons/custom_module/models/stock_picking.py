from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    zip = fields.Char(string='ZIP')
    country_id = fields.Many2one('res.country', string='Country')

    destination_latitude = fields.Char(string='Destination Latitude')
    destination_longitude =  fields.Char(string='Destination Longitude')
    delivered_latitude = fields.Char(string='Delivered Latitude')
    delivered_longitude =  fields.Char(string='Delivered Longitude')

    proof_of_delivery_before = fields.Binary(string="Proof of Delivery Before Departure", attachment=True)
    proof_of_delivery_before_filename = fields.Char(string="Filename")
    proof_of_delivery_after = fields.Binary(string="Proof of Delivery After Delivery", attachment=True)
    proof_of_delivery_after_filename = fields.Char(string="Filename")

    shipping_document = fields.Binary(string="Shipping Document", attachment=True)
    shipping_document_filename = fields.Char(string="Filename")

    receipt_product_detail_line_ids = fields.One2many('inventory.receipt.product.detail', 'receipt_id', string='Detail Product Lines')
    delivery_product_detail_line_ids = fields.One2many('inventory.delivery.product.detail', 'delivery_id', string='Detail Product Lines')
    return_product_detail_line_ids = fields.One2many('inventory.return.product.detail', 'return_id', string='Return Detail Product Lines')
    # purchase_id = fields.Many2one('purchase.order', string='Purchase Order')

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('waiting', 'Waiting Another Operation'),
            ('confirmed', 'Waiting'),
            ('assigned', 'Ready to Send'),
            ('delivery', 'On Delivery'),
            ('done', 'Done'),
            ('cancel', 'Cancelled')
        ], string='Status', copy=False, index=True, readonly=True, store=True, help="Status of the delivery order"
    )


    @api.onchange('state_id')
    def _onchange_state_id(self):
        """Auto-update country when state changes"""
        if self.state_id:
            self.country_id = self.state_id.country_id
    
    @api.onchange('country_id')
    def _onchange_country_id(self):
        """Clear state if country changes"""
        if self.country_id:
            # Only clear state if it doesn't belong to selected country
            if self.state_id and self.state_id.country_id != self.country_id:
                self.state_id = False
        else:
            self.state_id = False

    def action_start_delivery(self):
        """Method untuk memulai pengiriman (mengubah status ke delivery)"""
        for picking in self:
            if picking.state == 'assigned':
                # Gunakan write untuk update state secara langsung
                picking.write({'state': 'delivery'})
        return True
    
    def action_checklist_instalasi_lapangan(self):
        """Open wizard checklist instalasi lapangan dari Delivery Order"""
        self.ensure_one()
        wizard = self.env['checklist.instalasi.lapangan.wizard'].create({
            'delivery_id': self.id,
            'latitude': self.delivered_latitude,
            'longitude': self.delivered_longitude,
            'user_id': self.user_id.id
        })

        product_lines = []
        for move in self.move_ids_without_package:
            product_lines.append((0, 0, {
                'product_id': move.product_id.id,
                'demand': move.product_uom_qty,
                'uom_id': move.product_uom.id,
                'quantity': move.quantity,
            }))
        wizard.product_line_ids = product_lines
        # print("Produk dari DO %s: %s", move.name, product_lines)

        return {
        'name': 'Checklist Instalasi Lapangan',
        'type': 'ir.actions.act_window',
        'res_model': 'checklist.instalasi.lapangan.wizard',
        'view_mode': 'form',
        'view_id': self.env.ref('custom_module.checklist_instalasi_lapangan_wizard_form_view').id,
        'res_id': wizard.id,
        'target': 'new',  # supaya muncul popup
        }

    # # --- auto-generate detail lines ---
    # @api.onchange('move_ids_without_package')
    # def _onchange_generate_detail_lines(self):
    #     for picking in self:
    #         lines = []
    #         # hapus baris lama
    #         picking.receipt_product_detail_line_ids = [(5, 0, 0)]
    #         for move in picking.move_ids_without_package:
    #             product = move.product_id
    #             # gunakan quantity_done, jika kosong gunakan 0
    #             qty = int(move.quantity or 0)
    #             # jika menggunakan demand 
    #             # qty = int(move.product_uom_qty)
    #             for _ in range(qty):
    #                 lines.append((0, 0, {
    #                     'product_id': product.id,
    #                     'code_product': product.default_code or '',
    #                     'purchase_id': picking.purchase_id.id if picking.purchase_id else False,
    #                     'warehouse_id': picking.picking_type_id.warehouse_id.id if picking.picking_type_id.warehouse_id else False,
    #                 }))
    #         picking.receipt_product_detail_line_ids = lines

    # --- auto-generate detail lines ---
    # @api.onchange('move_ids_without_package', 
    #           'move_ids_without_package.quantity')
    # def _onchange_generate_detail_lines(self):
    #     for picking in self:
    #         picking_type = picking.picking_type_id.code  # incoming / outgoing / internal

    #         # kalau receipt (incoming)
    #         if picking_type == 'incoming':
    #             receipt_lines = []
    #             picking.receipt_product_detail_line_ids = [(5, 0, 0)]
    #             for move in picking.move_ids_without_package:
    #                 product = move.product_id
    #                 qty = int(move.quantity)
    #                 for _ in range(qty):
    #                     receipt_lines.append((0, 0, {
    #                         'product_id': product.id,
    #                         'code_product': product.default_code or '',
    #                         'purchase_id': picking.purchase_id.id if picking.purchase_id else False,
    #                         'warehouse_id': picking.picking_type_id.warehouse_id.id if picking.picking_type_id.warehouse_id else False,
    #                     }))
    #             picking.receipt_product_detail_line_ids = receipt_lines

    #         # kalau delivery (outgoing)
    #         elif picking_type == 'outgoing':
    #             delivery_lines = []
    #             picking.delivery_product_detail_line_ids = [(5, 0, 0)]
    #             for move in picking.move_ids_without_package:
    #                 product = move.product_id
    #                 qty = int(move.quantity)
    #                 for _ in range(qty):
    #                     delivery_lines.append((0, 0, {
    #                         'product_id': product.id,
    #                         'code_product': product.default_code or '',
    #                         # 'sale_id': picking.sale_id.id if picking.sale_id else False,
    #                         'warehouse_id': picking.picking_type_id.warehouse_id.id if picking.picking_type_id.warehouse_id else False,
    #                     }))
    #             picking.delivery_product_detail_line_ids = delivery_lines

    #         else:
    #             # untuk internal transfer atau jenis lain, kosongkan saja
    #             picking.receipt_product_detail_line_ids = [(5, 0, 0)]
    #             picking.delivery_product_detail_line_ids = [(5, 0, 0)]



# --------------------------- ini adalah kode yang dari calude --------------------------------------- 
    def action_create_return_from_delivery(self, original_delivery_id):
        """Method untuk membuat return picking dari delivery"""
        original_delivery = self.env['stock.picking'].browse(original_delivery_id)
        
        if not original_delivery or original_delivery.picking_type_id.code != 'outgoing':
            raise ValueError("Invalid delivery picking")
        
        # Buat return picking
        return_picking_vals = {
            'picking_type_id': self.env['stock.picking.type'].search([
                ('code', '=', 'incoming'),
                ('warehouse_id', '=', original_delivery.picking_type_id.warehouse_id.id)
            ], limit=1).id,
            'location_id': original_delivery.location_dest_id.id,
            'location_dest_id': original_delivery.location_id.id,
            'partner_id': original_delivery.partner_id.id,
            'origin': f"Return of {original_delivery.name}",
        }
        
        return_picking = self.create(return_picking_vals)
        
        # Ambil semua delivery detail yang belum di-return
        delivery_details = original_delivery.delivery_product_detail_line_ids.filtered(
            lambda x: not x.is_returned
        )
        
        if delivery_details:
            # Buat return details dari delivery details
            self.env['inventory.return.product.detail'].create_from_delivery_detail(
                delivery_details.ids, return_picking.id
            )
            
            # Buat move lines untuk return picking
            for detail in delivery_details:
                move_vals = {
                    'name': detail.product_id.name,
                    'product_id': detail.product_id.id,
                    'product_uom_qty': 1,
                    'product_uom': detail.product_id.uom_id.id,
                    'picking_id': return_picking.id,
                    'location_id': return_picking.location_id.id,
                    'location_dest_id': return_picking.location_dest_id.id,
                }
                self.env['stock.move'].create(move_vals)
        
        return return_picking

    @api.onchange('move_ids_without_package', 'move_ids_without_package.quantity')
    def _onchange_generate_detail_lines(self):
        for picking in self:
            picking_type = picking.picking_type_id.code

            if picking_type == 'incoming':
                # Check if this is a return picking
                is_return = 'Return of' in (picking.origin or '')
                
                if not is_return:
                    # Normal receipt
                    receipt_lines = []
                    picking.receipt_product_detail_line_ids = [(5, 0, 0)]
                    for move in picking.move_ids_without_package:
                        product = move.product_id
                        qty = int(move.quantity)
                        for _ in range(qty):
                            receipt_lines.append((0, 0, {
                                'product_id': product.id,
                                'code_product': product.default_code or '',
                                'purchase_id': picking.purchase_id.id if picking.purchase_id else False,
                                'warehouse_id': picking.picking_type_id.warehouse_id.id if picking.picking_type_id.warehouse_id else False,
                            }))
                    picking.receipt_product_detail_line_ids = receipt_lines

            elif picking_type == 'outgoing':
                delivery_lines = []
                picking.delivery_product_detail_line_ids = [(5, 0, 0)]
                for move in picking.move_ids_without_package:
                    product = move.product_id
                    qty = int(move.quantity)
                    for _ in range(qty):
                        delivery_lines.append((0, 0, {
                            'product_id': product.id,
                            'code_product': product.default_code or '',
                            'warehouse_id': picking.picking_type_id.warehouse_id.id if picking.picking_type_id.warehouse_id else False,
                        }))
                picking.delivery_product_detail_line_ids = delivery_lines

            else:
                picking.receipt_product_detail_line_ids = [(5, 0, 0)]
                picking.delivery_product_detail_line_ids = [(5, 0, 0)]