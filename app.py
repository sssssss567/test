from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# 获取绝对路径，确保在任何环境下都能找到数据库
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'campus_trade.db')

def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/items')
def list_items():
    filter_type = request.args.get('filter')
    sql = "SELECT * FROM Item"
    if filter_type == 'unsold': sql = "SELECT * FROM Item WHERE status = 0"
    elif filter_type == 'expensive': sql = "SELECT * FROM Item WHERE price > 30"
    elif filter_type == 'daily': sql = "SELECT * FROM Item WHERE category = 'DailyGoods'"
    elif filter_type == 'u001': sql = "SELECT * FROM Item WHERE seller_id = 'u001'"
    
    items = query_db(sql)
    return render_template('items.html', items=items)

@app.route('/buy/<int:item_id>')
def buy(item_id):
    conn = sqlite3.connect(DB_PATH)
    try:
        item = conn.execute("SELECT status FROM Item WHERE item_id=?", (item_id,)).fetchone()
        if item and item[0] == 0:
            conn.execute("BEGIN TRANSACTION")
            conn.execute("INSERT INTO Orders (order_id, item_id, buyer_id, order_date) VALUES (?, ?, ?, date('now'))", 
                         (f"NEW{item_id}", item_id, 'u001'))
            conn.execute("UPDATE Item SET status = 1 WHERE item_id = ?", (item_id,))
            conn.commit()
    except Exception:
        conn.rollback()
    finally:
        conn.close()
    return redirect(url_for('list_items'))

@app.route('/queries')
def stats():
    # 修正：改用索引 [0] 访问聚合函数结果，防止 TypeError
    res_total = query_db("SELECT COUNT(*) FROM Item", one=True)
    total_count = res_total[0] if res_total else 0

    res_avg = query_db("SELECT AVG(price) FROM Item", one=True)
    avg_price = res_avg[0] if res_avg and res_avg[0] is not None else 0

    cat_counts = query_db("SELECT category, COUNT(*) as c FROM Item GROUP BY category")
    
    res_top = query_db("SELECT seller_id, COUNT(*) FROM Item GROUP BY seller_id ORDER BY COUNT(*) DESC LIMIT 1", one=True)
    top_user = res_top if res_top else ["无", 0]

    return render_template('queries.html', 
                           total_count=total_count, 
                           avg_price=avg_price, 
                           cat_counts=cat_counts, 
                           top_user=top_user)

@app.route('/users')
def list_users():
    users = query_db("SELECT * FROM User")
    return render_template('users.html', users=users)

@app.route('/orders')
def list_orders():
    orders = query_db("""
        SELECT i.item_name, u.user_name, o.order_date 
        FROM Orders o 
        JOIN Item i ON o.item_id = i.item_id 
        JOIN User u ON o.buyer_id = u.user_id
    """)
    return render_template('orders.html', orders=orders)

if __name__ == '__main__':
    app.run(debug=True)