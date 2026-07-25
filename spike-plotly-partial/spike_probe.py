"""Probe: what does a partial plotly dist do with an unsupported trace type?

Serves nicegui/elements/plotly/dist on a random high port, loads it in headless
chromium, plots several trace types, and reports console output + DOM result.
"""
import functools
import http.server
import json
import socket
import socketserver
import sys
import threading
from pathlib import Path

DIST = Path(__file__).parent / 'nicegui' / 'elements' / 'plotly' / 'dist'

PAGE = '''<!doctype html><html><body>
<div id="p" style="width:600px;height:400px"></div>
<script type="module">
import { Plotly } from "./index.js";
window.Plotly = Plotly;
window.ready = true;
</script>
</body></html>'''

CASES = {
    'scatter':      [{'type': 'scatter', 'x': [1, 2, 3], 'y': [1, 4, 9]}],
    'bar':          [{'type': 'bar', 'x': ['a', 'b'], 'y': [1, 2]}],
    'pie':          [{'type': 'pie', 'labels': ['a', 'b'], 'values': [1, 2]}],
    'scatter3d':    [{'type': 'scatter3d', 'x': [1, 2], 'y': [1, 2], 'z': [1, 2]}],
    'surface':      [{'type': 'surface', 'z': [[1, 2], [3, 4]]}],
    'scattermapbox': [{'type': 'scattermapbox', 'lat': [1, 2], 'lon': [1, 2]}],
    'choropleth':   [{'type': 'choropleth', 'locations': ['USA'], 'z': [1]}],
    'scattergl':    [{'type': 'scattergl', 'x': [1, 2], 'y': [1, 2]}],
    'mixed_3d_and_scatter': [
        {'type': 'scatter', 'x': [1, 2, 3], 'y': [1, 4, 9]},
        {'type': 'scatter3d', 'x': [1, 2], 'y': [1, 2], 'z': [1, 2]},
    ],
}


def serve(directory):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    handler.log_message = lambda *a, **k: None
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
    httpd = socketserver.TCPServer(('127.0.0.1', port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port


def main():
    (DIST / 'probe.html').write_text(PAGE)
    httpd, port = serve(DIST)
    results = {}
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            msgs = []
            page.on('console', lambda m: msgs.append(f'{m.type}: {m.text[:300]}'))
            page.on('pageerror', lambda e: msgs.append(f'pageerror: {str(e)[:300]}'))
            page.goto(f'http://127.0.0.1:{port}/probe.html')
            page.wait_for_function('window.ready === true', timeout=30000)

            registered = page.evaluate(
                'Object.keys(Plotly.PlotSchema.get().traces).sort()')
            results['_registered_traces'] = registered

            for name, data in CASES.items():
                msgs.clear()
                out = page.evaluate(
                    '''async (data) => {
                        const el = document.getElementById('p');
                        Plotly.purge(el);
                        let threw = null;
                        try { await Plotly.newPlot(el, data, {}); }
                        catch (e) { threw = String(e).slice(0, 300); }
                        return {
                            threw,
                            traceNodes: el.querySelectorAll('.trace').length,
                            svgPoints: el.querySelectorAll('.point, .points > *').length,
                            gd_data_len: (el.data || []).length,
                            fullData_len: (el._fullData || []).length,
                            fullDataTypes: (el._fullData || []).map(t => t.type),
                            hasPlotArea: !!el.querySelector('.main-svg') || !!el.querySelector('canvas'),
                        };
                    }''',
                    data,
                )
                out['console'] = list(msgs)
                results[name] = out
            browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
        (DIST / 'probe.html').unlink(missing_ok=True)
        # verify the port is free again
        try:
            with socket.socket() as s:
                s.bind(('127.0.0.1', port))
            print(f'[cleanup] port {port} released OK', file=sys.stderr)
        except OSError as e:
            print(f'[cleanup] PORT STILL BOUND: {e}', file=sys.stderr)

    print(json.dumps(results, indent=1))


if __name__ == '__main__':
    main()
