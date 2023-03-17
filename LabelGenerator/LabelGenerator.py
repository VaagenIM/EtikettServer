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
    font_id = ImageFont.truetype("JetBrainsMono-Light.ttf", size=36)
    font_name = ImageFont.truetype("Lato-Regular.ttf", size=114)
    font_small = ImageFont.truetype("Lato-Light.ttf", size=28)
    font_logo = ImageFont.truetype("Lato-Bold.ttf", size=40)

    qr = qrcode.QRCode(border=0)
    qr.add_data(content.id)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img = qr_img.resize(rect(24, 24), resample=PIL.Image.NEAREST)

    # Create the info box
    info = PIL.Image.new("RGB", rect(61, 40), color="white")
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

    logo = PIL.Image.new("RGB", rect(58, 6), color="white")
    logo_draw = PIL.ImageDraw.Draw(logo)
    logo_draw.ellipse((rect(4, 0), rect(8, 5)), fill="black", outline="black", width=15)
    logo_draw.ellipse((rect(50, 0), rect(54, 5)), fill="black", outline="black", width=15)
    logo_draw.rectangle((rect(6, 0), rect(52, 5)), fill="black", outline="black", width=15)
    logo_draw.text((to_pixels(29), to_pixels(2.6)), "Vågen Videregående Skole", font=font_logo, fill="white", align="left", anchor="mm")

    # Find the correct font size
    while info_draw.textbbox((0, 0), content.item_name, font=font_name, align="left", anchor="mm")[2] > to_pixels(28):
        font_name = font_name.font_variant(size=font_name.size - 1)
    while info_draw.textbbox((0, 0), content.id, font=font_id, align="left", anchor="mm")[2] > to_pixels(26):
        font_id = font_id.font_variant(size=font_id.size - 1)

    # Draw the text
    draw_text(content.item_name, 14, font_name, stroke_width=1)
    draw_text(content.id, 23.2, font_id)
    # draw_text('Utstyrskode:', 20.2, font_small)

    # Construct the label
    label = PIL.Image.new("RGB", label_size, color="white")

    label.paste(info, (qr_img.width + to_pixels(3), to_pixels(1)))
    label.paste(logo, (to_pixels(29), to_pixels(2)))
    label.paste(qr_img, (to_pixels(2), to_pixels(2)))

    return label.resize((901, 306), resample=PIL.Image.NEAREST)


def _barcode_label(content: InventoryItem) -> PIL.Image:
    """Create a barcode label (Code 128) for the given content."""
    options = {
        'module_height': 18,
        'module_width': .25,
        'font_size': 8,
        'text_distance': 3.1,
        'font_path': 'JetBrainsMono-Regular.ttf',
    }
    image = barcode.get('code128', content.id, writer=barcode.writer.ImageWriter())
    image = image.render(options)

    # Resize the image to fit the label, if needed
    if image.width > label_size[0]:
        image = image.resize((label_size[0] - to_pixels(1), image.height))

    # Construct the label
    label = PIL.Image.new("RGB", label_size, color="white")
    label.paste(image, (int((label_size[0] - image.width) / 2), int((label_size[1] - image.height) / 2)))

    return label.resize((901, 306), resample=PIL.Image.NEAREST)


def create_label(content: InventoryItem, variant: LabelType = LabelType.QR) -> PIL.Image:
    """Create a label for the given content and type."""
    if variant == LabelType.QR:
        return _qr_label(content)
    if variant == LabelType.BARCODE:
        return _barcode_label(content)
    raise NotImplementedError()
