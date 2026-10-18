"""PrintWorks - event-driven logic written in PyScript.

Events used:
  input / change  -> live quote calculator, search filter, rush toggle
  timer (asyncio) -> automatic promo ads rotate every few seconds
  mouseenter/leave-> hovering pauses the ads
  click           -> close button hides the bottom promo bar
  change          -> file picker validates and appends files to print
  click           -> add to order, remove item, remove attached file, track order
  submit          -> order form and contact form with validation
"""
import time
import random
import asyncio
from html import escape
from pyscript import document, when, window

# ---------- Data ----------
SERVICES = [
    {"id": "bw",    "name": "Document Printing (B&W)",    "unit": "page",  "price": 2,   "desc": "Short, A4 or legal bond paper"},
    {"id": "color", "name": "Document Printing (Color)",  "unit": "page",  "price": 8,   "desc": "Full color, sharp text and graphics"},
    {"id": "copy",  "name": "Photocopy",                  "unit": "page",  "price": 1.5, "desc": "Quick copies, any paper size up to A4"},
    {"id": "photo", "name": "Photo Printing (4R)",        "unit": "photo", "price": 15,  "desc": "Glossy or matte finish"},
    {"id": "tarp",  "name": "Tarpaulin Printing",         "unit": "sq ft", "price": 18,  "desc": "Banners for events and stores"},
    {"id": "card",  "name": "Business Cards (100 pcs)",   "unit": "set",   "price": 250, "desc": "Both sides, 300gsm card"},
    {"id": "lam",   "name": "Lamination",                 "unit": "sheet", "price": 20,  "desc": "IDs, certificates and posters"},
    {"id": "bind",  "name": "Spiral Binding",             "unit": "book",  "price": 45,  "desc": "Clear cover and back page included"},
]
CONTACT_EMAIL = "printworks@example.com"
MAX_FILE_MB = 10
ALLOWED_EXT = (".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png")
DISCOUNT_MIN = 500      # subtotal that unlocks the discount
DISCOUNT_RATE = 0.10
RUSH_RATE = 0.20

cart = {}          # service id -> quantity
orders = {}        # reference number -> order info
selected_files = [] # list of attached file JS File objects


# ---------- Helpers ----------
def el(element_id):
    return document.getElementById(element_id)


def money(value):
    return f"\u20b1{value:,.2f}"


def service(sid):
    return next(s for s in SERVICES if s["id"] == sid)


def compute(subtotal, rush):
    """Return (rush_fee, discount, total) for a subtotal."""
    rush_fee = subtotal * RUSH_RATE if rush else 0
    discount = subtotal * DISCOUNT_RATE if subtotal >= DISCOUNT_MIN else 0
    return rush_fee, discount, subtotal + rush_fee - discount


def breakdown_html(subtotal, rush):
    rush_fee, discount, total = compute(subtotal, rush)
    rows = f"<dt>Subtotal</dt><dd>{money(subtotal)}</dd>"
    if rush_fee:
        rows += f"<dt>Rush fee</dt><dd>{money(rush_fee)}</dd>"
    if discount:
        rows += f"<dt>Bulk discount</dt><dd>-{money(discount)}</dd>"
    rows += f"<dt class='total'>Total</dt><dd class='total'>{money(total)}</dd>"
    return rows


def show_msg(element_id, text, ok=True):
    box = el(element_id)
    if box:
        box.textContent = text
        box.className = "msg ok" if ok else "msg error"


def read_qty(value):
    """Convert text from a number input into a positive whole number, or 0."""
    try:
        qty = int(float(value))
    except (TypeError, ValueError):
        return 0
    return qty if qty > 0 else 0


