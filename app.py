"""
FMS Flyer Generator Service
Flask API that generates custom fundraiser flyers as PNG images.
Deployed on Render.com (free tier).
"""
import os
import json
import base64
import tempfile
import subprocess
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.environ.get('FMS_API_KEY', 'fms-secret-2026')

def generate_flyer_png(org_name, start_date, end_date, fundraiser_code):
    """Generate a flyer PNG using Pillow image overlay and return the file path."""
    import sys
    sys.path.insert(0, SCRIPT_DIR)
    from generate_flyer_v2 import generate_flyer

    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    tmp.close()
    generate_flyer(
        org_name        = org_name,
        start_date      = start_date,
        end_date        = end_date,
        fundraiser_code = fundraiser_code,
        output_path     = tmp.name
    )
    return tmp.name

def _generate_flyer_png_old(org_name, start_date, end_date, fundraiser_code):
    """DEPRECATED: old HTML/puppeteer approach kept for reference."""
    # Load embedded images
    with open(os.path.join(SCRIPT_DIR, 'images.json')) as f:
        images = json.load(f)

    studio_src = f"data:image/png;base64,{images['studio']}"
    product_srcs = [f"data:image/png;base64,{p}" for p in images['products']]

    # Read template
    with open(os.path.join(SCRIPT_DIR, 'flyer_template.html')) as f:
        html = f.read()

    # Replace placeholders
    org_name_short = org_name[:22] + ('...' if len(org_name) > 22 else '')
    html = html.replace('{{ORG_NAME}}', org_name)
    html = html.replace('{{ORG_NAME_SHORT}}', org_name_short)
    html = html.replace('{{START_DATE}}', start_date)
    html = html.replace('{{END_DATE}}', end_date)
    html = html.replace('{{FUNDRAISER_CODE}}', fundraiser_code)

    # Replace studio photo placeholder with real image
    html = html.replace(
        '<img src="https://images.squarespace-cdn.com/content/v1/6424b2e0f3d0f1290e8e3e3e/1680000000000-XXXXXXXXXXXXXXXX/studio-photo.jpg"\n           onerror="this.style.display=\'none\'"\n           alt="Forever Metal Studio" />',
        f'<img src="{studio_src}" alt="Forever Metal Studio" style="width:100%;height:100%;object-fit:cover;display:block;" />'
    )

    # Replace product photo placeholders with real images
    for src in product_srcs:
        html = html.replace(
            '<div class="product-photo-placeholder">photo</div>',
            f'<img class="product-photo" src="{src}" alt="product" />',
            1
        )

    # Write to temp HTML file
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', dir='/tmp') as tf:
        tf.write(html)
        temp_html = tf.name

    # Output PNG path
    output_png = tempfile.mktemp(suffix='.png', dir='/tmp')

    # Render with Node.js/puppeteer
    render_script = os.path.join(SCRIPT_DIR, 'render_from_file.js')
    node_bin = _find_node()

    result = subprocess.run(
        [node_bin, render_script, temp_html, output_png],
        capture_output=True, text=True, timeout=60
    )

    try:
        os.unlink(temp_html)
    except Exception:
        pass

    if result.returncode != 0:
        raise RuntimeError(f"Render failed: {result.stderr}")

    return output_png


def _find_node():
    """Find the node binary."""
    candidates = [
        '/home/ubuntu/.nvm/versions/node/v22.13.0/bin/node',
        '/usr/local/bin/node',
        '/usr/bin/node',
        'node',
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return 'node'


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'FMS Flyer Generator'})


@app.route('/generate-flyer', methods=['POST'])
def generate_flyer():
    """
    POST /generate-flyer
    Body (JSON):
      {
        "api_key": "fms-secret-2026",
        "org_name": "Lincoln Elementary PTA",
        "start_date": "07/01/2026",
        "end_date": "07/14/2026",
        "fundraiser_code": "LINCOLNPTA"
      }
    Returns: PNG image file
    """
    data = request.get_json(force=True)

    # Auth check
    if data.get('api_key') != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401

    # Validate required fields
    required = ['org_name', 'start_date', 'end_date', 'fundraiser_code']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Missing field: {field}'}), 400

    try:
        png_path = generate_flyer_png(
            org_name=data['org_name'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            fundraiser_code=data['fundraiser_code']
        )
        safe_name = data['fundraiser_code'].replace(' ', '_') + '_flyer.png'
        return send_file(
            png_path,
            mimetype='image/png',
            as_attachment=True,
            download_name=safe_name
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/generate-flyer-b64', methods=['POST'])
def generate_flyer_b64():
    """
    Same as /generate-flyer but returns base64-encoded PNG in JSON.
    Useful for Google Apps Script which can't easily handle binary responses.
    """
    data = request.get_json(force=True)

    if data.get('api_key') != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401

    required = ['org_name', 'start_date', 'end_date', 'fundraiser_code']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Missing field: {field}'}), 400

    try:
        png_path = generate_flyer_png(
            org_name=data['org_name'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            fundraiser_code=data['fundraiser_code']
        )
        with open(png_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()
        try:
            os.unlink(png_path)
        except Exception:
            pass
        return jsonify({
            'success': True,
            'filename': data['fundraiser_code'] + '_flyer.png',
            'image_b64': b64
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
