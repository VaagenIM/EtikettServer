from dataclasses import dataclass
import qrcode
import PIL
from PIL import ImageFont, Image, ImageDraw


def to_pixels(mm, dpi=300):
    return int(mm / 25.4 * dpi)


def rect(x, y):
    return to_pixels(x), to_pixels(y)


@dataclass
class InventoryItem:
    id: str
    item_name: str
    item_category: str


font_id = ImageFont.truetype("consola.ttf", size=24)
font_name = ImageFont.truetype("arial.ttf", size=64)
font_category = ImageFont.truetype("arial.ttf", size=36)

label_size = rect(90, 29)
qr_size = rect(24, 24)
qr_id_size = rect(19, 6)
info_size = rect(60, 29)
padding = to_pixels(2)


def create_label(content: InventoryItem) -> PIL.Image:
    content.item_category = f"Lagerplass: {content.item_category}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=0,
    )
    qr.add_data(content.id)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img = qr_img.resize(qr_size, resample=PIL.Image.NEAREST)

    qr_id = PIL.Image.new("RGB", qr_id_size, color="white")
    qr_id_draw = PIL.ImageDraw.Draw(qr_id)
    qr_id_draw.text(
        (int(qr_img.width / 2), to_pixels(1)),
        content.id,
        font=font_id,
        fill="black",
        anchor="mm",
        align="center",
    )

    info = PIL.Image.new("RGB", info_size, color="white")
    info_draw = PIL.ImageDraw.Draw(info)
    info_draw.text(
        (to_pixels(1), to_pixels(1)),
        content.item_name,
        font=font_name,
        fill="black",
        stroke_width=1,
    )

    info_draw.text(
        (to_pixels(1), to_pixels(7)),
        content.item_category,
        font=font_category,
        fill="black",
    )

    logo = PIL.Image.open("logo.png")
    logo = logo.resize((to_pixels(42), to_pixels(14)), resample=PIL.Image.LANCZOS)
    info.paste(logo, (to_pixels(17), to_pixels(13)))

    # Create the label
    label = PIL.Image.new("RGB", label_size, color="white")
    label.paste(qr_img, (to_pixels(1), to_pixels(1)))
    label.paste(qr_id, (to_pixels(1), to_pixels(26)))
    label.paste(info, (qr_img.width + to_pixels(1), to_pixels(1)))

    return label
