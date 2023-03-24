import io
import time
import usb.core
import flask
import PIL.Image
from LabelGenerator import create_label, InventoryItem, LabelType
from flask_cors import CORS
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
from brother_ql.raster import BrotherQLRaster

app = flask.Flask(__name__)
CORS(app)

fqdn = ""  # If empty, all connections are allowed

# brother-ql config
label_size = (1132, 330)
#ql_backend = 'linux_kernel'
#ql_printer = '/dev/usb/lp0'
ql_backend = 'pyusb'
ql_printer = 'usb://0x04f9:0x209c'
ql_model = 'QL-810W'
ql_label = "17x54"

# The offset of the label on the label sheet, might need some manual tweaking to get it right
x_offset = 15
y_offset = -4


def make_label(img: PIL.Image) -> PIL.Image:
    """Add the offset to the given image."""
    new_label = PIL.Image.new("RGB", label_size, color="white")
    new_label.paste(img, (x_offset, y_offset))
    return new_label


def request_to_json(request) -> dict:
    """Get the JSON from the given request, JSON if possible, otherwise form data."""
    try:
        if not request.json:
            raise flask.wrappers.BadRequest("No JSON")
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


@app.route('/favicon.ico')
def favicon():
    return flask.send_file("favicon.ico", mimetype='image/vnd.microsoft.icon')


@app.route('/', methods=['GET'])
def home():
    if fqdn and fqdn != flask.request.headers.get('Host'):
        return flask.redirect(fqdn)

    return """<html>
    <head>
        <title>Label Generator</title>
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.classless.min.css">
        <link rel="icon" href="favicon.ico">
    </head>
    <body>
        <main>
            <center>
                <hgroup>
                    <h1>Vågens' Etikett Server</h1>
                    <h2>Made with ❤️ by <a href="https:github.com/VaagenIM/EtikettServer">Sondre Grønås</a></h2>
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
                    if (response.status === 200) {
                        status.innerText = `Skrev ut en etikett for "${data.get("id")}"!`;
                        status.style.color = "green";
                    } else {
                        status.innerText = `${response.status} ${response.statusText} - Kunne ikke skrive ut etiketter for '${data.get("id")}'! Dersom feilen vedvarer, kontakt IT.`;
                        status.style.color = "red";
                    }
                });
            }
        </script>
    </body>
</html>"""


@app.route('/preview', methods=['GET', 'POST'])
def preview_raw():
    if fqdn and fqdn != flask.request.headers.get('Host'):
        return flask.redirect(fqdn)

    data = request_to_json(flask.request)
    item, variant = get_inventory_item(data)

    label = create_label(item, variant=variant)

    img_bytes = io.BytesIO()
    label.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    return flask.send_file(img_bytes, mimetype='image/png')


@app.route('/print', methods=['POST'])
def print_label():
    try:
        dev = usb.core.find(idVendor=0x04f9, idProduct=0x209c)
        dev.reset()
    except Exception:
        return flask.jsonify({'error': 'Failed to print label'}), 400

    if fqdn and fqdn != flask.request.headers.get('Host'):
        return flask.jsonify({
            'error': 'Not allowed',
        }), 403

    data = request_to_json(flask.request)
    count = int(data.get('count', 1))
    item, variant = get_inventory_item(data)

    if not item.id or not item.item_name:
        return flask.jsonify({
            'error': 'Missing required fields',
        }), 400

    label = create_label(item, variant=variant)
    label = make_label(label)

    try:
        for i in range(count):
            brother_print(label)
    except FileNotFoundError:
        return flask.jsonify({
            'error': 'Failed to print label',
        }), 500

    return flask.jsonify({
        'status': 'ok',
    }), 200


def brother_print(im, attempt: int = 0):
    qlr = BrotherQLRaster(ql_model)
    qlr.exception_on_warning = True

    if attempt > 5:
        raise FileNotFoundError(f"Failed to print label, ${ql_printer} not found.")

    instructions = convert(
        qlr=qlr,
        images=[im],  # Takes a list of file names or PIL objects.
        label=ql_label,
        rotate=90,
        threshold=70.0,  # Black and white threshold in percent.
        dither=False,
        compress=False,
        red=False,  # Only True if using Red/Black 62 mm label tape.
        dpi_600=True,
        hq=True,  # False for low quality.
        cut=True
    )

    try:
        send(instructions=instructions, printer_identifier=ql_printer, backend_identifier=ql_backend, blocking=True)
    except FileNotFoundError:
        # Printer not found, wait a second and try again, /dev/usb/lp0 is not always ready immediately
        time.sleep(1)
        brother_print(im, attempt + 1)


app.run(host='0.0.0.0', port=5000)
