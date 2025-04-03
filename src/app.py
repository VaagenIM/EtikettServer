import PIL.Image
import atexit
import flask
import io
import os
import signal
import zpl
from dotenv import load_dotenv
from flask_cors import CORS
from functools import wraps
from threading import Thread
from zebra import Zebra

from LabelGenerator import create_label, InventoryItem, LabelType

load_dotenv()

FQDN = os.getenv("FQDN", None)


class PrintQueue(list):
    def __init__(self):
        super().__init__()
        self.running = False

    def print_worker(self):
        fails = 0
        while self:
            label = self[0]
            zebra_print(label)
            self.pop(0)
        print("queue empty")
        self.running = False

    def append(self, item):
        super().append(item)
        print("added label to queue")
        if not self.running:
            self.running = True
            Thread(target=self.print_worker).start()


queue = PrintQueue()
app = flask.Flask(__name__)
CORS(app)


def get_variant(variant: str) -> LabelType:
    """Get the label type from the given variant."""
    default = LabelType.QR
    return {
        "qr": LabelType.QR,
        "barcode": LabelType.BARCODE,
        "text": LabelType.TEXT,
        "text_2_lines": LabelType.TEXT_2_LINES,
    }.get(variant.lower(), default)


def use_fqdn_if_set(f) -> callable:
    @wraps(f)
    def decorated_function(*args, **kwargs) -> callable:
        """
        Redirect to the FQDN if it's set and the request is not using it.
        This is to prevent the user from accessing the API from an IP address.
        (Letting us configure a proxy and limit access to the API to only the FQDN with an access control list)
        """
        if FQDN and FQDN != flask.request.headers.get("Host"):
            return flask.redirect(f"//{FQDN}", code=301)
        return f(*args, **kwargs)

    return decorated_function


def validate_input(value: str) -> str:
    """Validate the given input."""
    value = value.strip()
    return value if value else "<Mangler>"


def label_from_request(data: dict) -> PIL.Image:
    """Parse the request data."""
    item_id = validate_input(data.get("id", ""))
    item_name = validate_input(data.get("name", ""))
    variant = get_variant(validate_input(data.get("variant", "qr")))

    item = InventoryItem(id=item_id, item_name=item_name)
    return create_label(item, variant=variant)


@app.route("/", methods=["GET"])
@use_fqdn_if_set
def index() -> str:
    return flask.render_template("index.html")


@app.route("/preview", methods=["GET"])
@use_fqdn_if_set
def preview():
    """Preview the label with the given data."""
    label = label_from_request(flask.request.args)

    img_bytes = io.BytesIO()
    label.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    return flask.send_file(img_bytes, mimetype="image/png")


@app.route("/print", methods=["POST"])
@use_fqdn_if_set
def print_label():
    """Print the label with the given data."""
    content_type = flask.request.headers.get("Content-Type")
    if content_type == "application/json":
        data = flask.request.json
    else:
        data = flask.request.args

    label = label_from_request(data)
    try:
        count = int(data.get("count", 1))
    except ValueError:
        count = 1
    if count < 1 or count >= 10:
        flask.jsonify({"error": "Count must be between 1 and 10"}), 400

    [queue.append(label) for _ in range(count)]

    return flask.jsonify(
        {
            "success": True,
        }
    ), 200


def zebra_print(im):
    z = Zebra()
    z.setqueue(z.getqueues()[0])
    l = zpl.Label(50, 50)
    l.origin(9.5, 0)
    l.write_graphic(im, 32)
    l.endorigin()
    z.output(l.dumpZPL())


def on_exit(signum=None, frame=None):
    queue.running = False
    raise SystemExit


atexit.register(on_exit)
signal.signal(signal.SIGTERM, on_exit)
signal.signal(signal.SIGINT, on_exit)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
