import os
import random
import string
import re
import io
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file
from models import db, Category, Product, Order, OrderItem, Inquiry, AdminUser
from whatsapp_service import build_order_whatsapp_message, get_whatsapp_url, send_backend_whatsapp_notification, BACKEND_WHATSAPP_NUMBER
from excel_report_service import generate_financial_excel_report, generate_financial_csv_report

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gifric-farm-poultry-secret-key-2026-secure'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gifric_farm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Helper function to generate unique order number
def generate_order_number():
    random_str = ''.join(random.choices(string.digits, k=4))
    return f"GF-2026-{random_str}"

# Helper function to create URL slug from product name
def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s_-]+', '-', text)

# Admin Authentication Decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_id'):
            flash('Please log in to access the admin portal.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Context processor to make global data available in templates
@app.context_processor
def inject_global_data():
    categories = Category.query.all()
    current_admin = None
    if session.get('admin_id'):
        current_admin = AdminUser.query.get(session.get('admin_id'))
    return {
        'all_categories': categories,
        'company_name': 'Gifric Farm',
        'company_phone': '+263 77 223 9953',
        'company_email': 'progressezekiel00@gmail.com',
        'company_address': '84 St Andrews Rd, Hatfield, Harare, Zimbabwe',
        'company_gps': '-17.8767, 31.0825',
        'company_motto': 'To carry on the trade or business of farmers, farm managers, agricultural producers',
        'current_admin': current_admin
    }

# Public Routes

@app.route('/')
def index():
    featured_products = Product.query.filter_by(is_featured=True).limit(6).all()
    categories = Category.query.all()
    recent_products = Product.query.order_by(Product.id.desc()).limit(4).all()
    return render_template('index.html', 
                           featured_products=featured_products, 
                           categories=categories,
                           recent_products=recent_products)

@app.route('/products')
def products():
    category_slug = request.args.get('category', '')
    search_query = request.args.get('q', '').strip()
    
    query = Product.query
    selected_category = None
    
    if category_slug:
        selected_category = Category.query.filter_by(slug=category_slug).first()
        if selected_category:
            query = query.filter_by(category_id=selected_category.id)
            
    if search_query:
        query = query.filter(Product.name.ilike(f"%{search_query}%") | Product.description.ilike(f"%{search_query}%"))
        
    products_list = query.all()
    categories = Category.query.all()
    
    return render_template('products.html', 
                           products=products_list, 
                           categories=categories, 
                           selected_category=selected_category,
                           search_query=search_query)

@app.route('/product/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug).first_or_404()
    related_products = Product.query.filter(Product.category_id == product.category_id, Product.id != product.id).limit(4).all()
    return render_template('product_detail.html', product=product, related_products=related_products)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        service_type = request.form.get('service_type', 'general')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        if not name or not email or not message:
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('contact'))
            
        inquiry = Inquiry(
            name=name,
            email=email,
            phone=phone,
            service_type=service_type,
            subject=subject or 'General Inquiry',
            message=message
        )
        db.session.add(inquiry)
        db.session.commit()
        
        flash('Thank you for contacting Gifric Farm! Our agricultural team will respond promptly.', 'success')
        return redirect(url_for('contact'))
        
    return render_template('contact.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        delivery_address = request.form.get('delivery_address')
        city = request.form.get('city')
        payment_method = request.form.get('payment_method', 'cash')
        notes = request.form.get('notes')
        
        cart_data_json = request.form.get('cart_data')
        import json
        try:
            cart_items = json.loads(cart_data_json) if cart_data_json else []
        except Exception:
            cart_items = []
            
        if not cart_items:
            flash('Your cart is empty. Please add fresh products before checkout.', 'error')
            return redirect(url_for('products'))
            
        total_amount = 0.0
        order_items_to_create = []
        
        # Validate stock availability and deduct stock automatically
        for item in cart_items:
            product = Product.query.get(item['id'])
            if product:
                qty = int(item.get('quantity', 1))
                
                # Check if enough stock exists
                if product.stock_quantity < qty:
                    flash(f'Sorry, only {product.stock_quantity} units of "{product.name}" are currently available in stock.', 'error')
                    return redirect(url_for('cart'))
                    
                subtotal = product.price * qty
                total_amount += subtotal
                
                # Automatically update remaining stock in database
                product.stock_quantity -= qty
                
                order_items_to_create.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'price': product.price,
                    'quantity': qty,
                    'subtotal': subtotal
                })
                
        order_num = generate_order_number()
        new_order = Order(
            order_number=order_num,
            customer_name=customer_name,
            email=email,
            phone=phone,
            delivery_address=delivery_address,
            city=city,
            payment_method=payment_method,
            total_amount=total_amount,
            notes=notes,
            status='Confirmed' if payment_method in ['cash', 'ecocash'] else 'Pending'
        )
        db.session.add(new_order)
        db.session.commit()
        
        for item_data in order_items_to_create:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item_data['product_id'],
                product_name=item_data['product_name'],
                price=item_data['price'],
                quantity=item_data['quantity'],
                subtotal=item_data['subtotal']
            )
            db.session.add(order_item)
            
        db.session.commit()
        
        # Trigger automated backend WhatsApp notification to farm contact (+263 77 223 9953)
        try:
            send_backend_whatsapp_notification(new_order)
        except Exception as e:
            print(f"[-] Backend WhatsApp alert error: {e}")
            
        return redirect(url_for('order_success', order_number=order_num, auto_wa='1'))
        
    return render_template('checkout.html')

