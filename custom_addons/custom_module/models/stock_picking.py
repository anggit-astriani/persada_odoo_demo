from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    zip = fields.Char(string='ZIP')
    country_id = fields.Many2one('res.country', string='Country')

    destination_latitude = fields.Float(
        string='Destination Latitude',
        digits=(16, 6),
        tracking=True,
        help='Latitude coordinate (manual entry)'
    )
    destination_longitude =  fields.Float(
        string='Destination longitude',
        digits=(16, 6),
        tracking=True,
        help='delivered longitude coordinate (manual entry)'
    )
    delivered_latitude = fields.Float(
        string='Delivered Latitude',
        digits=(16, 6),
        tracking=True,
        help='Latitude coordinate (manual entry)'
    )
    delivered_longitude =  fields.Float(
        string='Delivered Longitude',
        digits=(16, 6),
        tracking=True,
        help='Longitude coordinate (manual entry)'
    )

    proof_of_delivery_before = fields.Binary(string="Proof of Delivery Before Departure", attachment=True)
    proof_of_delivery_before_filename = fields.Char(string="Filename")
    proof_of_delivery_after = fields.Binary(string="Proof of Delivery After Delivery", attachment=True)
    proof_of_delivery_after_filename = fields.Char(string="Filename")

    shipping_document = fields.Binary(string="Shipping Document", attachment=True)
    shipping_document_filename = fields.Char(string="Filename")

    receipt_product_detail_line_ids = fields.One2many('inventory.receipt.product.detail', 'receipt_id', string='Detail Product Lines')
    delivery_product_detail_line_ids = fields.One2many('inventory.delivery.product.detail', 'delivery_id', string='Detail Product Lines')
    return_product_detail_line_ids = fields.One2many('inventory.return.product.detail', 'return_id', string='Return Detail Product Lines')
    
    # PostGIS geometry field
    shape = fields.GeoPoint(
        string='Map Location',
        help='Location coordinates using PostGIS geometry (SRID 4326)',
        srid=4326
    )

    # Display fields
    location_display = fields.Char(
        string='Location',
        compute='_compute_location_display',
        store=True
    )

    geo_wkt = fields.Char(
        string='Geometry (WKT)',
        compute='_compute_geo_wkt',
        store=True
    )

    active = fields.Boolean(default=True, tracking=True)

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


# --------------------------- function dari geoengine ---------------------------------------
# ===========================================================================================
    @api.onchange('shape')
    def _onchange_shape(self):
        """Kalau user pilih lokasi di map, isi delivered_latitude/delivered_longitude"""
        for rec in self:
            if rec.shape and hasattr(rec.shape, 'coords'):
                try:
                    lon, lat = rec.shape.coords[0], rec.shape.coords[1]
                    rec.delivered_latitude = float(lat)
                    rec.delivered_longitude = float(lon)
                except Exception as e:
                    _logger.warning(f"Failed to extract coords from shape: {e}")

    @api.onchange('delivered_latitude', 'delivered_longitude')
    def _onchange_latlon(self):
        """Kalau user isi delivered_latitude/delivered_longitude manual, update shape"""
        for rec in self:
            if rec.delivered_latitude and rec.delivered_longitude:
                try:
                    rec.set_location_from_coordinates(rec.delivered_latitude, rec.delivered_longitude)
                except Exception as e:
                    _logger.warning(f"Failed to update shape from lat/lon: {e}")

    @api.depends('shape', 'delivered_latitude', 'delivered_longitude')
    def _compute_location_display(self):
        for rec in self:
            if rec.shape and hasattr(rec.shape, 'coords'):
                try:
                    lon, lat = rec.shape.coords[0], rec.shape.coords[1]
                    rec.location_display = f"Lat: {lat:.6f}, Lng: {lon:.6f}"
                except Exception:
                    rec.location_display = "PostGIS Geometry Set"
            elif rec.delivered_latitude and rec.delivered_longitude:
                rec.location_display = f"Lat: {rec.delivered_latitude:.6f}, Lng: {rec.delivered_longitude:.6f}"
            else:
                rec.location_display = "No location set"

    @api.depends('shape', 'delivered_latitude', 'delivered_longitude')
    def _compute_geo_wkt(self):
        for rec in self:
            if rec.shape:
                try:
                    if hasattr(rec.shape, 'wkt'):
                        rec.geo_wkt = rec.shape.wkt
                    else:
                        rec.geo_wkt = str(rec.shape)
                except Exception:
                    rec.geo_wkt = "PostGIS Geometry"
            elif rec.delivered_latitude and rec.delivered_longitude:
                rec.geo_wkt = f'POINT({rec.delivered_longitude} {rec.delivered_latitude})'
            else:
                rec.geo_wkt = False

    @api.constrains('delivered_latitude', 'delivered_longitude')
    def _check_coordinates(self):
        for rec in self:
            if rec.delivered_latitude and (rec.delivered_latitude < -90 or rec.delivered_latitude > 90):
                raise ValidationError(_('delivered_latitude must be between -90 and 90 degrees.'))
            if rec.delivered_longitude and (rec.delivered_longitude < -180 or rec.delivered_longitude > 180):
                raise ValidationError(_('delivered_longitude must be between -180 and 180 degrees.'))

    def set_location_from_coordinates(self, lat, lng):
        """Internal method: set shape dari lat/lon"""
        self.ensure_one()
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValidationError(_('Invalid coordinates.'))
        try:
            self._cr.execute("""
                UPDATE stock_picking
                SET shape = ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                WHERE id = %s
            """, (lng, lat, self.id))
            self.write({'delivered_latitude': lat, 'delivered_longitude': lng})
        except Exception as e:
            _logger.error("Failed to create PostGIS geometry: %s", e)
            raise ValidationError(_('Failed to create PostGIS geometry.'))
        return True

    def action_set_location_from_coordinates(self):
        self.ensure_one()
        if not self.delivered_latitude or not self.delivered_longitude:
            raise ValidationError(_('Please enter both delivered_latitude and delivered_longitude.'))
        return self.set_location_from_coordinates(self.delivered_latitude, self.delivered_longitude)

    def action_clear_location(self):
        self.write({'shape': False, 'delivered_latitude': False, 'delivered_longitude': False})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Location Cleared'),
                'message': _('Location coordinates have been cleared.'),
                'type': 'success',
            }
        }

    def action_geocode_address(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Geocoding'),
                'message': _('Geocoding service not configured. Please set location manually.'),
                'type': 'info',
            }
        }

    def action_open_map_view(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Location Map'),
            'res_model': 'stock.picking',
            'view_mode': 'geoengine',
            'domain': [('id', '=', self.id)],
            'context': {'create': False, 'edit': False},
        }
    
    @api.model
    def get_customers_geojson(self):
        customers = self.search([('shape', '!=', False), ('active', '=', True)])
        features = []
        for cust in customers:
            try:
                if cust.shape:
                    features.append({
                        'type': 'Feature',
                        'properties': {
                            'id': cust.id,
                            'name': cust.name,
                            'description': cust.description or '',
                            'phone': cust.phone or '',
                            'email': cust.email or '',
                        },
                        'geometry': {
                            'type': 'Point',
                            'coordinates': [cust.shape.coords[0], cust.shape.coords[1]]
                        }
                    })
            except Exception as e:
                _logger.warning("Failed to process geometry for %s: %s", cust.name, e)
        return {'type': 'FeatureCollection', 'features': features}