# ---------- Rendering ----------
def render_services(filter_text=""):
    text = filter_text.strip().lower()
    cards = ""
    for s in SERVICES:
        if text and text not in s["name"].lower() and text not in s["desc"].lower():
            continue
        cards += f"""
        <article class="card">
          <h3>{s['name']}</h3>
          <p>{s['desc']}</p>
          <p class="price">{money(s['price'])} <span>per {s['unit']}</span></p>
          <div class="add-row">
            <input id="qty-{s['id']}" type="number" min="1" value="1" aria-label="Quantity for {s['name']}">
            <button class="btn small" data-add="{s['id']}">Add</button>
          </div>
        </article>"""
    if not cards:
        cards = "<p class='empty'>No service matches that search. Try a shorter word like \"print\" or \"card\".</p>"
    el("service-grid").innerHTML = cards


def render_calc():
    sid = el("calc-service").value
    qty = read_qty(el("calc-qty").value)
    if qty == 0:
        el("calc-out").innerHTML = "<dt>Enter a quantity of 1 or more</dt><dd></dd>"
        return
    subtotal = service(sid)["price"] * qty
    el("calc-out").innerHTML = breakdown_html(subtotal, el("calc-rush").checked)


def cart_subtotal():
    return sum(service(sid)["price"] * qty for sid, qty in cart.items())


def render_cart():
    if not cart:
        el("cart-body").innerHTML = "<tr><td colspan='4' class='empty'>Your order is empty. Add a service above.</td></tr>"
    else:
        rows = ""
        for sid, qty in cart.items():
            s = service(sid)
            rows += (f"<tr><td>{s['name']}</td><td>{qty} {s['unit']}</td>"
                     f"<td>{money(s['price'] * qty)}</td>"
                     f"<td><button class='link' data-remove='{sid}'>Remove</button></td></tr>")
        el("cart-body").innerHTML = rows
    el("cart-out").innerHTML = breakdown_html(cart_subtotal(), el("rush").checked)


def add_to_cart(sid, qty):
    cart[sid] = cart.get(sid, 0) + qty
    render_cart()


def render_file_list():
    """Renders all attached files with individual Remove buttons."""
    list_el = el("file-list")
    if not list_el:
        return
    
    if not selected_files:
        list_el.innerHTML = ""
        return
        
    items = ""
    for idx, f in enumerate(selected_files):
        items += f"""
        <li style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; padding: 4px 8px; background: rgba(0,0,0,0.05); border-radius: 4px;">
            <span>📄 <strong>{escape(str(f.name))}</strong> ({f.size / 1024:,.0f} KB)</span>
            <button type="button" class="link" data-remove-file="{idx}" style="color: #c00; font-weight: bold; cursor: pointer; border: none; background: none;">Remove</button>
        </li>
        """
    list_el.innerHTML = items


# ---------- Events ----------
@when("input", "#calc-form")
def on_calc_change(event):
    render_calc()


@when("click", "#calc-add")
def on_calc_add(event):
    qty = read_qty(el("calc-qty").value)
    if qty == 0:
        show_msg("calc-msg", "Enter a quantity of 1 or more first.", ok=False)
        return
    add_to_cart(el("calc-service").value, qty)
    show_msg("calc-msg", "Added. See it under Your order.")


@when("input", "#search")
def on_search(event):
    render_services(el("search").value)


@when("click", "#service-grid")
def on_add_click(event):
    button = event.target.closest("button[data-add]")
    if button is None:
        return
    sid = button.dataset.add
    qty = read_qty(el(f"qty-{sid}").value)
    if qty == 0:
        el(f"qty-{sid}").value = 1
        return
    add_to_cart(sid, qty)


@when("click", "#cart-body")
def on_remove_click(event):
    button = event.target.closest("button[data-remove]")
    if button is None:
        return
    cart.pop(button.dataset.remove, None)
    render_cart()


@when("change", "#rush")
def on_rush_toggle(event):
    render_cart()


# ---------- File to print ----------
def validate_file(f):
    """Return a problem message, or None if the file is fine."""
    if not str(f.name).lower().endswith(ALLOWED_EXT):
        return f"File '{f.name}' type isn't supported. Use PDF, Word, JPG or PNG."
    if f.size > MAX_FILE_MB * 1024 * 1024:
        return f"File '{f.name}' is {f.size / 1024 / 1024:.1f} MB. The limit is {MAX_FILE_MB} MB."
    return None