@app.route('/order-success/<order_number>')
def order_success(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    whatsapp_url = get_whatsapp_url(order)
    auto_wa = request.args.get('auto_wa') == '1'
    return render_template('order_success.html', 
                           order=order, 
                           whatsapp_url=whatsapp_url, 
                           auto_wa=auto_wa, 
                           backend_phone=BACKEND_WHATSAPP_NUMBER)


# Admin Authentication & Management Routes

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_id'):
        return redirect(url_for('admin'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        admin_user = AdminUser.query.filter((AdminUser.username == username) | (AdminUser.email == username)).first()
        
        if admin_user and admin_user.check_password(password):
            session['admin_id'] = admin_user.id
            session['admin_username'] = admin_user.username
            flash(f'Welcome back, {admin_user.username}!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid username/email or password.', 'error')
            
    return render_template('admin_login.html')

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('admin_register'))
            
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('admin_register'))
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(url_for('admin_register'))
            
        existing_user = AdminUser.query.filter((AdminUser.username == username) | (AdminUser.email == email)).first()
        if existing_user:
            flash('Username or Email already registered.', 'error')
            return redirect(url_for('admin_register'))
            
        new_admin = AdminUser(username=username, email=email)
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()
        
        session['admin_id'] = new_admin.id
        session['admin_username'] = new_admin.username
        flash('Admin account created successfully!', 'success')
        return redirect(url_for('admin'))
        
    return render_template('admin_register.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('You have logged out of the admin portal.', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    products_list = Product.query.order_by(Product.id.asc()).all()
    categories_list = Category.query.order_by(Category.name.asc()).all()
    total_sales = sum(o.total_amount for o in orders if o.status != 'Cancelled')
    
    # Financial snapshot for dashboard
    cogs_est = total_sales * 0.55
    expenses_est = total_sales * 0.10
    net_profit = total_sales - (cogs_est + expenses_est)
    inventory_val = sum(p.stock_quantity * p.price for p in products_list)
    
    return render_template('admin.html', 
                           orders=orders, 
                           inquiries=inquiries, 
                           products=products_list, 
                           products_count=len(products_list), 
                           categories=categories_list,
                           categories_count=len(categories_list),
                           total_sales=total_sales,
                           cogs_est=cogs_est,
                           expenses_est=expenses_est,
                           net_profit=net_profit,
                           inventory_val=inventory_val)

# Admin Financial & Order History Excel / CSV Exporter

@app.route('/admin/export/excel', methods=['GET', 'POST'])
@admin_required
def admin_export_excel():
    start_date = request.args.get('start_date') or request.form.get('start_date')
    end_date = request.args.get('end_date') or request.form.get('end_date')
    status_filter = request.args.get('status') or request.form.get('status')
    
    try:
        cost_ratio = float(request.args.get('cost_ratio') or request.form.get('cost_ratio') or 0.55)
    except (ValueError, TypeError):
        cost_ratio = 0.55

    try:
        expense_ratio = float(request.args.get('expense_ratio') or request.form.get('expense_ratio') or 0.10)
    except (ValueError, TypeError):
        expense_ratio = 0.10
    
    query = Order.query
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.created_at >= start_dt)
        except ValueError:
            pass
            
    if end_date:
        try:
            end_dt = datetime.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            query = query.filter(Order.created_at <= end_dt)
        except ValueError:
            pass
            
    if status_filter and status_filter != 'all':
        query = query.filter(Order.status == status_filter)
        
    orders = query.order_by(Order.created_at.desc()).all()
    products = Product.query.all()
    
    xlsx_file = generate_financial_excel_report(
        orders, 
        products, 
        cost_ratio=cost_ratio, 
        expense_ratio=expense_ratio, 
        start_date=start_date, 
        end_date=end_date
    )
    filename = f"Gifric_Farm_Financial_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    
    return send_file(
        xlsx_file,
        download_name=filename,
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/admin/export/csv', methods=['GET', 'POST'])
@admin_required
def admin_export_csv():
    try:
        cost_ratio = float(request.args.get('cost_ratio') or request.form.get('cost_ratio') or 0.55)
    except (ValueError, TypeError):
        cost_ratio = 0.55

    try:
        expense_ratio = float(request.args.get('expense_ratio') or request.form.get('expense_ratio') or 0.10)
    except (ValueError, TypeError):
        expense_ratio = 0.10
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    products = Product.query.all()
    
    csv_bytes = generate_financial_csv_report(orders, products, cost_ratio=cost_ratio, expense_ratio=expense_ratio)
    filename = f"Gifric_Farm_Financial_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    buffer = io.BytesIO(csv_bytes)
    return send_file(
        buffer,
        download_name=filename,
        as_attachment=True,
        mimetype="text/csv"
    )

# Admin Category Management CRUD

@app.route('/admin/category/add', methods=['POST'])
@admin_required
def admin_add_category():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not name:
        flash('Category name is required.', 'error')
        return redirect(url_for('admin'))
        
    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    while Category.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
        
    new_cat = Category(name=name, slug=slug, description=description)
    db.session.add(new_cat)
    db.session.commit()
    flash(f'Farm Produce Category "{name}" added successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/category/delete/<int:category_id>', methods=['POST'])
@admin_required
def admin_delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    cat_name = category.name
    
    product_count = Product.query.filter_by(category_id=category.id).count()
    if product_count > 0:
        flash(f'Cannot delete category "{cat_name}" because it currently contains {product_count} product(s). Please delete or reassign those products first.', 'error')
        return redirect(url_for('admin'))
        
    db.session.delete(category)
    db.session.commit()
    flash(f'Category "{cat_name}" removed successfully.', 'success')
    return redirect(url_for('admin'))

# Admin Product Management CRUD

@app.route('/admin/product/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    categories = Category.query.order_by(Category.name.asc()).all()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category_id_val = request.form.get('category_id')
        new_category_name = request.form.get('new_category_name', '').strip()
        price = request.form.get('price', type=float)
        
        unit_select = request.form.get('unit', '').strip()
        custom_unit = request.form.get('custom_unit', '').strip()
        unit = custom_unit if unit_select == 'custom' and custom_unit else (unit_select or 'per kg')
        
        stock_quantity = request.form.get('stock_quantity', type=int, default=100)
        description = request.form.get('description', '').strip()
        short_description = request.form.get('short_description', '').strip()
        image_url = request.form.get('image_url', '').strip()
        is_featured = 'is_featured' in request.form
        is_organic = 'is_organic' in request.form
        is_halal = 'is_halal' in request.form
        
        # Handle category: either existing or newly created on the fly
        category_id = None
        if new_category_name:
            base_cat_slug = slugify(new_category_name)
            cat_slug = base_cat_slug
            c_cnt = 1
            while Category.query.filter_by(slug=cat_slug).first():
                cat_slug = f"{base_cat_slug}-{c_cnt}"
                c_cnt += 1
            new_cat = Category(name=new_category_name, slug=cat_slug, description="Farm produce category created by admin.")
            db.session.add(new_cat)
            db.session.flush()
            category_id = new_cat.id
        elif category_id_val and category_id_val.isdigit():
            category_id = int(category_id_val)
            
        if not name or not category_id or price is None or not image_url:
            flash('Please fill in all required product fields (Name, Category, Price, and Image).', 'error')
            categories = Category.query.order_by(Category.name.asc()).all()
            return render_template('admin_product_form.html', categories=categories, product=None)
            
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while Product.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        new_product = Product(
            category_id=category_id,
            name=name,
            slug=slug,
            price=price,
            unit=unit,
            stock_quantity=stock_quantity,
            description=description,
            short_description=short_description,
            image_url=image_url,
            is_featured=is_featured,
            is_organic=is_organic,
            is_halal=is_halal
        )
        db.session.add(new_product)
        db.session.commit()
        
        flash(f'Product "{name}" added successfully with {stock_quantity} available stock!', 'success')
        return redirect(url_for('admin'))
        
    return render_template('admin_product_form.html', categories=categories, product=None)

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.order_by(Category.name.asc()).all()
    
    if request.method == 'POST':
        product.name = request.form.get('name', '').strip()
        
        new_category_name = request.form.get('new_category_name', '').strip()
        if new_category_name:
            base_cat_slug = slugify(new_category_name)
            cat_slug = base_cat_slug
            c_cnt = 1
            while Category.query.filter_by(slug=cat_slug).first():
                cat_slug = f"{base_cat_slug}-{c_cnt}"
                c_cnt += 1
            new_cat = Category(name=new_category_name, slug=cat_slug, description="Farm produce category created by admin.")
            db.session.add(new_cat)
            db.session.flush()
            product.category_id = new_cat.id
        else:
            cat_id = request.form.get('category_id', type=int)
            if cat_id:
                product.category_id = cat_id

        product.price = request.form.get('price', type=float)
        
        unit_select = request.form.get('unit', '').strip()
        custom_unit = request.form.get('custom_unit', '').strip()
        product.unit = custom_unit if unit_select == 'custom' and custom_unit else (unit_select or 'per kg')
        
        product.stock_quantity = request.form.get('stock_quantity', type=int, default=0)
        product.description = request.form.get('description', '').strip()
        product.short_description = request.form.get('short_description', '').strip()
        product.image_url = request.form.get('image_url', '').strip()
        product.is_featured = 'is_featured' in request.form
        product.is_organic = 'is_organic' in request.form
        product.is_halal = 'is_halal' in request.form
        
        db.session.commit()
        flash(f'Product "{product.name}" updated successfully! Available Stock: {product.stock_quantity}.', 'success')
        return redirect(url_for('admin'))
        
    return render_template('admin_product_form.html', categories=categories, product=product)

@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    product_name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{product_name}" removed from database.', 'success')
    return redirect(url_for('admin'))

@app.route('/api/order/status', methods=['POST'])
@admin_required
def update_order_status():
    data = request.get_json()
    order_id = data.get('order_id')
    new_status = data.get('status')
    
    order = Order.query.get(order_id)
    if order and new_status:
        order.status = new_status
        db.session.commit()
        return jsonify({'success': True, 'status': order.status})
    return jsonify({'success': False, 'error': 'Invalid order or status'}), 400

@app.route('/api/inquiry/status', methods=['POST'])
@admin_required
def update_inquiry_status():
    data = request.get_json()
    inquiry_id = data.get('inquiry_id')
    new_status = data.get('status')
    
    inquiry = Inquiry.query.get(inquiry_id)
    if inquiry and new_status:
        inquiry.status = new_status
        db.session.commit()
        return jsonify({'success': True, 'status': inquiry.status})
    return jsonify({'success': False, 'error': 'Invalid inquiry'}), 400

with app.app_context():
    db.create_all()
    # Auto-seed database if fresh deployment on Render or empty
    if Category.query.count() == 0:
        try:
            from seed_data import seed_database
            seed_database()
            print("[+] Database auto-seeded for fresh deployment!")
        except Exception as e:
            print(f"[-] Auto-seed notice: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1']
    print(f"[+] Starting Gifric Farm Web Server on http://0.0.0.0:{port} ...")
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
