import qrcode
import PIL
import barcode
from PIL import ImageFont, Image, ImageDraw
from barcode import writer
from dataclasses import dataclass
from enum import Enum, auto

dpi = 300


def to_pixels(mm: float) -> int:
    """Convert millimeters to pixels."""
    return int(mm / 25.4 * dpi)


def rect(x: float, y: float) -> tuple:
    """Convert a rectangle from millimeters to pixels."""
    return to_pixels(x), to_pixels(y)


label_size = rect(90, 29)


@dataclass
class InventoryItem:
    id: str
    item_name: str


class LabelType(Enum):
    QR = auto()
    BARCODE = auto()


def _qr_label(content: InventoryItem) -> PIL.Image:
    """Create a QR code label for the given content."""
    font_id = ImageFont.truetype("consola.ttf", size=36)
    font_name = ImageFont.truetype("times.ttf", size=64)
    font_small = ImageFont.truetype("arial.ttf", size=24)

    qr = qrcode.QRCode(border=0)
    qr.add_data(content.id)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img = qr_img.resize(rect(27, 27), resample=PIL.Image.NEAREST)

    # Create the info box
    info = PIL.Image.new("RGB", rect(61, 27), color="white")
    info_draw = PIL.ImageDraw.Draw(info)

    def draw_text(text, y, font, stroke_width=0, fill="black"):
        # TODO: Add support for long text (wrap), though it's unlikely to be needed
        info_draw.text(
            (to_pixels(30.5), to_pixels(y)),
            text,
            font=font,
            fill=fill,
            align="left",
            anchor="mm",
            stroke_width=stroke_width,
        )

    # Add logo.png
    logo = PIL.Image.open("logo.png")
    logo = logo.resize(rect(22, 7.5), resample=PIL.Image.LANCZOS)
    info.paste(logo, (to_pixels(19.5), to_pixels(0)))

    # Add text
    draw_text(content.item_name, 13, font_name, stroke_width=1)
    draw_text('Utstyrskode:', 22, font_small)
    draw_text(content.id, 25, font_id)

    # Construct the label
    label = PIL.Image.new("RGB", label_size, color="white")
    label.paste(qr_img, (to_pixels(1), to_pixels(1)))
    label.paste(info, (qr_img.width + to_pixels(1), to_pixels(1)))

    return label


def _barcode_label(content: InventoryItem) -> PIL.Image:
    """Create a barcode label (Code 128) for the given content."""
    options = {
        'module_height': 18,
        'module_width': .25,
        'font_size': 8,
        'text_distance': 3.1,
    }
    image = barcode.get('code128', content.id, writer=barcode.writer.ImageWriter())
    image = image.render(options)

    # Resize the image to fit the label, if needed
    if image.width > label_size[0]:
        image = image.resize((label_size[0] - to_pixels(1), image.height))

    # Construct the label
    label = PIL.Image.new("RGB", label_size, color="white")
    label.paste(image, (int((label_size[0] - image.width) / 2), int((label_size[1] - image.height) / 2 + to_pixels(1.5))))

    return label


def create_label(content: InventoryItem, variant: LabelType = LabelType.QR) -> PIL.Image:
    """Create a label for the given content and type."""
    print(f"Creating label for {content.id} ({variant})")
    if variant == LabelType.QR:
        return _qr_label(content)
    if variant == LabelType.BARCODE:
        return _barcode_label(content)
    raise NotImplementedError()
