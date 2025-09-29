from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class RequestInstallmentOrder(models.Model):
    _name = "request.installment.order"
    _description = "Request Installment Order"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    title = fields.Char(string="Title", required=True, tracking=True)
    description = fields.Text(string="Description")
    image_ids = fields.One2many('request.installment.image', 'request_installment_order_id')
    
    # Multiple images - perbaiki relasi
    attachment_ids = fields.One2many(
        'ir.attachment', 
        'res_id', 
        domain=[('res_model', '=', 'request.installment.order'), ('mimetype', 'like', 'image/')],
        string='Images',
        context={'default_res_model': 'request.installment.order'}
    )
    
    # Address fields - detailed format
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street 2")
    city = fields.Char(string="City")
    state_id = fields.Many2one('res.country.state', string="State")
    zip = fields.Char(string="ZIP")
    country_id = fields.Many2one('res.country', string="Country")
    
    # Computed field untuk full address (backward compatibility)
    address = fields.Char(string="Full Address", compute="_compute_address", store=True)
    
    # latitude = fields.Float("Latitude", digits=(16, 5), default=0.0)
    # longitude = fields.Float("Longitude", digits=(16, 5), default=0.0)

    # PostGIS geometry field
    shape = fields.GeoPoint(
        string='Map Location',
        help='Location coordinates using PostGIS geometry (SRID 4326)',
        srid=4326
    )

    latitude = fields.Float(
        string='Latitude',
        digits=(16, 6),
        tracking=True,
        help='Latitude coordinate (manual entry)',
        default=0.0
    )
    longitude = fields.Float(
        string='Longitude',
        digits=(16, 6),
        tracking=True,
        help='Longitude coordinate (manual entry)',
        default=0.0
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

    contact_id = fields.Many2one('res.partner', string="Contact", tracking=True)
    
    # Status workflow
    status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('done', 'Done'),
    ], string="Status", default='draft', tracking=True, readonly=True)
    
    product_line_ids = fields.One2many(
        "request.installment.order.product",
        "request_installment_order_id",
        string="Products"
    )
    
    # Field untuk smart button
    purchase_order_count = fields.Integer(
        string="Purchase Order Count", 
        compute="_compute_purchase_order_count"
    )
    
    @api.depends('street', 'street2', 'city', 'state_id', 'zip', 'country_id')
    def _compute_address(self):
        """Compute full address dari komponen address"""
        for record in self:
            address_parts = []
            
            if record.street:
                address_parts.append(record.street)
            if record.street2:
                address_parts.append(record.street2)
            if record.city:
                address_parts.append(record.city)
            if record.state_id:
                address_parts.append(record.state_id.name)
            if record.zip:
                address_parts.append(record.zip)
            if record.country_id:
                address_parts.append(record.country_id.name)
            
            record.address = ', '.join(address_parts) if address_parts else ''
    
    @api.depends('title')
    def _compute_purchase_order_count(self):
        """Hitung jumlah PO yang dibuat dari request ini"""
        for record in self:
            record.purchase_order_count = self.env['purchase.order'].search_count([
                ('origin', '=', record.title)
            ])
    
    @api.onchange('contact_id')
    def _onchange_contact_id(self):
        """Auto-fill address dari contact"""
        if self.contact_id:
            self.street = self.contact_id.street
            self.street2 = self.contact_id.street2
            self.city = self.contact_id.city
            self.state_id = self.contact_id.state_id
            self.zip = self.contact_id.zip
            self.country_id = self.contact_id.country_id
    
    def action_submit(self):
        """Submit request untuk approval"""
        if not self.product_line_ids:
            raise UserError("Please add at least one product before submitting.")
        
        self.write({'status': 'submitted'})
        self.message_post(body="Request submitted for approval.")

    def action_approve(self):
        """Approve request"""
        self.write({'status': 'approved'})
        self.message_post(body=f"Request approved by {self.env.user.name}.")

    def action_reject(self):
        """Reject request dan kembalikan ke draft"""
        self.write({'status': 'draft'})
        self.message_post(
            body=f"Request rejected by {self.env.user.name}. Please review and resubmit."
        )

    def action_create_purchase(self):
        """Buat Purchase Order dari request ini"""
        if not self.product_line_ids:
            raise UserError("No products to create purchase order.")
        
        po_vals = {
            'partner_id': self.contact_id.id if self.contact_id else False,
            'origin': self.title,
            'order_line': [],
        }
        
        for line in self.product_line_ids:
            po_line_vals = {
                'product_id': line.product_id.id,
                'product_qty': line.quantity,
                'product_uom': line.product_id.uom_id.id,
                'price_unit': line.product_id.standard_price or 0.0,
                'name': line.description or line.product_id.name or 'Product',
            }
            po_vals['order_line'].append((0, 0, po_line_vals))
        
        if not po_vals['partner_id']:
            raise UserError("Please set a contact/supplier before creating purchase order.")
            
        purchase_order = self.env['purchase.order'].create(po_vals)
        
        self.write({'status': 'done'})
        self.message_post(
            body=f"Purchase Order created: {purchase_order.name}. Request completed."
        )
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'res_model': 'purchase.order',
            'res_id': purchase_order.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_purchase_orders(self):
        """View PO yang dibuat dari request ini (untuk smart button)"""
        purchase_orders = self.env['purchase.order'].search([('origin', '=', self.title)])
        
        if len(purchase_orders) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Purchase Order',
                'res_model': 'purchase.order',
                'res_id': purchase_orders[0].id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Purchase Orders',
                'res_model': 'purchase.order',
                'domain': [('origin', '=', self.title)],
                'view_mode': 'tree,form',
                'target': 'current',
            }

    def action_done(self): 
        """Manual mark as done (jika diperlukan)"""
        self.write({'status': 'done'})
    
    @api.model
    def create(self, vals):
        """Override create untuk memastikan attachment ter-link"""
        record = super().create(vals)
        # Update attachment yang mungkin sudah di-upload tapi belum ter-link
        if 'attachment_ids' in vals:
            attachments = self.env['ir.attachment'].browse([att[1] for att in vals['attachment_ids'] if att[0] in (4, 6)])
            attachments.write({
                'res_model': self._name,
                'res_id': record.id
            })
        return record
    
    def write(self, vals):
        """Override write untuk memastikan attachment ter-link"""
        result = super().write(vals)
        if 'attachment_ids' in vals:
            for record in self:
                # Update semua attachment yang terkait record ini
                attachments = self.env['ir.attachment'].search([
                    ('res_model', '=', self._name),
                    ('res_id', '=', record.id),
                    ('mimetype', 'like', 'image/')
                ])
                attachments.write({
                    'res_model': self._name,
                    'res_id': record.id
                })
        return result

    #=========================================
    @api.onchange('shape')
    def _onchange_shape(self):
        """Kalau user pilih lokasi di map, isi latitude/longitude"""
        for rec in self:
            if rec.shape and hasattr(rec.shape, 'coords'):
                try:
                    lon, lat = rec.shape.coords[0], rec.shape.coords[1]
                    rec.latitude = float(lat)
                    rec.longitude = float(lon)
                except Exception as e:
                    _logger.warning(f"Failed to extract coords from shape: {e}")

    @api.onchange('latitude', 'longitude')
    def _onchange_latlon(self):
        """Kalau user isi latitude/longitude manual, update shape"""
        for rec in self:
            if rec.latitude and rec.longitude:
                try:
                    rec.set_location_from_coordinates(rec.latitude, rec.longitude)
                except Exception as e:
                    _logger.warning(f"Failed to update shape from lat/lon: {e}")

    # def write(self, vals):
    #     """Override write untuk sinkronisasi lat/lon <-> shape dan attachment"""
        
    #     # BAGIAN 1: Sinkronisasi lat/lon -> shape (sebelum write)
    #     if ('latitude' in vals or 'longitude' in vals) and 'shape' not in vals:
    #         for rec in self:
    #             lat = vals.get('latitude', rec.latitude)
    #             lon = vals.get('longitude', rec.longitude)
                
    #             if lat and lon and rec.id:
    #                 try:
    #                     self._cr.execute("""
    #                         UPDATE request_installment_order 
    #                         SET shape = ST_SetSRID(ST_MakePoint(%s, %s), 4326)
    #                         WHERE id = %s
    #                     """, (lon, lat, rec.id))
    #                 except Exception as e:
    #                     _logger.warning(f"Failed to sync lat/lon to shape: {e}")
        
    #     # Panggil super write
    #     result = super().write(vals)
        
    #     # BAGIAN 2: Update attachment ter-link
    #     if 'attachment_ids' in vals:
    #         for record in self:
    #             attachments = self.env['ir.attachment'].search([
    #                 ('res_model', '=', self._name),
    #                 ('res_id', '=', record.id),
    #                 ('mimetype', 'like', 'image/')
    #             ])
    #             attachments.write({
    #                 'res_model': self._name,
    #                 'res_id': record.id
    #             })
        
    #     # BAGIAN 3: Sinkronisasi shape -> lat/lon (setelah write)
    #     if 'shape' in vals and vals.get('shape'):
    #         if 'latitude' not in vals and 'longitude' not in vals:
    #             for rec in self:
    #                 if rec.shape and rec.id:
    #                     try:
    #                         self._cr.execute("""
    #                             SELECT ST_X(shape::geometry), ST_Y(shape::geometry)
    #                             FROM request_installment_order
    #                             WHERE id = %s
    #                         """, (rec.id,))
    #                         coord = self._cr.fetchone()
    #                         if coord:
    #                             self._cr.execute("""
    #                                 UPDATE request_installment_order 
    #                                 SET longitude = %s, latitude = %s
    #                                 WHERE id = %s
    #                             """, (coord[0], coord[1], rec.id))
    #                             rec.invalidate_cache(['longitude', 'latitude'])
    #                     except Exception as e:
    #                         _logger.warning(f"Failed to extract coords from shape: {e}")
        
    #     return result

    @api.depends('shape', 'latitude', 'longitude')
    def _compute_location_display(self):
        for rec in self:
            if rec.shape and hasattr(rec.shape, 'coords'):
                try:
                    lon, lat = rec.shape.coords[0], rec.shape.coords[1]
                    rec.location_display = f"Lat: {lat:.6f}, Lng: {lon:.6f}"
                except Exception:
                    rec.location_display = "PostGIS Geometry Set"
            elif rec.latitude and rec.longitude:
                rec.location_display = f"Lat: {rec.latitude:.6f}, Lng: {rec.longitude:.6f}"
            else:
                rec.location_display = "No location set"

    @api.depends('shape', 'latitude', 'longitude')
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
            elif rec.latitude and rec.longitude:
                rec.geo_wkt = f'POINT({rec.longitude} {rec.latitude})'
            else:
                rec.geo_wkt = False

    @api.constrains('latitude', 'longitude')
    def _check_coordinates(self):
        for rec in self:
            if rec.latitude and (rec.latitude < -90 or rec.latitude > 90):
                raise ValidationError(_('Latitude must be between -90 and 90 degrees.'))
            if rec.longitude and (rec.longitude < -180 or rec.longitude > 180):
                raise ValidationError(_('Longitude must be between -180 and 180 degrees.'))

    def set_location_from_coordinates(self, lat, lng):
        """Internal method: set shape dari lat/lon"""
        self.ensure_one()
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValidationError(_('Invalid coordinates.'))
        try:
            self._cr.execute("""
                UPDATE request_installment_order 
                SET shape = ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                WHERE id = %s
            """, (lng, lat, self.id))
            self.write({'latitude': lat, 'longitude': lng})
        except Exception as e:
            _logger.error("Failed to create PostGIS geometry: %s", e)
            raise ValidationError(_('Failed to create PostGIS geometry.'))
        return True

    def action_set_location_from_coordinates(self):
        self.ensure_one()
        if not self.latitude or not self.longitude:
            raise ValidationError(_('Please enter both latitude and longitude.'))
        return self.set_location_from_coordinates(self.latitude, self.longitude)

    def action_clear_location(self):
        self.write({'shape': False, 'latitude': False, 'longitude': False})
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
            'res_model': 'request.installment.order',
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
                            'title': cust.title,
                            'description': cust.description or '',
                        },
                        'geometry': {
                            'type': 'Point',
                            'coordinates': [cust.shape.coords[0], cust.shape.coords[1]]
                        }
                    })
            except Exception as e:
                _logger.warning("Failed to process geometry for %s: %s", cust.title, e)
        return {'type': 'FeatureCollection', 'features': features}