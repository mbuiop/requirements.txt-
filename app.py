from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import uuid
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# ایجاد دیتابیس و جدول‌های لازم
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # جدول کاربران
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  referral_code TEXT UNIQUE,
                  referred_by TEXT,
                  wallet_address TEXT,
                  transaction_hash TEXT,
                  transaction_verified INTEGER DEFAULT 0,
                  app_access INTEGER DEFAULT 0,
                  signals_access INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # جدول تراکنش‌ها
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  transaction_hash TEXT UNIQUE,
                  amount REAL,
                  status TEXT DEFAULT 'pending',
                  verified_by INTEGER,
                  verified_at TIMESTAMP,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # جدول پیام‌های همگانی
    c.execute('''CREATE TABLE IF NOT EXISTS announcements
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  message TEXT,
                  created_by INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

init_db()

# صفحه اصلی
@app.route('/')
def index():
    return render_template('index.html')

# صفحه رفرال
@app.route('/referral')
def referral():
    if 'user_id' not in session:
        # ایجاد کاربر جدید اگر وجود ندارد
        user_id = str(uuid.uuid4())
        referral_code = str(uuid.uuid4())[:8]
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (username, referral_code) VALUES (?, ?)", 
                 (user_id, referral_code))
        conn.commit()
        conn.close()
        
        session['user_id'] = user_id
        session['referral_code'] = referral_code
    else:
        referral_code = session.get('referral_code', '')
    
    referral_link = request.host_url + 'referral?ref=' + referral_code
    return render_template('referral.html', referral_link=referral_link)

# صفحه اپلیکیشن ساز
@app.route('/app_creator')
def app_creator():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('referral'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT transaction_verified, app_access FROM users WHERE username = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    
    if user and user[0] and user[1]:
        # کاربر تأیید شده است و دسترسی دارد
        return redirect('https://web2apkpro.com/projects.php')
    
    wallet_address = "T61aTh98MGqmteYzda5AaBzdXgGqreG6A"
    return render_template('app_creator.html', wallet_address=wallet_address)

# ثبت تراکنش
@app.route('/submit_transaction', methods=['POST'])
def submit_transaction():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'لطفاً ابتدا وارد شوید'})
    
    transaction_hash = request.form.get('transaction_hash')
    
    if not transaction_hash:
        return jsonify({'success': False, 'message': 'لطفاً هش تراکنش را وارد کنید'})
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # بررسی وجود تراکنش تکراری
    c.execute("SELECT id FROM transactions WHERE transaction_hash = ?", (transaction_hash,))
    if c.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'این تراکنش قبلاً ثبت شده است'})
    
    # ثبت تراکنش
    c.execute("INSERT INTO transactions (user_id, transaction_hash, amount) VALUES (?, ?, ?)",
             (user_id, transaction_hash, 50))
    
    # به روز رسانی اطلاعات کاربر
    c.execute("UPDATE users SET transaction_hash = ? WHERE username = ?", 
             (transaction_hash, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'تراکنش با موفقیت ثبت شد. در انتظار تأیید ادمین'})

# صفحه سیگنال
@app.route('/signals')
def signals():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('referral'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT transaction_verified, signals_access FROM users WHERE username = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    
    if user and user[0] and user[1]:
        # در اینجا الگوریتم پیشرفته سیگنال‌دهی قرار می‌گیرد
        # برای نمونه، یک سیگنال تصادفی تولید می‌شود
        import random
        signals = [
            {
                'symbol': 'EUR/USD',
                'action': 'BUY' if random.random() > 0.5 else 'SELL',
                'price': round(1.0800 + random.random() * 0.01, 4),
                'sl': round(1.0750 + random.random() * 0.005, 4),
                'tp': round(1.0850 + random.random() * 0.01, 4)
            },
            {
                'symbol': 'GBP/USD',
                'action': 'BUY' if random.random() > 0.5 else 'SELL',
                'price': round(1.2600 + random.random() * 0.01, 4),
                'sl': round(1.2550 + random.random() * 0.005, 4),
                'tp': round(1.2650 + random.random() * 0.01, 4)
            }
        ]
        return render_template('signals.html', signals=signals)
    
    return render_template('signals.html', access_denied=True)

# صفحه لاگین ادمین
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == '12345!@#$%54321':
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error='رمز عبور اشتباه است')
    
    return render_template('admin_login.html')

# پنل ادمین
@app.route('/admin')
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # دریافت تراکنش‌های در انتظار تأیید
    c.execute('''SELECT t.id, u.username, t.transaction_hash, t.amount, t.created_at 
                 FROM transactions t 
                 JOIN users u ON t.user_id = u.username 
                 WHERE t.status = 'pending' 
                 ORDER BY t.created_at DESC''')
    pending_transactions = c.fetchall()
    
    # دریافت کاربران
    c.execute("SELECT username, referral_code, transaction_verified, app_access, signals_access FROM users")
    users = c.fetchall()
    
    conn.close()
    
    return render_template('admin_panel.html', 
                          pending_transactions=pending_transactions,
                          users=users)

# تأیید تراکنش
@app.route('/admin/verify_transaction', methods=['POST'])
def verify_transaction():
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'دسترسی غیرمجاز'})
    
    transaction_id = request.form.get('transaction_id')
    action = request.form.get('action')  # approve یا reject
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    if action == 'approve':
        # دریافت اطلاعات تراکنش
        c.execute("SELECT user_id FROM transactions WHERE id = ?", (transaction_id,))
        transaction = c.fetchone()
        
        if transaction:
            user_id = transaction[0]
            
            # به روز رسانی وضعیت تراکنش
            c.execute("UPDATE transactions SET status = 'approved', verified_at = datetime('now') WHERE id = ?", 
                     (transaction_id,))
            
            # فعال کردن دسترسی‌های کاربر
            c.execute("UPDATE users SET transaction_verified = 1, app_access = 1, signals_access = 1 WHERE username = ?", 
                     (user_id,))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'تراکنش تأیید شد و دسترسی کاربر فعال گردید'})
    
    elif action == 'reject':
        c.execute("UPDATE transactions SET status = 'rejected', verified_at = datetime('now') WHERE id = ?", 
                 (transaction_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'تراکنش رد شد'})
    
    conn.close()
    return jsonify({'success': False, 'message': 'عملیات ناموفق بود'})

# ارسال پیام همگانی
@app.route('/admin/send_announcement', methods=['POST'])
def send_announcement():
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'دسترسی غیرمجاز'})
    
    message = request.form.get('message')
    
    if not message:
        return jsonify({'success': False, 'message': 'لطفاً متن پیام را وارد کنید'})
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO announcements (message, created_by) VALUES (?, ?)", 
             (message, 'admin'))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'پیام همگانی با موفقیت ارسال شد'})

if __name__ == '__main__':
    app.run(debug=True)
