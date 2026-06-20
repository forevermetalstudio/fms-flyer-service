"""
FMS Flyer Generator
Generates a custom fundraiser flyer PNG from org details.
Usage: python3 generate_flyer.py "Org Name" "07/01/2026" "07/14/2026" "ORGCODE" "/output/path.png"
"""
import sys, json, subprocess, os, tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def generate_flyer(org_name, start_date, end_date, fundraiser_code, output_path):
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
    product_labels = [
        ('Permanent<br>Jewelry', '✨'),
        ('Trucker<br>Hats', '🧢'),
        ('Cowboy<br>Hats', '🤠'),
        ('Custom<br>Tumblers', '🥤'),
        ('Personalized<br>Gifts', '🎁'),
        ('Engraved<br>Keepsakes', '💝'),
    ]
    for i, src in enumerate(product_srcs):
        html = html.replace(
            f'<div class="product-photo-placeholder">photo</div>',
            f'<img class="product-photo" src="{src}" alt="product" />',
            1  # replace one at a time
        )

    # Write to temp file
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as tf:
        tf.write(html)
        temp_path = tf.name

    # Render with Node.js/puppeteer
    render_script = os.path.join(SCRIPT_DIR, 'render_from_file.js')
    node_bin = '/home/ubuntu/.nvm/versions/node/v22.13.0/bin/node'

    result = subprocess.run(
        [node_bin, render_script, temp_path, output_path],
        capture_output=True, text=True
    )

    os.unlink(temp_path)

    if result.returncode != 0:
        print("ERROR:", result.stderr)
        return False

    print(result.stdout.strip())
    return True


if __name__ == '__main__':
    if len(sys.argv) >= 6:
        generate_flyer(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        # Test
        generate_flyer(
            'Lincoln Elementary PTA',
            '07/01/2026',
            '07/14/2026',
            'LINCOLNPTA',
            os.path.join(SCRIPT_DIR, 'test_flyer_v2.png')
        )
