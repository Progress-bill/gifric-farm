from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class AdminUser(db.Model):
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email
        }

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    products = db.relationship('Product', backref='category', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description
        }

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False, default="per kg")
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(500), nullable=False)
    stock_quantity = db.Column(db.Integer, default=100, nullable=False)
    is_featured = db.Column(db.Boolean, default=False)
    is_organic = db.Column(db.Boolean, default=True)
    is_halal = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def category_name(self):
        return self.category.name if self.category else 'Fresh Produce'

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else '',
            'name': self.name,
            'slug': self.slug,
            'price': self.price,
            'unit': self.unit,
            'description': self.description,
            'short_description': self.short_description,
            'image_url': self.image_url,
            'stock_quantity': self.stock_quantity,
            'is_in_stock': self.stock_quantity > 0,
            'is_featured': self.is_featured,
            'is_organic': self.is_organic,
            'is_halal': self.is_halal
        }

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(30), nullable=False)
    delivery_address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False, default="cash")
    status = db.Column(db.String(30), nullable=False, default="Pending") # Pending, Confirmed, Delivered, Cancelled
    total_amount = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'customer_name': self.customer_name,
            'email': self.email,
            'phone': self.phone,
            'delivery_address': self.delivery_address,
            'city': self.city,
            'payment_method': self.payment_method,
            'status': self.status,
            'total_amount': self.total_amount,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'items': [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    product_name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'product_name': self.product_name,
            'price': self.price,
            'quantity': self.quantity,
            'subtotal': self.subtotal
        }

class Inquiry(db.Model):
    __tablename__ = 'inquiries'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True, default="")
    phone = db.Column(db.String(30), nullable=True)
    service_type = db.Column(db.String(50), nullable=False, default="general") # wholesale, feed, general
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Unread") # Unread, Responded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'service_type': self.service_type,
            'subject': self.subject,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }
