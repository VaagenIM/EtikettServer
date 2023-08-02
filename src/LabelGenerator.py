import qrcode
import PIL
import barcode
from PIL import ImageFont, Image, ImageDraw
from barcode import writer
from dataclasses import dataclass
from enum import Enum, auto

lx = int(1132 * .99)
ly = int(330 * .90)
padding = 20


@dataclass
class InventoryItem:
    id: str
    item_name: str


class LabelType(Enum):
    QR = auto()
    BARCODE = auto()
    TEXT = auto()
    TEXT_2_LINES = auto()


def _qr_label(content: InventoryItem) -> PIL.Image:
    """Create a QR code label for the given content."""
    font_id = ImageFont.truetype("JetBrainsMono-Light.ttf", size=int(ly/8.38))
    font_name = ImageFont.truetype("Lato-Regular.ttf", size=int(ly/2.28))
    font_logo = ImageFont.truetype("Lato-Bold.ttf", size=int(ly/6.5))

    qr_size = (ly, ly)
    info_size = (lx - ly, ly)

    # Create the QR code
    qr = qrcode.QRCode(border=0)
    qr.add_data(content.id)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img = qr_img.resize(qr_size, resample=PIL.Image.NEAREST)

    # Create the info box
    info = PIL.Image.new("RGB", info_size, color="white")
    info_draw = PIL.ImageDraw.Draw(info)

    def draw_text(text, y, font, stroke_width=0, fill="black"):
        info_draw.text(
            (info_size[0]/2, y),
            text,
            font=font,
            fill=fill,
            align="left",
            anchor="mm",
            stroke_width=stroke_width,
        )

    logo_start = 40
    logo_end = info_size[0] - 40
    logo_height = int(ly / 3.61)

    # Create the logo (black pill, white text)
    logo = PIL.Image.new("RGB", (logo_end, logo_height), color="white")
    logo_draw = PIL.ImageDraw.Draw(logo)
    logo_draw.ellipse((logo_start, 2, logo_start + 35, logo_height), fill="black", outline="black", width=15)
    logo_draw.ellipse((logo_end - 35, 2, logo_end, logo_height), fill="black", outline="black", width=15)
    logo_draw.rectangle((logo_start + 22, 2, logo_end - 22, logo_height), fill="black", outline="black", width=15)
    logo_draw.text(((logo_end + 17.5) / 2, logo_height / 2), "Vågen Videregående Skole", font=font_logo, fill="white", align="left", anchor="mm")

    # Find the correct font size
    while (info_draw.textbbox((0, 0), content.item_name, font=font_name, align="left", anchor="mm")[2] * 2) > lx - qr_size[0] - padding:
        font_name = font_name.font_variant(size=font_name.size - 1)
    while (info_draw.textbbox((0, 0), content.id, font=font_id, align="left", anchor="mm")[2] * 2) > lx - qr_size[0] - (padding * 2):
        font_id = font_id.font_variant(size=font_id.size - 1)

    # Draw the text
    draw_text(content.item_name, ly / 4 + 5, font_name, stroke_width=1)
    draw_text(content.id, ly / 2 + 35, font_id)

    # Construct the label
    label = PIL.Image.new("RGB", (lx, ly), color="white")
    label.paste(info, (qr_size[0], logo_height))
    label.paste(logo, (qr_size[0], 0))
    label.paste(qr_img, (0, 0))

    return label


def _barcode_label(content: InventoryItem) -> PIL.Image:
    """Create a barcode label (Code 128) for the given content."""
    options = {
        'module_height': ly/16.25,
        'module_width': ly/742.857,
        'font_size': 0,
    }
    image = barcode.get('code128', content.id, writer=barcode.writer.ImageWriter())
    image = image.render(options)

    # Resize the image to fit the label, if needed
    if image.width > lx:
        image = image.resize((lx - padding, image.height))

    # Construct the label
    label = PIL.Image.new("RGB", (lx, ly), color="white")
    # Add the barcode in the center
    label.paste(image, (int((lx - image.width) / 2), int((ly - image.height) / 2) - 17))
    # Add the text below the barcode
    font_id = ImageFont.truetype("JetBrainsMono-Light.ttf", size=int(ly/7.647))

    id_draw = PIL.ImageDraw.Draw(label)
    while (id_draw.textbbox((0, 0), content.id, font=font_id, align="left", anchor="mm")[2] * 2) > lx - padding:
        font_id = font_id.font_variant(size=font_id.size - 1)
    id_draw.text(
        (lx / 2, ly - 32),
        content.id,
        font=font_id,
        fill="black",
        align="left",
        anchor="mm",
        stroke_width=0,
    )

    return label


def _text_label(content: InventoryItem) -> PIL.Image:
    """Create a text label for the given content."""
    font_name = ImageFont.truetype("Lato-Regular.ttf", size=int(ly/1.25))

    info_size = (lx, ly)

    # Create the info box
    info = PIL.Image.new("RGB", info_size, color="white")
    info_draw = PIL.ImageDraw.Draw(info)

    def draw_text(text, y, font, stroke_width=0, fill="black"):
        info_draw.text(
            (info_size[0]/2, y),
            text,
            font=font,
            fill=fill,
            align="left",
            anchor="mm",
            stroke_width=stroke_width,
        )

    # Find the correct font size
    while (info_draw.textbbox((0, 0), content.item_name, font=font_name, align="left", anchor="mm")[2] * 2) > lx - (padding * 2):
        font_name = font_name.font_variant(size=font_name.size - 1)

    # Draw the text
    draw_text(content.item_name, ly / 2, font_name)

    # Construct the label
    label = PIL.Image.new("RGB", (lx, ly), color="white")
    label.paste(info, (0, 0))

    return label


def _text_label_2_lines(content: InventoryItem) -> PIL.Image:
    """Create a text label for the given content."""
    font_name = ImageFont.truetype("Lato-Regular.ttf", size=int(ly/2.5))
    font_id = ImageFont.truetype("Lato-Regular.ttf", size=int(ly/2.5))

    info_size = (lx, ly)

    # Create the info box
    info = PIL.Image.new("RGB", info_size, color="white")
    info_draw = PIL.ImageDraw.Draw(info)

    def draw_text(text, y, font, stroke_width=0, fill="black"):
        info_draw.text(
            (info_size[0]/2, y),
            text,
            font=font,
            fill=fill,
            align="left",
            anchor="mm",
            stroke_width=stroke_width,
        )

    # Find the correct font size
    while (info_draw.textbbox((0, 0), content.item_name, font=font_name, align="left", anchor="mm")[2] * 2) > lx - (padding * 2):
        font_name = font_name.font_variant(size=font_name.size - 1)

    while (info_draw.textbbox((0, 0), content.id, font=font_id, align="left", anchor="mm")[2] * 2) > lx - (padding * 2):
        font_id = font_id.font_variant(size=font_id.size - 1)


    # Draw the text
    draw_text(content.item_name, ly / 1.5, font_name)
    draw_text(content.id, ly / 4, font_id)

    # Construct the label
    label = PIL.Image.new("RGB", (lx, ly), color="white")
    label.paste(info, (0, 0))

    return label


def create_label(content: InventoryItem, variant: LabelType = LabelType.QR) -> PIL.Image:
    """Create a label for the given content and type."""
    if variant == LabelType.QR:
        return _qr_label(content)
    if variant == LabelType.BARCODE:
        return _barcode_label(content)
    if variant == LabelType.TEXT:
        return _text_label(content)
    if variant == LabelType.TEXT_2_LINES:
        return _text_label_2_lines(content)
    raise NotImplementedError()