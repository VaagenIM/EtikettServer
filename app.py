from typing import Tuple

import flask
from LabelGenerator import create_label, InventoryItem, LabelType

app = flask.Flask(__name__)


def get_inventory_item(args: dict) -> tuple[InventoryItem, LabelType]:
    """Get the inventory item from the given arguments."""
    return InventoryItem(
        id=args.get('id', 'N/A'),
        item_name=args.get('name', 'N/A'),
    ), get_variant(args.get('variant'))


def get_variant(variant: str) -> LabelType:
    """Get the label type from the given variant."""
    default = LabelType.QR
    try:
        return {
            'qr': LabelType.QR,
            'barcode': LabelType.BARCODE,
        }.get(variant.lower(), default)
    except AttributeError:
        return default


@app.route('/preview.png', methods=['GET'])
def preview_png():
    return flask.send_file("preview.png", mimetype='image/png')


@app.route('/', methods=['GET'])
def home():
    return """<html>
    <head>
        <title>Label Generator</title>
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.classless.min.css">
    </head>
    <body>
        <main>
            <h1>Label Generator</h1>
            <form action="/preview" method="get">
                <div class="form-group">
                    <label for="id">ID</label>
                    <input type="text" name="id" id="id" class="form-control" placeholder="ID">
                </div>
                <div class="form-group">
                    <label for="name">Name</label>
                    <input type="text" name="name" id="name" class="form-control" placeholder="Name">
                </div>
                <div class="form-group">
                    <label for="variant">Variant</label>
                    <select name="variant" id="variant" class="form-control">
                        <option value="qr">QR</option>
                        <option value="barcode">Barcode</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">Preview</button>
            </form>
        </main>
    </body>
</html>"""


@app.route('/preview', methods=['POST'])
def preview():
    item, variant = get_inventory_item(flask.request.args)
    label = create_label(item, variant=variant)
    label.save("preview.png")

    # display the image
    return """<html>
    <head>
        <title>Label Generator</title>
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.classless.min.css">
    </head>
    <body>
        <main>
            <h1>Label Generator</h1>
            <img src="/preview.png" alt="Preview" style="width:100%;">
            <br>
            <br>
            <form action="/print" method="post">
                <input type="hidden" name="id" value="{item_id}">
                <input type="hidden" name="name" value="{item_name}">
                <input type="hidden" name="variant" value="{variant}">
                <button type="submit" class="btn btn-primary">Print</button>
            </form>
        </main>
    </body>
</html>""".format(item_id=item.id, item_name=item.item_name, variant=variant)


@app.route('/preview', methods=['GET'])
def preview_post():
    item, variant = get_inventory_item(flask.request.args)
    label = create_label(item, variant=variant)
    label.save("preview.png")

    return flask.send_file("preview.png", mimetype='image/png')


@app.route('/print', methods=['POST'])
def print_label():
    item, variant = get_inventory_item(flask.request.args)
    label = create_label(item, variant=variant)

    return "NOT IMPLEMENTED YET"


app.run(host='localhost', port=5000)
