from pyscript import document
from js import FileReader, window
import random

# --- Global State ---
cart = []
attached_files = []

# --- Services Data ---
services = [
    {"id": "doc-bw", "name": "Document Printing (B&W)", "price": 2.00, "unit": "page"},
    {"id": "doc-color", "name": "Document Printing (Color)", "price": 5.00, "unit": "page"},
    {"id": "tarp", "name": "Tarpaulin Printing", "price": 150.00, "unit": "sq.ft"},
    {"id": "photo", "name": "Photo Printing (4R)", "price": 15.00, "unit": "piece"},
    {"id": "card", "name": "Business Cards (Box of 100)", "price": 250.00, "unit": "box"}
]

def init_services():
    grid = document.getElementById("service-grid")
    select = document.getElementById("calc-service")
    if not grid or not select:
        return

    grid.innerHTML = ""
    select.innerHTML = ""

    for s in services:
        # Populate service grid
        card = document.createElement("div")
        card.className = "service-card"
        card.innerHTML = f"<h3>{s['name']}</h3><p>₱{s['price']:.2f} per {s['unit']}</p>"
        grid.appendChild(card)

        # Populate calculator dropdown
        opt = document.createElement("option")
        opt.value = s["id"]
        opt.text = f"{s['name']} (₱{s['price']:.2f}/{s['unit']})"
        select.appendChild(opt)

# --- Quick Quote Calculator ---
def update_calc(event=None):
    service_id = document.getElementById("calc-service").value
    qty = int(document.getElementById("calc-qty").value or 1)
    rush = document.getElementById("calc-rush").checked

    selected_service = next((s for s in services if s["id"] == service_id), None)
    if not selected_service:
        return

    subtotal = selected_service["price"] * qty
    rush_fee = subtotal * 0.20 if rush else 0.0
    total = subtotal + rush_fee

    out = document.getElementById("calc-out")
    out.innerHTML = f"<dt>Subtotal</dt><dd>₱{subtotal:.2f}</dd>"
    if rush:
        out.innerHTML += f"<dt>Rush Fee (+20%)</dt><dd>₱{rush_fee:.2f}</dd>"
    out.innerHTML += f"<dt>Total</dt><dd><strong>₱{total:.2f}</strong></dd>"

# --- Cart Management ---
def add_to_cart(event=None):
    service_id = document.getElementById("calc-service").value
    qty = int(document.getElementById("calc-qty").value or 1)
    rush = document.getElementById("calc-rush").checked

    selected_service = next((s for s in services if s["id"] == service_id), None)
    if not selected_service:
        return

    price = selected_service["price"] * qty
    if rush:
        price *= 1.20

    item_name = f"{selected_service['name']} ({qty} {selected_service['unit']})"
    cart.append({"name": item_name, "qty": qty, "amount": price})
    
    render_cart()
    document.getElementById("calc-msg").innerText = "Added to your order!"

def remove_from_cart(event):
    # Retrieve index from data attribute safely
    idx_str = event.target.getAttribute("data-index")
    if idx_str is not None:
        idx = int(idx_str)
        if 0 <= idx < len(cart):
            cart.pop(idx)
            render_cart()

def render_cart():
    tbody = document.getElementById("cart-body")
    tbody.innerHTML = ""
    
    subtotal = sum(item["amount"] for item in cart)
    discount = subtotal * 0.10 if subtotal >= 500 else 0.0
    total = subtotal - discount

    for i, item in enumerate(cart):
        tr = document.createElement("tr")
        tr.innerHTML = f"""
            <td>{item['name']}</td>
            <td>{item['qty']}</td>
            <td>₱{item['amount']:.2f}</td>
            <td><button type="button" class="btn small" data-index="{i}" py-click="remove_from_cart">Remove</button></td>
        """
        tbody.appendChild(tr)

    out = document.getElementById("cart-out")
    out.innerHTML = f"<dt>Subtotal</dt><dd>₱{subtotal:.2f}</dd>"
    if discount > 0:
        out.innerHTML += f"<dt>Discount (10%)</dt><dd>-₱{discount:.2f}</dd>"
    out.innerHTML += f"<dt>Total</dt><dd><strong>₱{total:.2f}</strong></dd>"

