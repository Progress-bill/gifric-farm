/**
 * Gifric Farm - Main JavaScript Cart & Interactivity Engine
 */

class GifricCart {
    constructor() {
        this.cartKey = 'gifric_farm_cart_v1';
        this.cart = this.loadCart();
    }

    loadCart() {
        try {
            const stored = localStorage.getItem(this.cartKey);
            return stored ? JSON.parse(stored) : [];
        } catch (e) {
            console.error('Failed to load cart', e);
            return [];
        }
    }

    saveCart() {
        try {
            localStorage.setItem(this.cartKey, JSON.stringify(this.cart));
        } catch (e) {
            console.error('Failed to save cart', e);
        }
        this.updateUI();
    }

    addItem(product, quantity = 1) {
        if (!product || !product.id) {
            console.error('Invalid product data', product);
            return;
        }
        quantity = parseInt(quantity) || 1;
        const existingIndex = this.cart.findIndex(item => item.id === product.id);

        if (existingIndex > -1) {
            this.cart[existingIndex].quantity += quantity;
        } else {
            this.cart.push({
                id: product.id,
                name: product.name,
                price: parseFloat(product.price),
                unit: product.unit || 'per bird',
                image_url: product.image_url || '',
                quantity: quantity
            });
        }

        this.saveCart();
        this.showToast(`Added "${product.name}" to cart!`);
        this.openDrawer();
    }

    removeItem(id) {
        this.cart = this.cart.filter(item => item.id !== id);
        this.saveCart();
        this.showToast('Item removed from cart');
    }

    updateQuantity(id, quantity) {
        quantity = parseInt(quantity);
        if (quantity <= 0) {
            this.removeItem(id);
            return;
        }
        const item = this.cart.find(item => item.id === id);
        if (item) {
            item.quantity = quantity;
            this.saveCart();
        }
    }

    clearCart() {
        this.cart = [];
        this.saveCart();
    }

    getTotalCount() {
        return this.cart.reduce((sum, item) => sum + item.quantity, 0);
    }

    getTotalPrice() {
        return this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    }

