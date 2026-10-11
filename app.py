"""
OXFORD MODERN SCHOOL - Integrated ERP System
Developed by: Akandwanaho Ismah
Modules: Inventory Management + Finance Ledger
Database: Single SQLite (oxford_erp.db)
"""

from flask import Flask, request, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize Flask App
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///oxford_erp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ===================== DATABASE TABLES =====================

class StockItem(db.Model):
    """Stores all school items: Uniform, Sweater, Books, Pens, Rubbers, Dusters"""
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(20), unique=True, nullable=False)  # e.g OXF-PEN-01
    name = db.Column(db.String(100), nullable=False)  # e.g Blue Pen
    category = db.Column(db.String(30), default='General')  # Pen, Rubber, Duster, Sweater etc
    qty = db.Column(db.Integer, default=0)  # Quantity in stock
    price = db.Column(db.Float, nullable=False)  # Price in UGX
    reorder_level = db.Column(db.Integer, default=5)  # Alert when low

class Student(db.Model):
    """Student Registration Table"""
    id = db.Column(db.Integer, primary_key=True)
    adm_no = db.Column(db.String(20), unique=True, nullable=False)  # Admission Number
    name = db.Column(db.String(100), nullable=False)
    class_level = db.Column(db.String(20))  # e.g P.7, S.1

class FeesLedger(db.Model):
    """Finance Ledger - Automatically updated when items are sold"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # SALE, FEES, etc
    description = db.Column(db.String(200))  # e.g 2 x Pen Blue Pen
    date = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('Student')  # Link to student

# ===================== ROUTES =====================

@app.route('/')
def index():
    """Main Dashboard - Shows everything"""
    students = Student.query.all()
    items = StockItem.query.all()
    ledger = FeesLedger.query.order_by(FeesLedger.date.desc()).all()
    total = sum([l.amount for l in ledger])
    return render_template('index.html', students=students, items=items, ledger=ledger, total=total)

@app.route('/add_student', methods=['POST'])
def add_student():
    """Add a new student to the system"""
    try:
        new_student = Student(
            adm_no=request.form['adm_no'],
            name=request.form['name'],
            class_level=request.form['class_level']
        )
        db.session.add(new_student)
        db.session.commit()
    except:
        db.session.rollback()  # If admission number already exists, ignore
    return redirect(url_for('index'))

@app.route('/add_stock', methods=['POST'])
def add_stock():
    """Add stock - If item code already exists, just increase quantity"""
    code = request.form.get('code').strip()
    name = request.form.get('name').strip()
    category = request.form.get('category', 'General')
    qty = int(request.form.get('qty', 0))
    price = float(request.form.get('price', 0))

    existing_item = StockItem.query.filter_by(item_code=code).first()
    
    if existing_item:
        # Item already exists -> Update it
        existing_item.qty += qty
        existing_item.name = name
        existing_item.category = category
        existing_item.price = price
    else:
        # New item -> Create it
        new_item = StockItem(item_code=code, name=name, category=category, qty=qty, price=price)
        db.session.add(new_item)
    
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/sell', methods=['POST'])
def sell():
    """Sell an item - Reduces stock and automatically posts to finance ledger"""
    item = StockItem.query.get(int(request.form['item_id']))
    qty_to_sell = int(request.form['qty'])

    # Check if enough stock is available
    if item.qty < qty_to_sell:
        return f"<h3 style='color:red; text-align:center; margin-top:50px;'>ERROR: Only {item.qty} left of {item.name}. <br><br><a href='/'>Go Back</a></h3>"

    # 1. Reduce stock
    item.qty -= qty_to_sell
    
    # 2. Calculate total sale
    sale_amount = item.price * qty_to_sell
    
    # 3. Post to finance ledger automatically
    finance_entry = FeesLedger(
        student_id=int(request.form['student_id']),
        amount=sale_amount,
        type='SALE',
        description=f"{qty_to_sell} x {item.category} - {item.name}"
    )
    db.session.add(finance_entry)
    db.session.commit()
    
    return redirect(url_for('index'))

# ===================== START APP =====================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
        
        # Add initial demo data if database is empty
        if not StockItem.query.first():
            demo_items = [
                StockItem(item_code='OXF-UNI-01', name='School Uniform Boys', category='Uniform', qty=50, price=45000),
                StockItem(item_code='OXF-SW-01', name='School Sweater Green', category='Sweater', qty=60, price=35000),
                StockItem(item_code='OXF-BOOK-01', name='Math Textbook P.7', category='Books', qty=100, price=25000),
                StockItem(item_code='OXF-PEN-01', name='Blue Pen Bic', category='Pen', qty=200, price=500),
                StockItem(item_code='OXF-RUB-01', name='Eraser Rubber', category='Rubber', qty=150, price=300),
                StockItem(item_code='OXF-DUS-01', name='Blackboard Duster', category='Duster', qty=80, price=2000),
            ]
            db.session.add_all(demo_items)
            db.session.commit()

        if not Student.query.first():
            db.session.add(Student(adm_no='OXF/001', name='Akandwanaho Ismah', class_level='P.7'))
            db.session.commit()

    print("\n=== OXFORD MODERN SCHOOL ERP RUNNING ===")
    print("Open: http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)