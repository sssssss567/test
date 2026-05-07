from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'some_secret_key'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'campus_trade.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    # 将查询结果转换为字典列表，避免元组索引报错
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/items')
def list_items():
    conn = get_db_connection()
    f = request.args.get('filter')
    q = request.args.get('q')
    
    sql = "SELECT * FROM Item WHERE 1=1"
    params = []
    
    if f == 'unsold': sql += " AND status = 0" [cite: 44]
    elif f == 'expensive': sql += " AND price > 30" [cite: 45]
    elif f == 'daily': sql += " AND category = 'DailyGoods'" [cite: 46]
    elif f == 'u001': sql += " AND seller_id = 'u001'" [cite: 47]
    
    if q:
        sql += " AND item_name LIKE ?"
        params.append(f'%{q}%')
        
    items = conn.execute(sql, params).fetchall()
    conn.close()
    return render_template('items.html', items=items)

@app.route('/buy/<int:item_id>')
def buy(item_id):
    conn = get_db_connection()
    item = conn.execute("SELECT status FROM Item WHERE item_id=?", (item_id,)).fetchone()
    
    if item and item['status'] == 0: [cite: 24, 68]
        try:
            conn.execute("BEGIN TRANSACTION")
            conn.execute("INSERT INTO Orders (item_id, buyer_id, order_date) VALUES (?, 'u001', date('now'))", (item_id,)) [cite: 65]
            conn.execute("UPDATE Item SET status = 1 WHERE item_id = ?", (item_id,)) [cite: 66]
            conn.commit()
        except:
            conn.rollback()
    conn.close()
    return redirect(url_for('list_items'))

@app.route('/delete/<int:item_id>')
def delete_item(item_id):
    conn = get_db_connection()
    # 仅允许删除未售出的商品 
    conn.execute("DELETE FROM Item WHERE item_id = ? AND status = 0", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('list_items'))

@app.route('/edit_price', methods=['POST'])
def edit_price():
    item_id = request.form.get('item_id')
    new_price = request.form.get('price')
    conn = get_db_connection()
    conn.execute("UPDATE Item SET price = ? WHERE item_id = ?", (new_price, item_id)) [cite: 37]
    conn.commit()
    conn.close()
    return redirect(url_for('list_items'))

@app.route('/queries')
def stats():
    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) as c FROM Item").fetchone()['c'] [cite: 55]
    avg = conn.execute("SELECT AVG(price) as a FROM Item").fetchone()['a'] or 0 [cite: 57]
    cats = conn.execute("SELECT category, COUNT(*) as c FROM Item GROUP BY category").fetchall() [cite: 56]
    top = conn.execute("SELECT seller_id, COUNT(*) as c FROM Item GROUP BY seller_id ORDER BY c DESC LIMIT 1").fetchone() [cite: 58]
    
    # 连接查询：已售商品及其买家姓名 [cite: 50]
    sold_details = conn.execute("""
        SELECT i.item_name, u.user_name FROM Item i 
        JOIN Orders o ON i.item_id = o.item_id 
        JOIN User u ON o.buyer_id = u.user_id
    """).fetchall()
    
    conn.close()
    return render_template('queries.html', **locals())

@app.route('/users')
def list_users():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM User").fetchall() [cite: 5]
    conn.close()
    return render_template('users.html', users=users)

@app.route('/orders')
def list_orders():
    conn = get_db_connection()
    # 连接查询：商品名+买家名+日期 [cite: 51]
    orders = conn.execute("""
        SELECT i.item_name, u.user_name, o.order_date FROM Orders o 
        JOIN Item i ON o.item_id = i.item_id 
        JOIN User u ON o.buyer_id = u.user_id
    """).fetchall()
    conn.close()
    return render_template('orders.html', orders=orders)

if __name__ == '__main__':
    app.run(debug=True)