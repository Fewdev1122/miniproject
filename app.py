from flask import Flask,render_template,request,flash, redirect,session,jsonify,send_file
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash,generate_password_hash
import json
import sqlite3
import os
from promptpay import qrcode as pp_qrcode  
import qrcode 
import io, base64




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
                details TEXT
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
    
    return render_template('index.html',is_logged_in=is_logged_in, is_admin=is_admin,)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']   
        password = request.form['password']
        try:
            with get_db() as db:
                seller = db.execute("SELECT * FROM seller WHERE email = ?", (email,)).fetchone()
                if seller and check_password_hash(seller['password'], password):
                    if seller['is_admin'] == 1:
                        session['admin_id'] = seller['id_seller']
                        session['is_admin'] = True
                    print("เข้าสู่ระบบสำเร็จ")
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

        # ✅ เก็บความหวาน
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
    is_admin_value = session.get('is_admin', False) 
    return jsonify({
        'menus': menus_list,
        'options': option_list,
        'menu_option_prices': menu_options,
        "is_admin": is_admin_value
    })
@app.route('/api/menus/<int:id_menu>', methods=['DELETE'])
def delete_menu(id_menu):
    if not session.get('is_admin'):         # กันคนที่ไม่ใช่ admin
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

    # ✅ generate payload จาก promptpay
    payload = pp_qrcode.generate_payload(PROMPTPAY_ACCOUNT, amount=total)

    # ✅ สร้าง QR code จาก payload
    qr_img = qrcode.make(payload)

    # ✅ แปลงเป็น base64 string
    buffered = io.BytesIO()
    qr_img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return jsonify({
        "qr_payload": img_str,   # base64 พร้อมใช้งาน
        "total": f"{total:.2f}"
    })




if __name__ == '__main__':
    
    init_db()
    app.run(debug=True ,host='0.0.0.0', port=5000 ,threaded=False)