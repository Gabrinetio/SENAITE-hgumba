import sys

with open('/docker-entrypoint.sh', 'r') as f:
    content = f.read()

old = 'find /data  -not -user senaite -exec chown senaite:senaite {} \\+'
new = old + ' || true'
content = content.replace(old, new)

old = 'find /home/senaite -not -user senaite -exec chown senaite:senaite {} \\+'
new = old + ' || true'
content = content.replace(old, new)

with open('/docker-entrypoint.sh', 'w') as f:
    f.write(content)

print("entrypoint patched successfully")
sys.exit(0)
