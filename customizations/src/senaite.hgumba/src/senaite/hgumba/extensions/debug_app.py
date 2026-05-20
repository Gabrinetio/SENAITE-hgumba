print("Type of app:", type(app))
print("Dir of app:", [x for x in dir(app) if not x.startswith('_')])
# Check if it's a dict-like
try:
    print("Keys:", app.keys())
except:
    print("Not a mapping")
# Check items
try:
    print("Items:", app.items())
except:
    print("No items")
# Try to traverse
try:
    print("Has senaite:", hasattr(app, 'senaite'))
except:
    print("hasattr failed")