@when("change", "#file")
def on_file_change(event):
    files = el("file").files
    if files.length == 0:
        return
    
    problems = []
    added_count = 0
    for i in range(files.length):
        f = files.item(i)
        problem = validate_file(f)
        if problem:
            problems.append(problem)
        else:
            selected_files.append(f)
            added_count += 1

    render_file_list()
    el("file").value = ""  # clear input so user can pick more if needed

    if problems:
        show_msg("file-msg", " ".join(problems), ok=False)
    else:
        show_msg("file-msg", f"Added {added_count} file(s).")


@when("click", "#file-list")
def on_remove_file_click(event):
    button = event.target.closest("button[data-remove-file]")
    if button is None:
        return
    try:
        idx = int(button.getAttribute("data-remove-file"))
    except (ValueError, TypeError):
        return
    if 0 <= idx < len(selected_files):
        removed = selected_files.pop(idx)
        render_file_list()
        show_msg("file-msg", f"Removed {removed.name}.")


@when("change", "#c-file")
def on_contact_file_change(event):
    files = el("c-file").files
    f = files.item(0) if files.length > 0 else None
    if f is None:
        show_msg("c-file-msg", "")
        return
    problem = validate_file(f)
    if problem:
        show_msg("c-file-msg", problem, ok=False)
        el("c-file").value = ""
    else:
        show_msg("c-file-msg", f"Attached: {f.name} ({f.size / 1024:,.0f} KB)")


@when("submit", "#order-form")
def on_order_submit(event):
    event.preventDefault()
    name = el("name").value.strip()
    phone = el("phone").value.strip()
    digits = "".join(ch for ch in phone if ch.isdigit())

    if not cart:
        show_msg("order-msg", "Your order is empty. Add at least one service.", ok=False)
    elif len(name) < 2:
        show_msg("order-msg", "Enter your full name.", ok=False)
    elif len(digits) < 10 or len(digits) > 12:
        show_msg("order-msg", "Enter a valid mobile number, for example 09171234567.", ok=False)
    else:
        rush = el("rush").checked
        total = compute(cart_subtotal(), rush)[2]
        ref = f"PW-{random.randint(1000, 9999)}"
        while ref in orders:
            ref = f"PW-{random.randint(1000, 9999)}"
        
        file_names = [str(f.name) for f in selected_files]
        orders[ref] = {
            "name": name, 
            "placed": time.time(), 
            "rush": rush,
            "files": file_names, 
            "notes": el("notes").value.strip()
        }
        
        attached = f"{len(file_names)} file(s) attached ({', '.join(file_names)}). " if file_names else "No files attached. "
        show_msg("order-msg",
                 f"Thank you, {name}! Order {ref} is received. Total: {money(total)}. "
                 f"{el('method').value}. {attached}"
                 f"Send your files to {CONTACT_EMAIL} and include {ref}.")
        
        # Reset form & state
        cart.clear()
        selected_files.clear()
        render_file_list()
        
        el("name").value = ""
        el("phone").value = ""
        el("rush").checked = False
        el("notes").value = ""
        el("file").value = ""
        show_msg("file-msg", "")
        render_cart()


@when("click", "#track-btn")
def on_track(event):
    ref = el("ref").value.strip().upper()
    order = orders.get(ref)
    if order is None:
        show_msg("track-msg", "No order found with that reference number. Check it and try again.", ok=False)
        return
    elapsed = time.time() - order["placed"]
    step = 10 if order["rush"] else 20
    if elapsed < step:
        status = "Received. We are preparing your files."
    elif elapsed < step * 3:
        status = "Printing."
    else:
        status = "Ready for pickup or delivery."
    show_msg("track-msg", f"{ref} for {order['name']}: {status}")


