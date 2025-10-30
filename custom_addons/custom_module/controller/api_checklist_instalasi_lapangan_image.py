from odoo import http
from odoo.http import request, Response
import json
import base64

class ApiChecklistInstalasiLapanganImage(http.Controller):

    @http.route('/api/checklist_instalasi_lapangan_image', type='http', auth='none', methods=['GET'], csrf=False)
    def get_checklist_instalasi_lapangan_image(self, **params):
        """
        Endpoint API untuk mengambil data checklist instalasi lapangan beserta gambar.
        URL: /api/checklist_instalasi_lapangan_image
        Method: GET
        """
        # Ambil parameter limit dari query string, default 10
        limit = int(params.get('limit', 10))

        # Ambil record checklist.instalasi.lapangan.image, batasi sesuai limit
        records = request.env['checklist.instalasi.lapangan.image'].sudo().search([], limit=limit)

        data = []  # List untuk menampung data response
        base_url = request.httprequest.host_url.rstrip('/')  # Base URL server

        # Loop setiap record checklist
        for rec in records:
            checklist_instalasi_product = []
            # Ambil detail checklist_instalasi_product_id
            for line in rec.checklist_instalasi_product_id:
                checklist_instalasi_product.append({
                    'title': line.title,       # Judul checklist produk
                    'sequence': line.sequence, # Urutan checklist
                })

            checklist_instalasi_product_criteria = []
            # Ambil criteria untuk setiap checklist produk
            for line in rec.product_criteria_ids:
                checklist_instalasi_product_criteria.append({
                    'criteria': line.criteria,        # Nama criteria
                    'information': line.information,  # Keterangan criteria
                    'sequence': line.sequence,        # Urutan criteria
                })

            checklist_instalasi_lapangan = []
            # Ambil data lapangan (delivery) yang terkait
            for line in rec.checklist_instalasi_lapangan_id:
                products = []
                # Ambil setiap product line di lapangan
                for prod in line.product_line_ids:
                    products.append({
                        'product_name': prod.product_id.name,  # Nama produk
                        'demand': prod.demand,                 # Jumlah permintaan
                        'quantity': prod.quantity,             # Jumlah aktual
                    })

                checklist_instalasi_lapangan.append({
                    'delivery_order': line.delivery_id.name,  # Nama DO
                    'officer': line.officer_id.name,          # Nama petugas
                    'latitude': line.latitude,                # Koordinat latitude
                    'longitude': line.longitude,              # Koordinat longitude
                    'information': line.information,          # Info tambahan
                    'product_line': products                  # List produk di DO
                })

            # Gabungkan semua data untuk satu record
            data.append({
                'checklist_instalasi_product_id': checklist_instalasi_product,
                'product_criteria_ids': checklist_instalasi_product_criteria,
                'checklist_instalasi_lapangan_id': checklist_instalasi_lapangan,
                # Buat URL untuk mengakses gambar via web/image
                # 'image': base64.b64encode(rec.image).decode()  if rec.image  else None,
                # 'image1': base64.b64encode(rec.image1).decode() if rec.image1 else None,
                # 'image2': base64.b64encode(rec.image2).decode() if rec.image2 else None,
                # 'image3': base64.b64encode(rec.image3).decode() if rec.image3 else None,
                'image_url':  base_url + '/web/image/checklist.instalasi.lapangan.image/%d/image'  % rec.id,
                'image1_url': base_url + '/web/image/checklist.instalasi.lapangan.image/%d/image1' % rec.id,
                'image2_url': base_url + '/web/image/checklist.instalasi.lapangan.image/%d/image2' % rec.id,
                'image3_url': base_url + '/web/image/checklist.instalasi.lapangan.image/%d/image3' % rec.id,
                'information': rec.information,  # Info tambahan untuk record
            })

        # Return response JSON
        return Response(
            json.dumps({'ok': True, 'count': len(data), 'data': data}),
            headers=[('Content-Type', 'application/json')]
        )
    
    @http.route('/api/checklist_instalasi_lapangan', type='http', auth='public', methods=['POST'], csrf=False)
    def create_checklist_instalasi_lapangan(self, **params):
        """
        Endpoint API untuk membuat record baru checklist instalasi lapangan.
        URL: /api/checklist_instalasi_lapangan
        Method: POST
        """
        try:
            # Ambil body request dan parsing JSON
            body = json.loads(request.httprequest.data)
        except Exception:
            # Jika JSON tidak valid, return error 400
            return Response(
                json.dumps({'ok': False, 'error': 'Invalid JSON format.'}),
                status=400,
                headers=[('Content-Type', 'application/json')]
            )

        try:
            # Mapping JSON body ke dictionary values untuk create record
            values = {
                'checklist_instalasi_product_id': int(body.get('checklist_instalasi_product', 0)) or None,  # Convert ke int, jika 0 -> None
                'checklist_instalasi_lapangan_id': int(body.get('checklist_instalasi_lapangan', 0)) or None,
                'product_id': int(body.get('product_id', 0)) or None,
                'image': body.get('image'),   # Base64 string gambar utama
                'image1': body.get('image1'), # Base64 string gambar tambahan 1
                'image2': body.get('image2'), # Base64 string gambar tambahan 2
                'image3': body.get('image3'), # Base64 string gambar tambahan 3
                'information': body.get('information'), # Field teks tambahan
            }

            # ===============================
            # Validasi semua gambar yang dikirim
            # ===============================
            for key in ['image', 'image1', 'image2', 'image3']:
                if values.get(key):
                    try:
                        base64.b64decode(values[key])  # Pastikan format valid base64
                    except Exception:
                        # Jika tidak valid base64, return error 400
                        return Response(
                            json.dumps({'ok': False, 'error': f'{key} is not valid base64.'}),
                            status=400,
                            headers=[('Content-Type', 'application/json')]
                        )

            # Buat record baru di model checklist.instalasi.lapangan.image
            # sudo() digunakan untuk bypass access rights
            new_rec = request.env['checklist.instalasi.lapangan.image'].sudo().create(values)

            # Return response sukses 201 Created beserta id record baru
            return Response(
                json.dumps({'ok': True, 'id': new_rec.id, 'message': 'Gambar berhasil disimpan.'}),
                status=201,
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            # Tangkap semua exception lain, return 500 Internal Server Error
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
        """
        Endpoint API untuk update data dan gambar checklist instalasi lapangan.
        URL: /api/checklist_instalasi_lapangan_image/<delivery_id>
        Method: PUT
        """
        try:
            # Ambil body request dan parsing JSON
            body = json.loads(request.httprequest.data)
        except Exception:
            # Jika JSON tidak valid, return error 400
            return Response(
                json.dumps({'ok': False, 'error': 'Invalid JSON format.'}),
                status=400,
                headers=[('Content-Type', 'application/json')]
            )

        # Cari record checklist berdasarkan delivery_id, bypass access rights
        image_rec = request.env['checklist.instalasi.lapangan.image'].sudo().browse(delivery_id)
        if not image_rec.exists():
            # Jika record tidak ditemukan, return 404
            return Response(
                json.dumps({'ok': False, 'error': 'Data tidak ditemukan.'}),
                status=404,
                headers=[('Content-Type', 'application/json')]
            )

        try:
            update_vals = {}  # Dictionary untuk menampung data yang akan diupdate

            # ===============================
            # Update field numerik / relasi / teks
            # ===============================
            if 'checklist_instalasi_product_id' in body:
                # Konversi ke int, jika 0 maka jadi None
                update_vals['checklist_instalasi_product_id'] = int(body.get('checklist_instalasi_product_id', 0)) or None
            if 'checklist_instalasi_lapangan_id' in body:
                update_vals['checklist_instalasi_lapangan_id'] = int(body.get('checklist_instalasi_lapangan_id', 0)) or None
            if 'product_id' in body:
                update_vals['product_id'] = int(body.get('product_id', 0)) or None
            if 'information' in body:
                update_vals['information'] = body.get('information')  # Field teks tambahan

            # ===============================
            # Validasi dan update gambar (base64)
            # ===============================
            for key in ['image', 'image1', 'image2', 'image3']:
                if key in body and body[key]:
                    try:
                        base64.b64decode(body[key])  # Validasi base64
                        update_vals[key] = body[key]  # Jika valid, simpan ke update_vals
                    except Exception:
                        # Jika tidak valid base64, return error 400
                        return Response(
                            json.dumps({'ok': False, 'error': f'{key} is not valid base64.'}),
                            status=400,
                            headers=[('Content-Type', 'application/json')]
                        )

            # Update record checklist dengan semua field yang valid
            image_rec.write(update_vals)

            # Return response sukses
            return Response(
                json.dumps({'ok': True, 'id': image_rec.id, 'message': 'Data gambar berhasil diperbarui.'}),
                status=200,
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            # Tangkap semua exception lain, return 500
            return Response(
                json.dumps({'ok': False, 'error': str(e)}),
                status=500,
                headers=[('Content-Type', 'application/json')]
            )
