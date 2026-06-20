"""
FMS Flyer Generator
Generates a custom fundraiser flyer PNG from org details.
Usage: python3 generate_flyer.py "Org Name" "07/01/2026" "07/14/2026" "ORGCO" "/output/path.png"
"""
import sys, json, subprocess, os, tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def generate_flyer(org_name, start_date, end_date, fundraiser_code, output_path, logo_b64=None):
    # Load embedded images
    with open(os.path.join(SCRIPT_DIR, 'images.json')) as f:
        images = json.load(f)

    studio_src   = f"data:image/png;base64,{images['studio']}"
    product_srcs = [f"data:image/png;base64,{p}" for p in images['products']]

    # Read template
    with open(os.path.join(SCRIPT_DIR, 'flyer_template.html')) as f:
        html = f.read()

    # Org name short for footer
    org_name_short = org_name[:22] + ('...' if len(org_name) > 22 else '')

    # Logo content — either an uploaded logo or the placeholder box
    if logo_b64:
        logo_content = (
            f'<img src="data:image/png;base64,{logo_b64}" '
            f'style="width:180px;height:130px;object-fit:contain;border:2px solid #E8356D;" '
            f'alt="Organization Logo" />'
        )
    else:
        logo_content = '<div class="logo-box">YOUR<br>LOGO<br>HERE</div>'

    # Replace all placeholders
    html = html.replace('{{ORG_NAME}}',        org_name)
    html = html.replace('{{ORG_NAME_SHORT}}',  org_name_short)
    html = html.replace('{{START_DATE}}',      start_date)
    html = html.replace('{{END_DATE}}',        end_date)
    html = html.replace('{{FUNDRAISER_CODE}}', fundraiser_code)
    html = html.replace('{{LOGO_CONTENT}}',    logo_content)
    html = html.replace('{{STUDIO_PHOTO}}',    studio_src)

    # Replace product photo placeholders
    for i, src in enumerate(product_srcs):
        html = html.replace(f'{{{{PRODUCT_{i+1}}}}}', src)

    # Write to temp file
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as tf:
        tf.write(html)
        temp_path = tf.name

    # Render with Node.js/puppeteer
    render_script = os.path.join(SCRIPT_DIR, 'render_from_file.js')

    # Try to find node binary
    node_candidates = [
        '/home/ubuntu/.nvm/versions/node/v22.13.0/bin/node',
        '/usr/local/bin/node',
        '/usr/bin/node',
        'node',
    ]
    node_bin = 'node'
    for candidate in node_candidates:
        if os.path.exists(candidate):
            node_bin = candidate
            break

    result = subprocess.run(
        [node_bin, render_script, temp_path, output_path],
        capture_output=True, text=True,
        timeout=60
    )

    try:
        os.unlink(temp_path)
    except Exception:
        pass

    if result.returncode != 0:
        print("ERROR:", result.stderr[:500])
        return False

    print(result.stdout.strip())
    return True


if __name__ == '__main__':
    if len(sys.argv) >= 6:
        generate_flyer(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        # Test render
        generate_flyer(
            'Lincoln Elementary PTA',
            '07/01/2026',
            '07/14/2026',
            'LINCO',
            os.path.join(SCRIPT_DIR, 'test_flyer_v3.png')
        )
