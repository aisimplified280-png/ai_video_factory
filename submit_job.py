import urllib.request, urllib.parse, time

time.sleep(2)  # wait for server to be ready

data = urllib.parse.urlencode({
    'topic': 'What is MCP - Model Context Protocol',
    'style': 'kinetic',
    'music': 'none',
    'duration': '30',
    'notes': ''
}).encode()

req = urllib.request.Request(
    'http://127.0.0.1:5000/create',
    data=data,
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
    method='POST'
)
try:
    resp = urllib.request.urlopen(req, timeout=10)
    print('Job submitted! Status:', resp.status)
except Exception as e:
    print('Error:', e)
