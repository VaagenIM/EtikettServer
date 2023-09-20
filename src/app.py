import io
import os
import time
import atexit
import signal
from functools import wraps
from threading import Thread

import PIL.Image
import flask
import usb.core
from brother_ql.backends.helpers import send
from brother_ql.conversion import convert
from brother_ql.raster import BrotherQLRaster
from dotenv import load_dotenv
from flask_cors import CORS

from LabelGenerator import create_label, InventoryItem, LabelType

load_dotenv()

# Only supports 17x54 labels (for now) (1132x330 px)
# TODO: Support more label sizes
LABEL_SIZE = (1132, 330)
QL_LABEL = "17x54"

FQDN = os.getenv('FQDN', None)
QL_PRINTER = os.getenv('QL_PRINTER', 'usb://0x04f9:0x209c')
QL_MODEL = os.getenv('QL_MODEL', 'QL-810W')
QL_BACKEND = 'pyusb'
ID_VENDOR = int(QL_PRINTER.split('usb://')[1].split(':')[0], 16)
ID_PRODUCT = int(QL_PRINTER.split(':')[2], 16)

# The label needs to be offset to the right and down a bit, to center it on the label (in pixels)
# This might be different depending on the printer model, not sure
X_OFFSET = int(os.getenv('X_OFFSET', 15))
Y_OFFSET = int(os.getenv('Y_OFFSET', -4))


class PrintQueue(list):
    def __init__(self):
        super().__init__()
        self.running = False

    def print_worker(self):
        fails = 0
        while self:
            try:
                label = self[0]
                brother_print(label)
                self.pop(0)
                fails = 0
                print('printed label')
            except usb.core.USBError:
                print('USB error, assuming print job was successful')
                # (The printer connection is handled by the request,
                # so if the request is successful, the printer is connected,
                # and this is likely a false positive)
                self.pop(0)
            except Exception as e:
                print('error', e, '(retrying in 60 seconds)')
                fails += 1
                time.sleep(5)  # wait 5 seconds before retrying
            if fails > 10:
                print('too many fails in a row, clearing queue')
                self.clear()
                fails = 0
        print('queue empty')
        self.running = False

    def append(self, item):
        super().append(item)
        print('added label to queue')
        if not self.running:
            self.running = True
            Thread(target=self.print_worker).start()

queue = PrintQueue()
app = flask.Flask(__name__)
CORS(app)


def offset_label(img: PIL.Image) -> PIL.Image:
    """Create a new label with the given label image to center it on the label."""
    new_label = PIL.Image.new("RGB", LABEL_SIZE, color="white")
    new_label.paste(img, (X_OFFSET, Y_OFFSET))
    return new_label


def get_variant(variant: str) -> LabelType:
    """Get the label type from the given variant."""
    default = LabelType.QR
    return {
        'qr': LabelType.QR,
        'barcode': LabelType.BARCODE,
        'text': LabelType.TEXT,
        'text_2_lines': LabelType.TEXT_2_LINES,
    }.get(variant.lower(), default)


def use_fqdn_if_set(f) -> callable:
    @wraps(f)
    def decorated_function(*args, **kwargs) -> callable:
        """
        Redirect to the FQDN if it's set and the request is not using it.
        This is to prevent the user from accessing the API from an IP address.
        (Letting us configure a proxy and limit access to the API to only the FQDN with an access control list)
        """
        if FQDN and FQDN != flask.request.headers.get('Host'):
            return flask.redirect(f'//{FQDN}', code=301)
        return f(*args, **kwargs)

    return decorated_function


def validate_input(value: str) -> str:
    """Validate the given input."""
    value = value.strip()
    return value if value else '<Mangler>'


def label_from_request(data: dict) -> PIL.Image:
    """Parse the request data."""
    item_id = validate_input(data.get('id', ''))
    item_name = validate_input(data.get('name', ''))
    variant = get_variant(validate_input(data.get('variant', 'qr')))

    item = InventoryItem(id=item_id, item_name=item_name)
    return create_label(item, variant=variant)


@app.route('/', methods=['GET'])
@use_fqdn_if_set
def index() -> str:
    return flask.render_template('index.html')


@app.route('/preview', methods=['GET'])
@use_fqdn_if_set
def preview():
    """Preview the label with the given data."""
    label = label_from_request(flask.request.args)

    img_bytes = io.BytesIO()
    label.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    return flask.send_file(img_bytes, mimetype='image/png')


@app.route('/print', methods=['POST'])
@use_fqdn_if_set
def print_label():
    """Print the label with the given data."""
    # Check if the printer is connected
    try:
        dev = usb.core.find(idVendor=ID_VENDOR, idProduct=ID_PRODUCT)
        dev.reset()  # (Might not be needed)
    # If this fails, it's probably because the printer is not connected, so just ignore it for now
    # TODO: Proper error handling
    except Exception:
        return flask.jsonify({'error': 'Failed to print label'}), 500

    content_type = flask.request.headers.get('Content-Type')
    if content_type == 'application/json':
        data = flask.request.json
    else:
        data = flask.request.args

    label = offset_label(label_from_request(data))
    try:
        count = int(data.get('count', 1))
    except ValueError:
        count = 1
    if count < 1 or count >= 10:
        flask.jsonify({'error': 'Count must be between 1 and 10'}), 400

    [queue.append(label) for _ in range(count)]

    return flask.jsonify({
        'success': True,
    }), 200


def brother_print(im):
    qlr = BrotherQLRaster(QL_MODEL)
    qlr.exception_on_warning = True

    instructions = convert(
        qlr=qlr,
        images=[im],
        label=QL_LABEL,
        rotate=90,
        threshold=70.0,
        dither=False,
        compress=False,
        red=False,
        dpi_600=True,
        hq=True,
        cut=True
    )

    send(instructions=instructions, printer_identifier=QL_PRINTER, backend_identifier=QL_BACKEND, blocking=True)

def on_exit(signum=None, frame=None):
    queue.running = False
    raise SystemExit


atexit.register(on_exit)
signal.signal(signal.SIGTERM, on_exit)
signal.signal(signal.SIGINT, on_exit)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
