from odoo import http
from odoo.http import request, Response
import json

class ApiChecklistInstalasiLapangan(http.Controller):

    @http.route('/api/checklist_instalasi_lapangan', type='http', auth='none', methods=['GET'], csrf=False)
    def get_checklist_instalasi_lapangan(self, **params):
        limit = int(params.get('limit', 10))
        records = request.env['checklist.instalasi.lapangan'].sudo().search([], limit=limit)

        data = []
        for rec in records:
            products = []
            for line in rec.product_line_ids:
                products.append({
                    # 'checklist_product_id': line.checklist_product_id.id,
                    'product_name': line.product_id.name,
                    'demand': line.demand,
                    'quantity': line.quantity,
                    
                })

            data.append({
                'delivery_order': rec.delivery_id.name,
                'officer': rec.officer_id.name,
                'latitude': rec.latitude,
                'longitude': rec.longitude,
                'information': rec.information,
                'product_line': products,
            })
        
        return Response(
            json.dumps({'ok': True, 'count': len(data), 'data': data}),
            headers=[('Content-Type', 'application/json')]
        )
    
    # API untuk menampilkan data image berdasarkan instalasi lapangan product
    @http.route('/api/checklist_instalasi_lapangan/<int:delivery_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def detail_checklist_instalasi_lapangan(self, delivery_id,**params):
        records = request.env['checklist.instalasi.lapangan'].sudo().browse(delivery_id)

        data = []
        for rec in records:
            products = []
            for line in rec.product_line_ids:

                products.append({
                    # 'checklist_product_id': line.checklist_product_id.id,
                    'product_name': line.product_id.name,
                    'demand': line.demand,
                    'quantity': line.quantity
                })

            data_images = []
            base_url = request.httprequest.host_url.rstrip('/')
            for image in rec.image_line_ids:
                checklist_instalasi_product = []
                for cip in image.checklist_instalasi_product_id:
                    checklist_instalasi_product.append({
                        'product_id': cip.product_id.name,
                        'title': cip.title,
                        'sequence': cip.sequence,
                    })

                checklist_instalasi_product_criteria = []
                for cipc in image.product_criteria_ids:
                    checklist_instalasi_product_criteria.append({
                        'criteria': cipc.criteria,
                        'information': cipc.information,
                        'sequence': cipc.sequence,
                    })

                data_images.append({
                    'checklist_instalasi_product_id': checklist_instalasi_product,
                    'product_criteria_ids': checklist_instalasi_product_criteria,
                    # 'checklist_instalasi_lapangan_id': checklist_instalasi_lapangan,
                    'image_url':  base_url + '/web/image/checklist.instalasi.lapangan.image/%d/image'  % rec.id,
                    'image1_url': base_url + '/web/image/checklist.instalasi.lapangan.image/%d/image1' % rec.id,
                    'image2_url': base_url + '/web/image/checklist.instalasi.lapangan.image/%d/image2' % rec.id,
                    'image3_url': base_url + '/web/image/checklist.instalasi.lapangan.image/%d/image3' % rec.id,
                    'information': image.information,
                    })

            data.append({
                'delivery_order': rec.delivery_id.name,
                'officer': rec.officer_id.name,
                'latitude': rec.latitude,
                'longitude': rec.longitude,
                'information': rec.information,
                'product_line': products,
                'checklist_instalasi': data_images
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
            # Siapkan data utama
            values = {
                'delivery_id': int(body.get('delivery_id', 0)) or None,
                'officer_id': int(body.get('officer_id', 0)) or None,
                'latitude': body.get('latitude'),
                'longitude': body.get('longitude'),
                'information': body.get('information'),
            }

            # Siapkan relasi One2many untuk product_line_ids
            product_lines = []
            for line in body.get('product_line_ids', []):
                product_lines.append((0, 0, {
                    'product_id': int(line.get('product_id', 0)) or None,
                    'demand': float(line.get('demand', 0)),
                    'quantity': float(line.get('quantity', 0)),
                }))
            values['product_line_ids'] = product_lines

            # Siapkan relasi One2many untuk image_line_ids
            image_lines = []
            for img in body.get('image_line_ids', []):
                image_lines.append((0, 0, {
                    'checklist_instalasi_product_id': int(img.get('checklist_instalasi_product_id', 0)) or None,
                    'product_id': int(img.get('product_id', 0)) or None,
                    'image': img.get('image'),
                    'image1': img.get('image1'),
                    'image2': img.get('image2'),
                    'image3': img.get('image3'),
                    'information': img.get('information'),
                }))
            values['image_line_ids'] = image_lines

            new_rec = request.env['checklist.instalasi.lapangan'].sudo().create(values)

            return Response(
                json.dumps({'ok': True, 'id': new_rec.id, 'message': 'Data checklist instalasi lapangan berhasil dibuat.'}),
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
        Payload untuk update dan create hampir sama, hanya saja pada update ID tidak perlu dikirimkan karena sudah ada di URL
        {
            "delivery_id": 12,
            "officer_id": 45,
            "latitude": "-6.260",
            "longitude": "106.798",
            "information": "Update lokasi dan officer",
            "product_line_ids": [
                {
                "product_id": 101,
                "demand": 10,
                "quantity": 8
                }
            ],
            "image_line_ids": [
                {
                "checklist_instalasi_product_id": 201,
                "product_id": 101,
                "image": "/9j/4AAQSkZJRgABAQAAAQABAAD...",
                "information": "Foto baru setelah instalasi"
                }
            ]
        }
    """
    @http.route('/api/checklist_instalasi_lapangan/<int:delivery_id>', type='http', auth='public', methods=['PUT'], csrf=False)
    def update_checklist_instalasi_lapangan(self, delivery_id, **params):
        try:
            body = json.loads(request.httprequest.data)
        except Exception:
            return Response(
                json.dumps({'ok': False, 'error': 'Invalid JSON format.'}),
                status=400,
                headers=[('Content-Type', 'application/json')]
            )

        checklist = request.env['checklist.instalasi.lapangan'].sudo().browse(delivery_id)
        if not checklist.exists():
            return Response(
                json.dumps({'ok': False, 'error': 'Checklist not found.'}),
                status=404,
                headers=[('Content-Type', 'application/json')]
            )

        try:
            checklist.write({
                # 'delivery_id': int(body.get('delivery_id', checklist.delivery_id.id)) or None,
                'officer_id': int(body.get('officer_id', checklist.officer_id.id)) or None,
                'latitude': body.get('latitude', checklist.latitude),
                'longitude': body.get('longitude', checklist.longitude),
                'information': body.get('information', checklist.information),
            })

            # Optional: replace product_line_ids
            # if 'product_line_ids' in body:
            #     checklist.product_line_ids.unlink()
            #     new_products = []
            #     for line in body['product_line_ids']:
            #         new_products.append((0, 0, {
            #             'product_id': int(line.get('product_id', 0)) or None,
            #             'demand': float(line.get('demand', 0)),
            #             'quantity': float(line.get('quantity', 0)),
            #         }))
            #     checklist.write({'product_line_ids': new_products})

            # Optional: replace image_line_ids
            if 'image_line_ids' in body:
                checklist.image_line_ids.unlink()
                new_images = []
                for img in body['image_line_ids']:
                    new_images.append((0, 0, {
                        'checklist_instalasi_product_id': int(img.get('checklist_instalasi_product_id', 0)) or None,
                        'product_id': int(img.get('product_id', 0)) or None,
                        'image': img.get('image'),
                        'image1': img.get('image1'),
                        'image2': img.get('image2'),
                        'image3': img.get('image3'),
                        'information': img.get('information'),
                    }))
                checklist.write({'image_line_ids': new_images})

            return Response(
                json.dumps({'ok': True, 'id': checklist.id, 'message': 'Checklist instalasi lapangan berhasil diperbarui.'}),
                status=200,
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            return Response(
                json.dumps({'ok': False, 'error': str(e)}),
                status=500,
                headers=[('Content-Type', 'application/json')]
            )





    # API untuk menampilkan data image berdasarkan instalasi lapangan product line
    # Tetapi masih belum bisa karena tidak ada id yang terhubung antara product line dan juga image
    @http.route('/api/checklist_instalasi_lapangan/line/<int:delivery_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def detail_checklist_instalasi_lapangan_line(self, delivery_id,**params):
        records = request.env['checklist.instalasi.lapangan'].sudo().browse(delivery_id)

        data = []
        for rec in records:
            products = []
            for line in rec.product_line_ids:
                
                data_images = []
                base_url = request.httprequest.host_url.rstrip('/')
                for image in line.image_line_ids:
                    checklist_instalasi_product = []
                    for cip in image.checklist_instalasi_product_id:
                        checklist_instalasi_product.append({
                            'title': cip.title,
                            'sequence': cip.sequence,
                        })

                    checklist_instalasi_product_criteria = []
                    for cipc in image.product_criteria_ids:
                        checklist_instalasi_product_criteria.append({
                            'criteria': cipc.criteria,
                            'information': cipc.information,
                            'sequence': cipc.sequence,
                        })

                    data_images.append({
                        'checklist_instalasi_product_id': checklist_instalasi_product,
                        'product_criteria_ids': checklist_instalasi_product_criteria,
                        # 'checklist_instalasi_lapangan_id': checklist_instalasi_lapangan,
                        'image_url':  base_url + '/web/image/checklist.instalasi.lapangan.image/%d/image'  % rec.id,
                        'image1_url': base_url + '/web/image/checklist.instalasi.lapangan.image/%d/image1' % rec.id,
                        'image2_url': base_url + '/web/image/checklist.instalasi.lapangan.image/%d/image2' % rec.id,
                        'image3_url': base_url + '/web/image/checklist.instalasi.lapangan.image/%d/image3' % rec.id,
                        'information': image.information,
                        })


                products.append({
                    # 'checklist_product_id': line.checklist_product_id.id,
                    'product_name': line.product_id.name,
                    'demand': line.demand,
                    'quantity': line.quantity,
                    'checklist_instalasi': data_images
                })

            data.append({
                'delivery_order': rec.delivery_id.name,
                'officer': rec.officer_id.name,
                'latitude': rec.latitude,
                'longitude': rec.longitude,
                'information': rec.information,
                'product_line': products,
            })

        
        
        return Response(
            json.dumps({'ok': True, 'count': len(data), 'data': data}),
            headers=[('Content-Type', 'application/json')]
        )