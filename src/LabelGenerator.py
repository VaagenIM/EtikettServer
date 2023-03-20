import qrcode
import PIL
import barcode
from PIL import ImageFont, Image, ImageDraw
from barcode import writer
from dataclasses import dataclass
from enum import Enum, auto

lx = int(1132 * .99)
ly = int(330 * .85)
padding = 20


@dataclass
class InventoryItem:
    id: str
    item_name: str


class LabelType(Enum):
    QR = auto()
    BARCODE = auto()


def _logo() -> PIL.Image:
    font_logo = ImageFont.truetype("Lato-Bold.ttf", size=int(ly/7))

    info_size = (lx - ly, ly)
    logo_start = 150
    logo_end = info_size[0] - 150
    logo_height = int(ly / 3.61)

    # Create the logo (black pill, white text)
    logo = PIL.Image.new("RGBA", (logo_end, logo_height - 10), color="white")
    logo_draw = PIL.ImageDraw.Draw(logo)
    logo_draw.ellipse((logo_start, 14, logo_start + 35, logo_height - 12), fill="black", outline="black", width=15)
    logo_draw.ellipse((logo_end - 35, 14, logo_end, logo_height - 12), fill="black", outline="black", width=15)
    logo_draw.rectangle((logo_start + 20, 14, logo_end - 20, logo_height - 12), fill="black", outline="black", width=15)
    logo_draw.text(((logo_end + 150) / 2, logo_height / 2), "Vågen Videregående Skole", font=font_logo, fill="white", align="left", anchor="mm")

    return logo


def _qr_label(content: InventoryItem) -> PIL.Image:
    """Create a QR code label for the given content."""
    font_id = ImageFont.truetype("JetBrainsMono-Light.ttf", size=int(ly/8.38))
    font_name = ImageFont.truetype("Lato-Regular.ttf", size=int(ly/2.28))

    qr_size = (ly, ly)
    info_size = (lx - ly, ly)

    # Create the QR code
    qr = qrcode.QRCode(border=0)
    qr.add_data(content.id)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img = qr_img.resize(qr_size, resample=PIL.Image.NEAREST)

    logo = _logo()

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
    while (info_draw.textbbox((0, 0), content.item_name, font=font_name, align="left", anchor="mm")[2] * 2) > lx - qr_size[0] - padding:
        font_name = font_name.font_variant(size=font_name.size - 1)
    while (info_draw.textbbox((0, 0), content.id, font=font_id, align="left", anchor="mm")[2] * 2) > lx - qr_size[0] - (padding * 2):
        font_id = font_id.font_variant(size=font_id.size - 1)

    # Draw the text
    draw_text(content.item_name, ly / 4 - 3, font_name, stroke_width=1)
    draw_text(content.id, ly / 2 + 35, font_id)

    # Construct the label
    label = PIL.Image.new("RGB", (lx, ly), color="white")
    label.paste(info, (qr_size[0], int(ly / 3.61)))
    label.paste(logo, (qr_size[0], 0))
    label.paste(qr_img, (0, 0))

    return label


def _barcode_label(content: InventoryItem) -> PIL.Image:
    """Create a barcode label (Code 128) for the given content."""
    options = {
        'module_height': ly/21,
        'module_width': ly/742.857,
        'font_size': 0,
    }
    image = barcode.get('code128', content.id, writer=barcode.writer.ImageWriter())
    image = image.render(options)

    # Resize the image to fit the label, if needed
    if image.width > lx:
        image = image.resize((lx - padding, image.height))

    logo = _logo()
    logo = logo.resize((int(logo.width / 1.5), int(logo.height / 1.5)))

    # Construct the label
    label = PIL.Image.new("RGBA", (lx, ly), color="white")
    # Add the logo to the top
    # Add the barcode in the center
    label.paste(image, (int((lx - image.width) / 2), int((ly - image.height) / 2) - 3))
    label.paste(logo, (int((lx - logo.width - 100) / 2), 2))
    # Add the text below the barcode
    font_id = ImageFont.truetype("JetBrainsMono-Light.ttf", size=int(ly/6.5))

    id_draw = PIL.ImageDraw.Draw(label)
    while (id_draw.textbbox((0, 0), content.id, font=font_id, align="left", anchor="mm")[2] * 2) > lx - padding:
        font_id = font_id.font_variant(size=font_id.size - 1)
    id_draw.text(
        (lx / 2, ly - 38),
        content.id,
        font=font_id,
        fill="black",
        align="center",
        anchor="mm",
        stroke_width=0,
    )

    return label


def create_label(content: InventoryItem, variant: LabelType = LabelType.QR) -> PIL.Image:
    """Create a label for the given content and type."""
    if variant == LabelType.QR:
        return _qr_label(content)
    if variant == LabelType.BARCODE:
        return _barcode_label(content)
    raise NotImplementedError()
