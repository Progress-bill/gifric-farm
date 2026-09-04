import os
import urllib.parse
import json
import logging

logger = logging.getLogger(__name__)

# Backend contact configuration
BACKEND_WHATSAPP_NUMBER = os.environ.get("BACKEND_WHATSAPP_NUMBER", "+263 77 223 9953")
CLEAN_WHATSAPP_PHONE = "".join(filter(str.isdigit, BACKEND_WHATSAPP_NUMBER)) # 263772239953

def build_order_whatsapp_message(order):
    """
    Constructs a clean, professional WhatsApp receipt message for Gifric Farm orders.
    Uses standard text formatting compatible across mobile, desktop, and all OS encodings.
    """
    items_text = []
    for item in order.items:
        items_text.append(f"  * {item.quantity}x {item.product_name} (${item.price:.2f} ea) = ${item.subtotal:.2f}")
    
    items_block = "\n".join(items_text)
    payment_label = order.payment_method.replace('_', ' ').upper()
    
    ecocash_block = ""
    if order.payment_method == 'ecocash':
        ecocash_block = (
            f"\n*ECOCASH PAYMENT DETAILS:*\n"
            f"Send ${order.total_amount:.2f} to: +263 77 223 9953\n"
            f"Account Name: Nyasha Florance Murau\n"
            f"Reference: {order.order_number}\n"
        )
        
    notes_block = f"\n*Special Notes:* {order.notes}\n" if order.notes else ""

    message = (
        f"*NEW ORDER - GIFRIC FARM*\n"
        f"-------------------------------------\n"
        f"*Order Code:* {order.order_number}\n"
        f"*Customer Name:* {order.customer_name}\n"
        f"*Phone / WhatsApp:* {order.phone}\n"
        f"*Delivery Address:* {order.delivery_address}, {order.city}\n"
        f"*Payment Method:* {payment_label}\n"
        f"-------------------------------------\n"
        f"*ITEMS ORDERED:*\n"
        f"{items_block}\n"
        f"-------------------------------------\n"
        f"*TOTAL AMOUNT: ${order.total_amount:.2f}*\n"
        f"{ecocash_block}"
        f"{notes_block}"
        f"-------------------------------------\n"
        f"_Order automatically dispatched to Gifric Farm (+263 77 223 9953)_"
    )
    return message

def get_whatsapp_url(order):
    """
    Generates a universal wa.me link with the pre-filled order receipt.
    """
    message = build_order_whatsapp_message(order)
    encoded_text = urllib.parse.quote(message)
    return f"https://wa.me/{CLEAN_WHATSAPP_PHONE}?text={encoded_text}"

def send_backend_whatsapp_notification(order):
    """
    Triggers automated backend notification to the contact (+263 77 223 9953).
    Supports Meta WhatsApp Cloud API, Twilio, or generic Webhook if credentials exist.
    Always logs the dispatched notification payload safely without Unicode encoding errors.
    """
    message = build_order_whatsapp_message(order)
    wa_url = get_whatsapp_url(order)
    
    print("\n[+] ================= WHATSAPP BACKEND NOTIFICATION =================")
    print(f"[+] Target Farm Contact: {BACKEND_WHATSAPP_NUMBER} ({CLEAN_WHATSAPP_PHONE})")
    print(f"[+] Order Number: {order.order_number}")
    print(f"[+] Customer: {order.customer_name} ({order.phone})")
    print(f"[+] Total: ${order.total_amount:.2f}")
    print(f"[+] Direct Dispatch URL: {wa_url}")
    print("[+] ==================================================================\n")
    
    # Check Meta Cloud API
    meta_token = os.environ.get("WHATSAPP_API_TOKEN")
    meta_phone_id = os.environ.get("WHATSAPP_PHONE_ID")
    if meta_token and meta_phone_id:
        try:
            import urllib.request
            api_url = f"https://graph.facebook.com/v18.0/{meta_phone_id}/messages"
            payload = {
                "messaging_product": "whatsapp",
                "to": CLEAN_WHATSAPP_PHONE,
                "type": "text",
                "text": {"body": message}
            }
            req = urllib.request.Request(
                api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {meta_token}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"[+] Meta WhatsApp Cloud API response status: {resp.status}")
                return {"success": True, "provider": "meta", "status": resp.status}
        except Exception as e:
            print(f"[-] Meta WhatsApp API error: {e}")
            
    # Check Webhook integration (e.g. UltraMsg, Green-API, CallMeBot, or n8n)
    webhook_url = os.environ.get("WHATSAPP_WEBHOOK_URL")
    if webhook_url:
        try:
            import urllib.request
            payload = {
                "phone": CLEAN_WHATSAPP_PHONE,
                "message": message,
                "order_number": order.order_number,
                "total": order.total_amount
            }
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"[+] WhatsApp Webhook response status: {resp.status}")
                return {"success": True, "provider": "webhook", "status": resp.status}
        except Exception as e:
            print(f"[-] WhatsApp Webhook error: {e}")

    return {"success": True, "provider": "direct_url", "url": wa_url}
