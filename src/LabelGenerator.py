from dataclasses import dataclass
from enum import Enum, auto

import PIL
import barcode
import qrcode
from PIL import ImageFont, Image, ImageDraw
from barcode import writer

# Get current python file path
from pathlib import Path
import os
fonts_dir = Path(f'{Path(os.path.realpath(__file__)).parent}/fonts')

output_label_dimensions = (int(((50/25.4) * 203)), int(((26/25.4) * 203)))
lx, ly = output_label_dimensions

@dataclass
class InventoryItem:
    id: str
    item_name: str


class LabelType(Enum):
    QR = auto()
    BARCODE = auto()
    TEXT = auto()
    TEXT_2_LINES = auto()


FONT_MONO = f'{fonts_dir}/RobotoMono-Medium.ttf'
FONT_NAME = f'{fonts_dir}/Lato-Regular.ttf'
FONT_LOGO = f'{fonts_dir}/Lato-Bold.ttf'

def _qr_label(content: InventoryItem) -> PIL.Image:
    """Create a QR code label for the given content."""
    font_id = ImageFont.truetype(FONT_MONO, size=int(ly / 5.5))
    font_name = ImageFont.truetype(FONT_NAME, size=int(ly / 2))
    font_logo = ImageFont.truetype(FONT_LOGO, size=int(ly / 6.8))

    qr_size = (int(ly*0.5), int(ly*0.5))
    info_size = (int(lx) - int(ly*0.55), int(ly*0.5))

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
            (info_size[0] / 2, y),
            text,
            font=font,
            fill=fill,
            align="left",
            anchor="mm",
            stroke_width=stroke_width,
        )

    logo_start = 10
    logo_end = lx - 10
    logo_height = int(ly / 4)

    # Create the logo (black pill, white text)
    logo = PIL.Image.new("RGB", (logo_end, logo_height), color="white")
    logo_draw = PIL.ImageDraw.Draw(logo)
    logo_draw.rounded_rectangle((logo_start, 2, logo_end, logo_height), fill="black", outline="black", width=15, radius=25)
    logo_draw.text(((logo_end + 9) / 2, logo_height / 2), "Vågen Videregående Skole", font=font_logo, fill="white",
                   align="left", anchor="mm")

    # Find the correct font size
    while (info_draw.textbbox((0, 0), content.item_name, font=font_name, align="left", anchor="mm")[2] * 2) > lx - \
            qr_size[0] - 9:
        font_name = font_name.font_variant(size=font_name.size - 1)
    while (info_draw.textbbox((0, 0), content.id, font=font_id, align="left", anchor="mm")[2] * 2) > lx - qr_size[0] - 9:
        font_id = font_id.font_variant(size=font_id.size - 1)

    # Draw the text
    draw_text(content.item_name, ly / 5 - 5, font_name, stroke_width=1)
    draw_text(content.id, ly / 2 - 15, font_id)

    # Construct the label
    label = PIL.Image.new("RGB", (lx, ly), color="white")
    label.paste(info, (int(qr_size[0] + ly*0.025), ly - qr_size[1] - 30))
    label.paste(logo, (0, 15))
    label.paste(qr_img, (0, ly - qr_size[1] - 20))

    return label


def _barcode_label(content: InventoryItem) -> PIL.Image:
    """Create a barcode label (Code 128) for the given content."""
    options = {
        'module_height': ly / 25,
        'module_width': ly / 742.857,
        'font_path': FONT_NAME,
        'text_distance': 4,
    }
    image = barcode.get('code128', content.id, writer=barcode.writer.ImageWriter()).render(options)

    font_logo = ImageFont.truetype(FONT_LOGO, size=int(ly / 6.8))

    # Resize the image to fit the label, if needed
    if image.width > lx:
        image = image.resize((lx, image.height))

    logo_start = 10
    logo_end = lx - 10
    logo_height = int(ly / 3.61)

    # Create the logo (black pill, white text)
    logo = PIL.Image.new("RGB", (logo_end, logo_height), color="white")
    logo_draw = PIL.ImageDraw.Draw(logo)
    logo_draw.rounded_rectangle((logo_start, 2, logo_end, logo_height), fill="black", outline="black", width=15, radius=25)
    logo_draw.text(((logo_end + 9) / 2, logo_height / 2), "Vågen Videregående Skole", font=font_logo, fill="white",
                   align="left", anchor="mm")

    # Construct the label
    label = PIL.Image.new("RGB", (lx, ly), color="white")
    label.paste(image, (int((lx - image.width) / 2), int((ly - image.height) / 2) + 35))
    label.paste(PIL.Image.new("RGB", (lx, logo.height + 15), color="white"), (0, 0))
    label.paste(logo, (0, 5))

    return label


def _text_label(content: InventoryItem) -> PIL.Image:
    """Create a text label for the given content."""
    font_name = ImageFont.truetype(FONT_NAME, size=int(ly / 1.25))

    info_size = (lx, ly)

    # Create the info box
    info = PIL.Image.new("RGB", info_size, color="white")
    info_draw = PIL.ImageDraw.Draw(info)

    def draw_text(text, y, font, stroke_width=0, fill="black"):
        info_draw.text(
            (info_size[0] / 2, y),
            text,
            font=font,
            fill=fill,
            align="left",
            anchor="mm",
            stroke_width=stroke_width,
        )

    # Find the correct font size
    while (info_draw.textbbox((0, 0), content.item_name, font=font_name, align="left", anchor="mm")[2] * 2) > lx:
        font_name = font_name.font_variant(size=font_name.size - 1)

    # Draw the text
    draw_text(content.item_name, ly / 2, font_name)

    # Construct the label
    label = PIL.Image.new("RGB", (lx, ly), color="white")
    label.paste(info, (0, 0))

    return label


def _text_label_2_lines(content: InventoryItem) -> PIL.Image:
    """Create a text label for the given content."""
    
    font_name = ImageFont.truetype(FONT_NAME, size=int(ly / 2.5))
    font_id = ImageFont.truetype(FONT_NAME, size=int(ly / 2.5))

    info_size = (lx, ly)

    # Create the info box
    info = PIL.Image.new("RGB", info_size, color="white")
    info_draw = PIL.ImageDraw.Draw(info)

    def draw_text(text, y, font, stroke_width=0, fill="black"):
        info_draw.text(
            (info_size[0] / 2, y),
            text,
            font=font,
            fill=fill,
            align="left",
            anchor="mm",
            stroke_width=stroke_width,
        )

    # Find the correct font size
    while (info_draw.textbbox((0, 0), content.item_name, font=font_name, align="left", anchor="mm")[2] * 2) > lx:
        font_name = font_name.font_variant(size=font_name.size - 1)

    while (info_draw.textbbox((0, 0), content.id, font=font_id, align="left", anchor="mm")[2] * 2) > lx:
        font_id = font_id.font_variant(size=font_id.size - 1)

    # Draw the text
    draw_text(content.item_name, ly / 1.5, font_name)
    draw_text(content.id, ly / 4, font_id)

    # Construct the label
    label = PIL.Image.new("RGB", (lx, ly), color="white")
    label.paste(info, (0, 0))

    return label


def paste_on_label(label: PIL.Image) -> PIL.Image:
    """Paste the given label on a new label."""
    new_label = PIL.Image.new("RGB", output_label_dimensions, color="white")

    label.thumbnail((output_label_dimensions[0], output_label_dimensions[1]))
    new_label.paste(label, (int((output_label_dimensions[0] - label.width) / 2), int((output_label_dimensions[1] - label.height) / 2)))

    return new_label


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
