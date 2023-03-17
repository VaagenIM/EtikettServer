import io
import flask
import PIL.Image
from LabelGenerator import create_label, InventoryItem, LabelType
from flask_cors import CORS

app = flask.Flask(__name__)
CORS(app)

label_size = (901, 306)

# The offset of the label on the label sheet, might need some manual tweaking to get it right
x_offset = 15
y_offset = 12


def make_label(img: PIL.Image) -> PIL.Image:
    """Add the offset to the given image."""
    new_label = PIL.Image.new("RGB", label_size, color="white")
    new_label.paste(img, (x_offset, y_offset))
    return new_label


def request_to_json(request) -> dict:
    """Get the JSON from the given request, JSON if possible, otherwise form data."""
    try:
        return request.json
    except flask.wrappers.BadRequest:
        return request.values


def get_inventory_item(args: dict) -> tuple[InventoryItem, LabelType]:
    """Get the inventory item from the given arguments."""
    return InventoryItem(
        id=args.get('id', 'Mangler Løpenummer'),
        item_name=args.get('name', 'Mangler navn'),
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


@app.route('/', methods=['GET'])
def home():
    return """<html>
    <head>
        <title>Label Generator</title>
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.classless.min.css">
    </head>
    <body>
        <main>
            <center>
                <hgroup>
                    <h1>Vågens' Etikett Server</h1>
                    <h2>Made with ❤️ by <a href="https:github.com/sondregronas">Sondre Grønås</a></h2>
                </hgroup>
                <img src="/preview" alt="Forhåndsvisning" id="preview" style="height:120px; border: 5px solid white; border-radius: 5px;">
            </center>
            <br>
            <form action="/print" method="POST">
                <div class="form-group">
                    <label for="id">Løpenummer</label>
                    <input type="text" name="id" id="id" class="form-control" placeholder="Løpenummer (A6500-01)" onchange="updatePreview()">
                </div>
                <div class="form-group">
                    <label for="name">Enhetsnavn</label>
                    <input type="text" name="name" id="name" class="form-control" placeholder="Enhetsnavn (Sony A6500)" onchange="updatePreview()">
                </div>
                <div class="form-group">
                    <table>
                        <tr>
                            <td>
                                <label for="variant">Variant</label>
                                <select name="variant" id="variant" class="form-control" onchange="updatePreview()">
                                    <option value="qr">QR</option>
                                    <option value="barcode">Strekkode</option>
                                </select>
                            </td>
                            <td>
                                <label for="count">Antall</label>
                                <input type="number" name="count" id="count" class="form-control" value="1" onchange="enforceMinMax(this, 1, 9);">
                            </td>
                        </tr>
                    </table>
                </div>
            </form>
            <button class="btn btn-primary" onclick="printLabel(new FormData(document.querySelector('form')))">Send til printer</button>
            <p id="print-status"></p>
        </main>
        <script>
            function updatePreview() {
                let id = document.getElementById("id").value || "Mangler Løpenummer";
                let name = document.getElementById("name").value || "Mangler navn";
                document.getElementById("preview").src = `/preview?id=${id}&name=${name}&variant=${document.getElementById("variant").value}`;
            }
            function enforceMinMax(input, min, max) {
                if (input.value < min) {
                    input.value = min;
                } else if (input.value > max) {
                    input.value = max;
                }
            }
            function printLabel(data) {
                fetch("/print", {
                    method: "POST",
                    body: data
                }).then(response => {
                    let status = document.getElementById("print-status");
                    if (response.ok) {
                        status.innerText = `Skrev ut ${data.get("count")} etiketter for "${data.get("id")}"!`;
                        status.style.color = "green";
                    } else {
                        status.innerText = `Kunne ikke skrive ut etiketter for '${data.get("id")}'! Dersom feilen vedvarer, kontakt IT.`;
                        status.style.color = "red";
                    }
                });
            }
        </script>
    </body>
</html>"""


@app.route('/preview', methods=['GET', 'POST'])
def preview_raw():
    data = request_to_json(flask.request)
    item, variant = get_inventory_item(data)

    label = create_label(item, variant=variant)

    img_bytes = io.BytesIO()
    label.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    return flask.send_file(img_bytes, mimetype='image/png')


@app.route('/print', methods=['POST'])
def print_label():
    data = request_to_json(flask.request)
    item, variant = get_inventory_item(data)
    count = data.get('count', 1)

    if not item.id or not item.item_name:
        return flask.jsonify({
            'error': 'Missing required fields',
        }), 400

    label = create_label(item, variant=variant)
    label = make_label(label)

    img_bytes = io.BytesIO()
    label.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    print(f"Printed {count} labels for {item}. (NOT IMPLEMENTED YET)")

    return flask.redirect('/')


app.run(host='0.0.0.0', port=5000)
