from flask import Flask,render_template,request,flash, redirect,session,jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash,generate_password_hash
import json
import sqlite3
import os
from promptpay import qrcode as pp_qrcode  
import qrcode 
import io, base64
from datetime import datetime, date
from collections import defaultdict
import uuid





app = Flask(__name__)


app.secret_key = 'your_secret'
db_garden = 'garden.db'
def get_db():
    conn = sqlite3.connect(db_garden, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS "seller" (
	            id_seller  INTEGER PRIMARY KEY AUTOINCREMENT,
	            email TEXT NOT NULL UNIQUE ,
	            password TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0
            );
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS "list_menu" (
	            id_menu  INTEGER PRIMARY KEY AUTOINCREMENT,
	            menu_name TEXT,
	            menu_price TEXT,
                category TEXT,
                img_path TEXT,
                details TEXT,
                sweetness TEXT DEFAULT '[]' 
            );
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS "menu_option" (
	            id_option  INTEGER PRIMARY KEY AUTOINCREMENT,
	            option_name TEXT
            );
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS "menu_option_list" (
	            id_menu INTEGER,
                id_option INTEGER,
                price_add INTEGER DEFAULT 0,
                FOREIGN KEY (id_menu) REFERENCES list_menu(id_menu),
                FOREIGN KEY (id_option) REFERENCES menu_option(id_option)
            );
        """)
        db.commit()

@app.route('/')
def index():
    is_logged_in = 'admin_id' in session  
    is_admin = session.get('is_admin', False)

    # ตัวอย่าง ตั้งค่า role
    if 'role' not in session:
        session['role'] = 'customer'  # หรือ 'owner'

    # ตัวอย่าง store status
    if 'store_open' not in session:
        session['store_open'] = True  # ร้านเปิดโดย default

    db = get_db()
    menus = db.execute('SELECT * FROM list_menu').fetchall()
    menus_list = []
    for menu in menus:
        menus_list.append({
            'id_menu': menu['id_menu'],
            'menu_name': menu['menu_name'],
            'menu_price': menu['menu_price'],
            'category': menu['category'],
            'img_path': menu['img_path'],
            'details': menu['details'],
            'sweetness': json.loads(menu['sweetness'] or '[]'),
            'option_types': json.loads(menu['option_types'] or '[]')
        })

    db.close()

    return render_template(
        'index.html',
        menus=menus_list,
        is_logged_in=is_logged_in,
        is_admin=is_admin,
        role=session.get('role'),         # ส่ง role เข้า template
        store_open=session.get('store_open')  # ส่ง store_open เข้า template
    )



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']   
        password = request.form['password']
        try:
            with get_db() as db:
                # ค้นหาผู้ใช้ในฐานข้อมูล
                seller = db.execute("SELECT * FROM seller WHERE email = ?", (email,)).fetchone()

                # ถ้าผู้ใช้ถูกต้องและรหัสผ่านตรง
                if seller and check_password_hash(seller['password'], password):
                    if seller['is_admin'] == 1:  # ร้านค้า
                        session['admin_id'] = seller['id_seller']
                        session['role'] = 'owner'   # ใช้ role ตรวจสอบแทน is_admin
                    else:
                        # ลูกค้า หรือ user ปกติ
                        session['user_id'] = seller['id_seller']
                    return redirect('/')

                else:
                    print("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
                    return render_template('login.html', error="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        except Exception as e:
            print("เกิดข้อผิดพลาด:", e)
            return "เกิดข้อผิดพลาด"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        store_code = request.form.get('code_store')
        is_admin = 1 if store_code == '1234' else 0
        try:
            with get_db() as db:
                db.execute("INSERT INTO seller (email, password, is_admin) VALUES (?, ?)", (email, hashed_password,is_admin))
                db.commit()
                print("บันทึกแล้ว")
                return redirect('/login')
        except sqlite3.IntegrityError:
            print("error")
    return render_template('register.html')

UPLOAD_FOLDER = 'static/uploads'
@app.route('/add-menu', methods=['GET','POST'])
def addMenu():
    if request.method == 'POST':
        name = request.form['menu_name']
        base_price = request.form['menu_price']
        option = request.form.getlist('option_type')
        cagatorie = request.form['cagatories-add']
        details = request.form.get('detail-menu-add', '').strip()
        if not details:
            details = "ไม่มีรายละเอียด"

    
        sweetness = request.form.getlist('sweetness')  # จะได้เป็น list เช่น ["หวานมาก","หวานน้อย"]
        sweetness_json = json.dumps(sweetness, ensure_ascii=False)  # เก็บเป็น JSON string

        option_price = {}
        image_path = ''

        for opt in option:
            val = request.form.get(f'option_type_{opt}', 0) or 0
            option_price[opt] = int(val)

        img = request.files['menu_image']
        if img and img.filename != '':
            filename = secure_filename(img.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            img.save(image_path)

        try:
            with get_db() as db:
                cursor = db.execute('''
                    INSERT INTO list_menu (menu_name, menu_price, category, img_path, details, sweetness)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, base_price, cagatorie, image_path, details, sweetness_json))
                id_menu = cursor.lastrowid

                for opt_id, add_price in option_price.items():
                    db.execute('''
                        INSERT INTO menu_option_list (id_menu, id_option, price_add)
                        VALUES (?, ?, ?)
                    ''', (id_menu, opt_id, add_price))

                db.commit()
                flash('เพิ่มเมนูสำเร็จ', 'success')
                return redirect('/')

        except Exception as e:
            print('Error:', e)
            flash('เกิดข้อผิดพลาด', 'error')

    return redirect('/')


@app.route('/api/menus')
def add_menus():
    db = get_db()
    menus = db.execute('SELECT * FROM list_menu').fetchall()
    option = db.execute('SELECT * FROM menu_option').fetchall()
    menu_option_list = db.execute('SELECT * FROM menu_option_list').fetchall()

    db.close()
    
    menus_list = []
    option_list = []
    menu_options = []
    for menu in menus:
        menus_list.append({
            'id_menu':menu['id_menu'],
            'menu_name':menu['menu_name'],
            'menu_price':menu['menu_price'],
            'category':menu['category'],
            'img_path':menu['img_path'],
            'details':menu['details'],
            'sweetness': json.loads(menu['sweetness'] or '[]')
        })
    for opt in option:
        option_list.append({
            'id_option':opt['id_option'],
            'option_name':opt['option_name']
        })
    for optli in menu_option_list:
        menu_options.append({
            'id_menu':optli['id_menu'],
            'id_option':optli['id_option'],
            'price_add':optli['price_add']
        })
    is_admin_value = session.get('role') == 'owner'
    return jsonify({
        'menus': menus_list,
        'options': option_list,
        'menu_option_prices': menu_options,
        "is_admin": is_admin_value
    })
@app.route('/api/menus/<int:id_menu>', methods=['DELETE'])
def delete_menu(id_menu):
    if session.get('role') != 'owner':
        return jsonify({'error': 'unauthorized'}), 403

    db = get_db()
    db.execute('DELETE FROM list_menu WHERE id_menu = ?', (id_menu,))
    db.commit()
    db.close()
    return jsonify({'success': True})

PROMPTPAY_ACCOUNT = "0633796360"

@app.route("/create_qr", methods=["POST"])
def create_qr():
    data = request.get_json()
    cart = data.get("cart", [])

    # คำนวณยอดรวม
    total = sum(float(item["price"]) * int(item.get("qty", 1)) for item in cart)

  
    payload = pp_qrcode.generate_payload(PROMPTPAY_ACCOUNT, amount=total)

    qr_img = qrcode.make(payload)

  
    buffered = io.BytesIO()
    qr_img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return jsonify({
        "qr_payload": img_str,   # base64 พร้อมใช้งาน
        "total": f"{total:.2f}"
    })

@app.route('/confirm_payment', methods=['POST'])
def confirm_payment():
    nickname = request.form.get('nickname')
    phone = request.form.get('phone')
    note = request.form.get('note')
    cart = request.form.get('cart')  # JSON string จาก JS
    slip = request.files.get('slip')

    slip_filename = None
    if slip:
        filename = secure_filename(slip.filename)
        save_dir = os.path.join('static', 'slips')
        os.makedirs(save_dir, exist_ok=True)
        slip.save(os.path.join(save_dir, filename))
        slip_filename = filename

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cancel_token = str(uuid.uuid4())  # สร้าง cancel_token ใหม่

    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO orders (nickname, phone, note, cart_data, status, timestamp, slip_filename,cancel_token)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nickname, phone, note, cart, "รอดำเนินการ", timestamp, slip_filename ,cancel_token))

        return jsonify({'success': True, 'message': 'บันทึกออเดอร์เรียบร้อย', 'cancel_token': cancel_token})
    except Exception as e:
        print("Error:", e)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/track-orders', methods=['GET'])
def track_orders():
    with get_db() as db:
        # ลูกค้าเห็นเฉพาะออเดอร์ที่ยังไม่ "รับแล้ว"
        orders = db.execute("""
            SELECT id, nickname, timestamp, status ,cancel_token
            FROM orders 
            WHERE status != 'รับแล้ว'
            ORDER BY timestamp ASC
        """).fetchall()

    return render_template('track_orders_customer.html', orders=orders)


@app.route('/track-orders/<int:order_id>', methods=['GET'])
def view_order(order_id):
    with get_db() as db:
        order = db.execute("""
            SELECT id, nickname, status, timestamp, cart_data 
            FROM orders 
            WHERE id = ?
        """, (order_id,)).fetchone()

        if order:
            cart = json.loads(order['cart_data'])  # แปลง JSON เป็น list
            return render_template('view_order_customer.html', order=order, cart=cart)

    return "ไม่พบคำสั่งซื้อนี้"


# --------------------
@app.route('/manage-orders', methods=['GET'])
def manage_orders():
    if session.get("role") != "owner":
        return "Unauthorized", 403

    with get_db() as db:
        # ดึงทุกคำสั่งซื้อที่ยังไม่ถึง "รับแล้ว"
        rows = db.execute(
            "SELECT id, nickname, timestamp, status, cancel_token FROM orders WHERE status != ? ORDER BY timestamp ASC",
            ("รับแล้ว",)
        ).fetchall()

        # แปลง Row เป็น dict
        orders = [dict(row) for row in rows]

    return render_template('manage_orders.html', orders=orders)



@app.route('/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    if session.get("role") != "owner":
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    try:
        data = request.get_json()
        new_status = data.get("status")
        if not new_status:
            return jsonify({"success": False, "error": "Missing status"}), 400

        with get_db() as db:
            # อัปเดตสถานะ
            db.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))

            # ถ้าเปลี่ยนเป็น "รับแล้ว" → บันทึก order_items
            if new_status == "รับแล้ว":
                order = db.execute("SELECT cart_data FROM orders WHERE id = ?", (order_id,)).fetchone()
                cart_list = json.loads(order["cart_data"])
                for item in cart_list:
                    # ใช้ qty จริง ๆ จาก cart_data
                    db.execute("""
                        INSERT INTO order_items (order_id, id_menu, qty, price)
                        VALUES (?, ?, ?, ?)
                    """, (order_id, item['id_menu'], int(item['qty']), item['price']))


            db.commit()
        return jsonify({"success": True})
    except Exception as e:
        # log ข้อผิดพลาด
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500




@app.route('/order/<int:order_id>')
def order_details(order_id):
    if session.get("role") != "owner":
        return "Unauthorized", 403

    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        return "ไม่พบคำสั่งซื้อ", 404

    # สมมติคุณเก็บ cart เป็น JSON
    cart = json.loads(order['cart_data'])  

    # คำนวณราคารวม
    total_price = sum(item['price'] * item['qty'] for item in cart)

    db.close()
    return render_template('order_details.html', order=order, cart=cart, total_price=total_price)

@app.route('/order_history')
def order_history():
    if session.get("role") != "owner":
        return "Unauthorized", 403

    db = get_db()
    # เลือกเฉพาะคำสั่งซื้อที่ status = 'รับแล้ว'
    orders = db.execute("SELECT * FROM orders WHERE status = 'รับแล้ว' ORDER BY timestamp DESC").fetchall()
    db.close()
    return render_template('order_history.html', orders=orders)



@app.route("/update-menu", methods=["POST"])
def update_menu():
    menu_id = request.form.get("id_menu")
    name = request.form.get("menu_name")
    price = request.form.get("menu_price")
    details = request.form.get("detail-menu-edit")
    file = request.files.get("menu_image")

    # รับค่าหวาน
    sweetness_list = request.form.getlist("sweetness")

    # รับ option + ราคาที่เลือก
    option_json = request.form.get("edit_options", "[]")
    option_list = json.loads(option_json)  # [{"id_option":1,"price_add":5}, ...]

    db = get_db()

    # อัปเดตรูป
    old_img = db.execute("SELECT img_path FROM list_menu WHERE id_menu = ?", (menu_id,)).fetchone()["img_path"]
    if file and file.filename != "":
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        img_path = f"/static/uploads/{filename}"
    else:
        img_path = old_img

    # UPDATE ข้อมูลเมนูหลัก
    db.execute(
        "UPDATE list_menu SET menu_name=?, menu_price=?, details=?, img_path=?, sweetness=? WHERE id_menu=?",
        (name, price, details, img_path, json.dumps(sweetness_list), menu_id)
    )

    # UPDATE menu_option_list: ลบก่อนแล้วเพิ่มใหม่
    db.execute("DELETE FROM menu_option_list WHERE id_menu=?", (menu_id,))
    for opt in option_list:
        db.execute(
            "INSERT INTO menu_option_list (id_menu, id_option, price_add) VALUES (?, ?, ?)",
            (menu_id, opt["id_option"], opt["price_add"])
        )

    db.commit()
    db.close()
    return redirect("/")

def get_order_data(category=None, date_filter=None, start_date=None, end_date=None):
    conn = sqlite3.connect("garden.db")
    cursor = conn.cursor()

    query = """
        SELECT m.menu_name, SUM(oi.qty) as total_qty, SUM(oi.qty * m.menu_price) as total_price
        FROM order_items oi
        JOIN list_menu m ON oi.id_menu = m.id_menu
        JOIN orders o ON oi.order_id = o.id
        WHERE 1=1
    """
    params = []

    today = date.today()

    # Filter by category
    if category:
        query += " AND TRIM(m.category) = ?"
        params.append(category.strip())

    # Filter by date
    if date_filter == "today":
        query += " AND DATE(o.timestamp) = ?"
        params.append(today)
    elif date_filter == "month":
        query += " AND strftime('%Y-%m', o.timestamp) = ?"
        params.append(today.strftime("%Y-%m"))
    elif date_filter == "year":
        query += " AND strftime('%Y', o.timestamp) = ?"
        params.append(today.strftime("%Y"))
    elif date_filter == "custom" and start_date and end_date:
        query += " AND DATE(o.timestamp) BETWEEN ? AND ?"
        params.extend([start_date, end_date])

    query += " GROUP BY m.menu_name"

    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()
    return data



@app.route("/dashboard")
def dashboard():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    category = request.args.get("category", "")
    date_filter = request.args.get("date_filter", "today")
    top_n = int(request.args.get("top_n", 5))  # Top N

    # ดึงข้อมูลทั้งหมดตามหมวด/วันที่
    category_data = get_order_data(category, date_filter, start_date, end_date)

    # ยอดรวมทั้งหมด (ตามหมวดที่เลือก)
    total_revenue = sum(row[2] for row in category_data) if category_data else 0

    # Sort Top N ตาม total_price สำหรับกราฟ
    top_data = sorted(category_data, key=lambda x: x[2], reverse=True)[:top_n]

    category_labels = [row[0] for row in top_data]
    category_values = [row[2] for row in top_data]  # ยอดเงิน

    return render_template("dashboard.html",
                           category_labels=category_labels,
                           category_values=category_values,
                           total_revenue=total_revenue,
                           selected_category=category,
                           selected_date_filter=date_filter,
                           start_date=start_date,
                           end_date=end_date,
                           top_n=top_n)


@app.route('/cancel_order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    role = session.get('role')
    with get_db() as db:
        order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            return "ไม่พบออร์เดอร์", 404

        # สำหรับลูกค้า ตรวจสอบ cancel_token
        if role != 'owner':
            token = request.form.get('token')
            if not token or token != order['cancel_token']:
                return "ไม่ได้รับอนุญาตให้ยกเลิกออร์เดอร์นี้", 403

        # ลบออร์เดอร์และรายการเมนู
        db.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        db.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        db.commit()

    return f"ออร์เดอร์ #{order_id} ถูกยกเลิกเรียบร้อยแล้ว"




@app.route('/api/orders', methods=['GET'])
def api_orders():
    """
    ดึงคำสั่งซื้อทั้งหมดที่ยังไม่ "รับแล้ว" พร้อม cancel_token
    ใช้ nickname/phone หรือไม่ก็ให้ลูกค้าใส่ cancel_token เพื่อยืนยันการยกเลิก
    """
    db = get_db()
    
    # ดึงทุกออร์เดอร์ที่ยังไม่ "รับแล้ว"
    orders = db.execute("""
        SELECT id, nickname, status, timestamp, cancel_token
        FROM orders
        WHERE status != 'รับแล้ว'
        ORDER BY timestamp ASC
    """).fetchall()
    db.close()

    orders_list = []
    for order in orders:
        orders_list.append({
            "id": order["id"],
            "nickname": order["nickname"],
            "status": order["status"],
            "timestamp": order["timestamp"],
            "cancel_token": order["cancel_token"]
        })

    return jsonify({"orders": orders_list})
def get_daily_sales(start_date=None, end_date=None):
    conn = sqlite3.connect("garden.db")
    cursor = conn.cursor()

    query = """
        SELECT DATE(o.timestamp) as day, SUM(oi.qty) as total_sales
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE 1=1
    """
    params = []

    if start_date and end_date:
        query += " AND DATE(o.timestamp) BETWEEN ? AND ?"
        params.extend([start_date, end_date])

    query += " GROUP BY day ORDER BY day"

    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()
    return data
@app.route("/api/orders_data")
def api_orders_data():
    category = request.args.get("category", "")
    date_filter = request.args.get("date_filter", "today")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    top_n = int(request.args.get("top_n", 5))

    # ดึงข้อมูล (โครงสร้าง row สมมติว่า = (ชื่อเมนู, จำนวนขาย, ยอดขายรวม))
    data = get_order_data(category, date_filter, start_date, end_date)

    # รวมยอดทั้งหมด
    total_revenue = sum(row[2] for row in data) if data else 0
    total_quantity = sum(row[1] for row in data) if data else 0

    # เลือก top ตามยอดขายรวม
    top_data = sorted(data, key=lambda x: x[2], reverse=True)[:top_n]

    labels = [row[0] for row in top_data]       # ชื่อเมนู
    quantities = [row[1] for row in top_data]   # จำนวนขาย
    values = [row[2] for row in top_data]       # ยอดขายรวม

    return jsonify({
        "labels": labels,
        "quantities": quantities,
        "values": values,
        "total_revenue": total_revenue,
        "total_quantity": total_quantity
    })


@app.route("/api/check_new_orders")
def api_check_new_orders():
    with get_db() as db:
        count = db.execute(
            "SELECT COUNT(*) FROM orders WHERE status = ?",
            ("รอดำเนินการ",)
        ).fetchone()[0]
    return jsonify({"new_orders": count})

@app.route('/toggle_store', methods=['POST'])
def toggle_store():
    if session.get('role') != 'owner':
        return jsonify({'error': 'ไม่ได้รับอนุญาต'}), 403

    # สลับสถานะร้าน
    session['store_open'] = not session.get('store_open', True)
    return jsonify({'store_open': session['store_open']})

# API สำหรับลูกค้าเช็คสถานะร้าน
@app.route('/api/store_status')
def store_status():
    return jsonify({'store_open': session.get('store_open', True)})


if __name__ == '__main__':
    
    init_db()
    app.run(debug=True ,host='0.0.0.0', port=5000 ,threaded=False)