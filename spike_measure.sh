#!/bin/bash
PORT=$1
cd /Users/evnchn/worktrees/tierb-importmap-filter
/Users/evnchn/nicegui/.venv/bin/python spike_app.py $PORT > /tmp/spike_server_$PORT.log 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null; wait $SRV 2>/dev/null' EXIT
for i in $(seq 1 40); do curl -sf -o /dev/null http://127.0.0.1:$PORT/ && break; sleep 0.5; done
curl -s http://127.0.0.1:$PORT/ > /tmp/spike_hello_$PORT.html
echo "raw_bytes: $(wc -c < /tmp/spike_hello_$PORT.html)"
echo "gzip_bytes: $(gzip -9 -c /tmp/spike_hello_$PORT.html | wc -c)"
python3 - "$PORT" <<'PY'
import json,re,sys
p=sys.argv[1]
h=open(f'/tmp/spike_hello_{p}.html').read()
m=re.search(r'\{"imports": (\{.*?\})\}\s*</script>', h, re.S)
d=json.loads(m.group(1))
print('importmap_entries:', len(d))
print('importmap_json_bytes:', len(m.group(1)))
esm=[k for k in d if k.startswith('nicegui-')]
print('esm_entries:', len(esm))
PY
