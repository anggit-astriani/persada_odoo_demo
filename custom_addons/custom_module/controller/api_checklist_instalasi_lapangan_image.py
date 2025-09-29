from odoo import http
from odoo.http import request, Response
import json
import base64

class ApiChecklistInstalasiLapanganImage(http.Controller):

    @http.route('/api/checklist_instalasi_lapangan_image', type='http', auth='none', methods=['GET'], csrf=False)
    def get_checklist_instalasi_lapangan_image(self, **params):
        limit = int(params.get('limit', 10))
        records = request.env['checklist.instalasi.lapangan.image'].sudo().search([], limit=limit)

        data = []
        base_url = request.httprequest.host_url.rstrip('/')
        for rec in records:
            checklist_instalasi_product = []
            for line in rec.checklist_instalasi_product_id:
                checklist_instalasi_product.append({
                    'title': line.title,
                    'sequence': line.sequence,
                })

            checklist_instalasi_product_criteria = []
            for line in rec.product_criteria_ids:
                checklist_instalasi_product_criteria.append({
                    'criteria': line.criteria,
                    'information': line.information,
                    'sequence': line.sequence,
                })

            checklist_instalasi_lapangan = []
            for line in rec.checklist_instalasi_lapangan_id:
                products = []
                for prod in line.product_line_ids:
                    products.append({
                        # 'checklist_product_id': line.checklist_product_id.id,
                        'product_name': prod.product_id.name,
                        'demand': prod.demand,
                        'quantity': prod.quantity,
                    })

                checklist_instalasi_lapangan.append({
                    'delivery_order': line.delivery_id.name,
                    'officer': line.officer_id.name,
                    'latitude': line.latitude,
                    'longitude': line.longitude,
                    'information': line.information,
                    'product_line': products
                })
            
            data.append({
                'checklist_instalasi_product_id': checklist_instalasi_product,
                'product_criteria_ids': checklist_instalasi_product_criteria,
                'checklist_instalasi_lapangan_id': checklist_instalasi_lapangan,
                # 'image': base64.b64encode(rec.image).decode()  if rec.image  else None,
                # 'image1': base64.b64encode(rec.image1).decode() if rec.image1 else None,
                # 'image2': base64.b64encode(rec.image2).decode() if rec.image2 else None,
                # 'image3': base64.b64encode(rec.image3).decode() if rec.image3 else None,
                'image_url':  base_url + '/web/image/checklist.instalasi.lapangan.image/%d/image'  % rec.id,
                'image1_url': base_url + '/web/image/checklist.instalasi.lapangan.image/%d/image1' % rec.id,
                'image2_url': base_url + '/web/image/checklist.instalasi.lapangan.image/%d/image2' % rec.id,
                'image3_url': base_url + '/web/image/checklist.instalasi.lapangan.image/%d/image3' % rec.id,
                'information': rec.information,
            })

        return Response(
            json.dumps({'ok': True, 'count': len(data), 'data': data}),
            headers=[('Content-Type', 'application/json')]
        )
    
    @http.route('/api/checklist_instalasi_lapangan', type='http', auth='public', methods=['POST'], csrf=False)
    def create_checklist_instalasi_lapangan(self, **params):
        try:
            body = json.loads(request.httprequest.data)
        except Exception:
            return Response(
                json.dumps({'ok': False, 'error': 'Invalid JSON format.'}),
                status=400,
                headers=[('Content-Type', 'application/json')]
            )

        try:
            values = {
                'checklist_instalasi_product_id': int(body.get('checklist_instalasi_product', 0)) or None,
                'checklist_instalasi_lapangan_id': int(body.get('checklist_instalasi_lapangan', 0)) or None,
                'product_id': int(body.get('product_id', 0)) or None,
                'image': body.get('image'),
                'image1': body.get('image1'),
                'image2': body.get('image2'),
                'image3': body.get('image3'),
                'information': body.get('information'),
            }

            # Validasi base64
            for key in ['image', 'image1', 'image2', 'image3']:
                if values.get(key):
                    try:
                        base64.b64decode(values[key])
                    except Exception:
                        return Response(
                            json.dumps({'ok': False, 'error': f'{key} is not valid base64.'}),
                            status=400,
                            headers=[('Content-Type', 'application/json')]
                        )

            new_rec = request.env['checklist.instalasi.lapangan.image'].sudo().create(values)

            return Response(
                json.dumps({'ok': True, 'id': new_rec.id, 'message': 'Gambar berhasil disimpan.'}),
                status=201,
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            return Response(
                json.dumps({'ok': False, 'error': str(e)}),
                status=500,
                headers=[('Content-Type', 'application/json')]
            )
        
    """
        ***contoh request untuk create dan update data
        {
            "product_id": 101,
            "information": "Foto diperbarui setelah inspeksi",
            "image": "/9j/4AAQSkZJRgABAQAAAQABAAD..."  // base64
        }
    """
    @http.route('/api/checklist_instalasi_lapangan_image/<int:delivery_id>', type='http', auth='public', methods=['PUT'], csrf=False)
    def update_checklist_instalasi_lapangan_image(self, delivery_id, **params):
        try:
            body = json.loads(request.httprequest.data)
        except Exception:
            return Response(
                json.dumps({'ok': False, 'error': 'Invalid JSON format.'}),
                status=400,
                headers=[('Content-Type', 'application/json')]
            )

        image_rec = request.env['checklist.instalasi.lapangan.image'].sudo().browse(delivery_id)
        if not image_rec.exists():
            return Response(
                json.dumps({'ok': False, 'error': 'Data tidak ditemukan.'}),
                status=404,
                headers=[('Content-Type', 'application/json')]
            )

        try:
            update_vals = {}

            # Update field numerik dan teks
            if 'checklist_instalasi_product_id' in body:
                update_vals['checklist_instalasi_product_id'] = int(body.get('checklist_instalasi_product_id', 0)) or None
            if 'checklist_instalasi_lapangan_id' in body:
                update_vals['checklist_instalasi_lapangan_id'] = int(body.get('checklist_instalasi_lapangan_id', 0)) or None
            if 'product_id' in body:
                update_vals['product_id'] = int(body.get('product_id', 0)) or None
            if 'information' in body:
                update_vals['information'] = body.get('information')

            # Validasi dan update gambar
            for key in ['image', 'image1', 'image2', 'image3']:
                if key in body and body[key]:
                    try:
                        base64.b64decode(body[key])
                        update_vals[key] = body[key]
                    except Exception:
                        return Response(
                            json.dumps({'ok': False, 'error': f'{key} is not valid base64.'}),
                            status=400,
                            headers=[('Content-Type', 'application/json')]
                        )

            image_rec.write(update_vals)

            return Response(
                json.dumps({'ok': True, 'id': image_rec.id, 'message': 'Data gambar berhasil diperbarui.'}),
                status=200,
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            return Response(
                json.dumps({'ok': False, 'error': str(e)}),
                status=500,
                headers=[('Content-Type', 'application/json')]
            )