    updateUI() {
        // Update badge counter
        const countBadges = document.querySelectorAll('.cart-count-badge');
        const count = this.getTotalCount();
        countBadges.forEach(badge => {
            badge.textContent = count;
            if (count > 0) {
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        });

        // Render Cart Drawer Content
        const drawerContainer = document.getElementById('cart-drawer-items');
        const drawerSubtotal = document.getElementById('cart-drawer-subtotal');
        
        if (drawerContainer) {
            if (this.cart.length === 0) {
                drawerContainer.innerHTML = `
                    <div class="text-center py-12 px-4">
                        <div class="w-16 h-16 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
                            🛒
                        </div>
                        <h4 class="text-lg font-bold text-gray-800 mb-1">Your cart is empty</h4>
                        <p class="text-sm text-gray-500 mb-6">Browse our fresh organic chicken and farm products!</p>
                        <a href="/products" class="inline-block bg-emerald-700 hover:bg-emerald-800 text-white font-medium text-sm px-5 py-2.5 rounded-lg transition">
                            Shop Fresh Products
                        </a>
                    </div>
                `;
            } else {
                drawerContainer.innerHTML = this.cart.map(item => `
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-100 mb-3">
                        <img src="${item.image_url}" alt="${item.name}" class="w-14 h-14 object-cover rounded-lg flex-shrink-0">
                        <div class="ml-3 flex-grow pr-2">
                            <h5 class="text-xs font-semibold text-gray-800 line-clamp-1">${item.name}</h5>
                            <p class="text-xs text-emerald-700 font-bold">$${item.price.toFixed(2)} <span class="text-gray-400 text-[10px] font-normal">/ ${item.unit}</span></p>
                            
                            <div class="flex items-center mt-1.5 space-x-2">
                                <button type="button" onclick="window.gifricCart.updateQuantity(${item.id}, ${item.quantity - 1})" class="w-6 h-6 rounded bg-gray-200 hover:bg-gray-300 flex items-center justify-center text-xs text-gray-700 font-bold">-</button>
                                <span class="text-xs font-bold text-gray-800 w-5 text-center">${item.quantity}</span>
                                <button type="button" onclick="window.gifricCart.updateQuantity(${item.id}, ${item.quantity + 1})" class="w-6 h-6 rounded bg-gray-200 hover:bg-gray-300 flex items-center justify-center text-xs text-gray-700 font-bold">+</button>
                            </div>
                        </div>
                        <div class="text-right">
                            <span class="text-xs font-bold text-gray-900 block">$${(item.price * item.quantity).toFixed(2)}</span>
                            <button type="button" onclick="window.gifricCart.removeItem(${item.id})" class="text-red-500 hover:text-red-700 text-xs mt-2 inline-block">
                                Delete
                            </button>
                        </div>
                    </div>
                `).join('');
            }
        }

        if (drawerSubtotal) {
            drawerSubtotal.textContent = `$${this.getTotalPrice().toFixed(2)}`;
        }

        // Render Checkout Page Summary if on Checkout
        this.renderCheckoutSummary();
    }

    renderCheckoutSummary() {
        const summaryContainer = document.getElementById('checkout-items-list');
        const summaryTotal = document.getElementById('checkout-total-price');
        const cartDataInput = document.getElementById('cart_data_input');

        if (cartDataInput) {
            cartDataInput.value = JSON.stringify(this.cart);
        }

        if (summaryContainer) {
            if (this.cart.length === 0) {
                summaryContainer.innerHTML = '<p class="text-gray-500 text-sm italic">No items in cart.</p>';
            } else {
                summaryContainer.innerHTML = this.cart.map(item => `
                    <div class="flex items-center justify-between text-sm py-2 border-b border-gray-100">
                        <div class="flex items-center">
                            <span class="font-bold text-emerald-800 mr-2">${item.quantity}x</span>
                            <span class="text-gray-800 font-medium">${item.name}</span>
                        </div>
                        <span class="font-semibold text-gray-900">$${(item.price * item.quantity).toFixed(2)}</span>
                    </div>
                `).join('');
            }
        }

        if (summaryTotal) {
            summaryTotal.textContent = `$${this.getTotalPrice().toFixed(2)}`;
        }
    }

    openDrawer() {
        const drawer = document.getElementById('cart-drawer');
        const backdrop = document.getElementById('cart-drawer-backdrop');
        if (drawer && backdrop) {
            drawer.classList.remove('translate-x-full');
            backdrop.classList.remove('hidden');
        }
    }

    closeDrawer() {
        const drawer = document.getElementById('cart-drawer');
        const backdrop = document.getElementById('cart-drawer-backdrop');
        if (drawer && backdrop) {
            drawer.classList.add('translate-x-full');
            backdrop.classList.add('hidden');
        }
    }

    showToast(message) {
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            document.body.appendChild(toastContainer);
        }

        const toast = document.createElement('div');
        toast.className = 'bg-gray-900 text-white px-4 py-3 rounded-lg shadow-xl mb-3 flex items-center space-x-3 text-sm animate-bounce duration-300';
        toast.innerHTML = `
            <span class="text-emerald-400">✓</span>
            <span>${message}</span>
        `;

        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Instantiate and expose globally on window
window.gifricCart = new GifricCart();
const gifricCart = window.gifricCart;

document.addEventListener('DOMContentLoaded', () => {
    window.gifricCart.updateUI();

    // Mobile nav toggle
    const mobileBtn = document.getElementById('mobile-menu-btn');
    const mobileNav = document.getElementById('mobile-menu');
    if (mobileBtn && mobileNav) {
        mobileBtn.addEventListener('click', () => {
            mobileNav.classList.toggle('hidden');
        });
    }
});
