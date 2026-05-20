#!/bin/bash
set -e

# Patch entrypoint to tolerate chown errors on bind mounts
python -c "
d = open('/docker-entrypoint.sh').read()
for target in ['/data', '/home/senaite']:
    old = 'find ' + target + '  -not -user senaite -exec chown senaite:senaite {} \\\\+'
    new = old + ' || true'
    d = d.replace(old, new)
open('/docker-entrypoint.sh', 'w').write(d)
print('patched: ' + target)
"

exec /docker-entrypoint.sh "$@"