# --- Multi-File Upload & Removal ---
def handle_file_upload(event):
    files = document.getElementById("file").files
    file_list_elem = document.getElementById("file-list")
    file_msg = document.getElementById("file-msg")
    
    if not files:
        return

    for i in range(files.length):
        f = files.item(i)
        if f.size > 10 * 1024 * 1024:
            file_msg.innerText = f"File {f.name} exceeds 10MB limit."
            continue
        attached_files.append(f)

    render_file_list()
    file_msg.innerText = f"Added {files.length} file(s)."

def remove_file(event):
    idx_str = event.target.getAttribute("data-remove-file")
    if idx_str is not None:
        idx = int(idx_str)
        if 0 <= idx < len(attached_files):
            attached_files.pop(idx)
            render_file_list()

def render_file_list():
    file_list_elem = document.getElementById("file-list")
    if not file_list_elem:
        return
    
    file_list_elem.innerHTML = ""
    for i, f in enumerate(attached_files):
        li = document.createElement("li")
        li.style.display = "flex"
        li.style.justifyContent = "space-between"
        li.style.alignItems = "center"
        li.style.margin = "4px 0"
        
        file_info = document.createElement("span")
        file_info.innerText = f"{f.name} ({(f.size / 1024):.1f} KB)"
        
        rem_btn = document.createElement("button")
        rem_btn.type = "button"
        rem_btn.className = "btn small"
        rem_btn.innerText = "Remove"
        rem_btn.setAttribute("data-remove-file", str(i))
        rem_btn.setAttribute("py-click", "remove_file")
        
        li.appendChild(file_info)
        li.appendChild(rem_btn)
        file_list_elem.appendChild(li)

# --- Dynamic Claim Method & Delivery Address Toggle ---
def toggle_delivery_address(event=None):
    method_dropdown = document.getElementById("method")
    address_label = document.getElementById("address-label")
    
    if method_dropdown and address_label:
        if method_dropdown.value == "Delivery":
            address_label.style.display = "block"
        else:
            address_label.style.display = "none"

# --- Order Submission Validation ---
def submit_order(event):
    event.preventDefault()
    name = document.getElementById("name").value.strip()
    phone = document.getElementById("phone").value.strip()
    method = document.getElementById("method").value
    address = document.getElementById("address").value.strip()
    msg = document.getElementById("order-msg")

    if not name or not phone:
        msg.innerText = "Please fill in your name and mobile number."
        return

    if not cart:
        msg.innerText = "Your cart is empty. Please add items to your order."
        return

    if method == "Delivery" and not address:
        msg.innerText = "Please enter your delivery address."
        return

    ref_num = f"PW-{random.randint(1000, 9999)}"
    msg.style.color = "green"
    msg.innerText = f"Order placed successfully! Reference: {ref_num}"
    
    # Clear cart and files after successful order
    cart.clear()
    attached_files.clear()
    render_cart()
    render_file_list()

# --- Initialization & Event Listeners ---
def main():
    init_services()

    # Calculator listeners
    document.getElementById("calc-service").addEventListener("change", update_calc)
    document.getElementById("calc-qty").addEventListener("input", update_calc)
    document.getElementById("calc-rush").addEventListener("change", update_calc)
    document.getElementById("calc-add").addEventListener("click", add_to_cart)

    # File upload listener
    document.getElementById("file").addEventListener("change", handle_file_upload)

    # Claim method dropdown listener for Delivery Address toggle
    method_elem = document.getElementById("method")
    if method_elem:
        method_elem.addEventListener("change", toggle_delivery_address)

    # Order form submission
    document.getElementById("order-form").addEventListener("submit", submit_order)

    # Initial calculation render
    update_calc()

# Run main setup
main()