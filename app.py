from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_session'

# 获取数据库绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'campus_trade.db')

def get_db_connection():
    """建立数据库连接并强制转换为字典格式，防止索引报错"""
    conn = sqlite3.connect(DB_PATH)
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
    
    if f == 'unsold': sql += " AND status = 0"
    elif f == 'expensive': sql += " AND price > 30"
    elif f == 'daily': sql += " AND category = 'DailyGoods'"
    elif f == 'u001': sql += " AND seller_id = 'u001'"
    
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
    
    if item and item['status'] == 0:
        try:
            conn.execute("BEGIN TRANSACTION")
            # 插入新订单记录
            conn.execute("INSERT INTO Orders (item_id, buyer_id, order_date) VALUES (?, 'u001', date('now'))", (item_id,))
            # 修改商品状态为已售出 (1)
            conn.execute("UPDATE Item SET status = 1 WHERE item_id = ?", (item_id,))
            conn.commit()
        except Exception:
            conn.rollback()
    conn.close()
    return redirect(url_for('list_items'))

@app.route('/queries')
def stats():
    conn = get_db_connection()
    # 统计基本信息
    total = conn.execute("SELECT COUNT(*) as c FROM Item").fetchone()['c']
    avg_res = conn.execute("SELECT AVG(price) as a FROM Item").fetchone()['a']
    avg = avg_res if avg_res else 0
    cats = conn.execute("SELECT category, COUNT(*) as c FROM Item GROUP BY category").fetchall()
    top = conn.execute("SELECT seller_id, COUNT(*) as c FROM Item GROUP BY seller_id ORDER BY c DESC LIMIT 1").fetchone()
    
    # 复杂查询：已售商品及其买家姓名
    sold_details = conn.execute("""
        SELECT i.item_name, u.user_name FROM Item i 
        JOIN Orders o ON i.item_id = o.item_id 
        JOIN User u ON o.buyer_id = u.user_id
    """).fetchall()
    
    conn.close()
    return render_template('queries.html', 
                           total_count=total, 
                           avg_price=avg, 
                           cat_counts=cats, 
                           top_user=top,
                           sold_details=sold_details)

@app.route('/users')
def list_users():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM User").fetchall()
    conn.close()
    return render_template('users.html', users=users)

@app.route('/orders')
def list_orders():
    conn = get_db_connection()
    # 连接查询任务
    orders = conn.execute("""
        SELECT i.item_name, u.user_name, o.order_date FROM Orders o 
        JOIN Item i ON o.item_id = i.item_id 
        JOIN User u ON o.buyer_id = u.user_id
    """).fetchall()
    conn.close()
    return render_template('orders.html', orders=orders)

if __name__ == '__main__':
    app.run(debug=True)