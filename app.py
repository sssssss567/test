from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

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

# 商品列表与各种查询 
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

# 购买逻辑实现 
@app.route('/buy/<int:item_id>')
def buy(item_id):
    conn = sqlite3.connect(DB_PATH)
    try:
        # 简单业务逻辑：检查状态并更新 
        item = conn.execute("SELECT status FROM Item WHERE item_id=?", (item_id,)).fetchone()
        if item and item[0] == 0:
            conn.execute("BEGIN TRANSACTION")
            # 1. 插入订单 (模拟 buyer 为 u001) 
            conn.execute("INSERT INTO Orders (order_id, item_id, buyer_id, order_date) VALUES (?, ?, ?, date('now'))", 
                         (f"NEW{item_id}", item_id, 'u001'))
            # 2. 修改状态为 1 
            conn.execute("UPDATE Item SET status = 1 WHERE item_id = ?", (item_id,))
            conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        conn.close()
    return redirect(url_for('list_items'))

# 聚合统计 
@app.route('/queries')
def stats():
    total_count = query_db("SELECT COUNT(*) as c FROM Item", one=True)['c']
    avg_price = query_db("SELECT AVG(price) as a FROM Item", one=True)['a']
    cat_counts = query_db("SELECT category, COUNT(*) as c FROM Item GROUP BY category")
    top_user = query_db("SELECT seller_id, COUNT(*) as c FROM Item GROUP BY seller_id ORDER BY c DESC LIMIT 1", one=True)
    return render_template('queries.html', **locals())

@app.route('/users')
def list_users():
    users = query_db("SELECT * FROM User")
    return render_template('users.html', users=users)

@app.route('/orders')
def list_orders():
    # 连接查询：商品名+买家名+日期 
    orders = query_db("""
        SELECT i.item_name, u.user_name, o.order_date 
        FROM Orders o 
        JOIN Item i ON o.item_id = i.item_id 
        JOIN User u ON o.buyer_id = u.user_id
    """)
    return render_template('orders.html', orders=orders)

if __name__ == '__main__':
    app.run(debug=True)