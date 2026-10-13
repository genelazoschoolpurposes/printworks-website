# PrintWorks: Printing Services Website

Final project for Event-Driven Programming. An interactive business website for a printing service, built with HTML, CSS and PyScript.

## Features (and the events behind them)

| Feature | Event |
|---|---|
| Live quote calculator (service, quantity, rush fee, bulk discount) | `input` |
| Service search filter | `input` |
| Add to order / remove from order | `click` (event delegation) |
| Rush toggle updates the order total | `change` |
| Order form with validation and reference number | `submit` |
| Order tracking with simulated status | `click` |
| Contact form with validation | `submit` |

## Run it

PyScript loads `main.py` with a request, so opening `index.html` by double-click will not work. Use one of these:

1. **Local:** in this folder run `python -m http.server 8000`, then open http://localhost:8000
2. **GitHub Pages:** Settings > Pages > Deploy from branch `main` > `/ (root)`. Your site will be at `https://<username>.github.io/<repo>/`

## Files

- `index.html`: page structure and PyScript tag
- `style.css`: layout and design
- `main.py`: all interactive logic (Python)

## Team contributions

| Member | Contribution |
|---|---|
| Member 1 | HTML structure and content |
| Member 2 | CSS and design |
| Member 3 | Calculator and search (`main.py`) |
| Member 4 | Cart, order form and validation (`main.py`) |

Replace with your real names and update as the project grows.