@when("submit", "#contact-form")
def on_contact_submit(event):
    event.preventDefault()
    email = el("c-email").value.strip()
    message = el("c-msg").value.strip()
    files = el("c-file").files
    f = files.item(0) if files.length > 0 else None
    file_problem = validate_file(f) if f is not None else None
    
    if "@" not in email or "." not in email.split("@")[-1]:
        show_msg("contact-msg", "Enter a valid email address.", ok=False)
    elif len(message) < 5:
        show_msg("contact-msg", "Write a message of at least 5 characters.", ok=False)
    elif file_problem:
        show_msg("contact-msg", file_problem, ok=False)
    else:
        extra = f" File attached: {escape(str(f.name))}. Please also email it to {CONTACT_EMAIL}." if f is not None else ""
        show_msg("contact-msg", f"Message sent. We will reply to {escape(email)} soon.{extra}")
        el("c-email").value = ""
        el("c-msg").value = ""
        el("c-file").value = ""
        show_msg("c-file-msg", "")


# ---------- Automatic promo ads ----------
ADS = [
    {"tone": "cyan",    "title": "Student special",   "text": "Thesis and reports, printed clean and ready to bind.", "sid": "bw",    "qty": 100},
    {"tone": "magenta", "title": "Event banners",     "text": "A 3x4 ft tarpaulin for your birthday, fiesta or shop opening.", "sid": "tarp",  "qty": 12},
    {"tone": "yellow",  "title": "Look professional", "text": "Business cards, ready in a day for your small business.", "sid": "card",  "qty": 1},
    {"tone": "ink",     "title": "Keep the memories", "text": "Glossy or matte photo prints for frames and gifts.", "sid": "photo", "qty": 20},
]
AD_SECONDS = 4
ad_index = 0
ad_paused = False


def render_ad():
    ad = ADS[ad_index]
    s = service(ad["sid"])
    el("ad-banner").setAttribute("data-tone", ad["tone"])
    el("ad-slide").innerHTML = (
        f"<h2>{ad['title']}</h2><p>{ad['text']}</p>"
        f"<button class='btn' data-ad='{ad_index}'>Add {ad['qty']} {s['unit']} for {money(s['price'] * ad['qty'])}</button>"
    )
    el("ad-dots").innerHTML = "".join(
        f"<button data-dot='{i}' class='{'on' if i == ad_index else ''}' aria-label='Show ad {i + 1}'></button>"
        for i in range(len(ADS))
    )


async def ad_loop():
    global ad_index
    while True:
        await asyncio.sleep(AD_SECONDS)
        if not ad_paused:
            ad_index = (ad_index + 1) % len(ADS)
            render_ad()


@when("mouseenter", "#ad-banner")
def on_ad_pause(event):
    global ad_paused
    ad_paused = True


@when("mouseleave", "#ad-banner")
def on_ad_resume(event):
    global ad_paused
    ad_paused = False


@when("click", "#ad-banner")
def on_ad_click(event):
    global ad_index
    dot = event.target.closest("button[data-dot]")
    if dot is not None:
        ad_index = int(dot.dataset.dot)
        render_ad()
        return
    button = event.target.closest("button[data-ad]")
    if button is not None:
        ad = ADS[int(button.dataset.ad)]
        add_to_cart(ad["sid"], ad["qty"])
        show_msg("ad-msg", f"Added {ad['qty']} x {service(ad['sid'])['name']} to your order.")


@when("click", "#promo-close")
def on_promo_close(event):
    el("promo-bar").hidden = True


# ---------- Start up ----------
try:
    el("calc-service").innerHTML = "".join(
        f"<option value='{s['id']}'>{s['name']} ({money(s['price'])}/{s['unit']})</option>" for s in SERVICES
    )
    el("send-email").textContent = CONTACT_EMAIL
    render_services()
    render_calc()
    render_cart()
    render_file_list()
    render_ad()
    asyncio.ensure_future(ad_loop())
    el("py-status").hidden = True
except Exception as error:
    el("py-status").textContent = f"The interactive features failed to load: {error}"
    raise