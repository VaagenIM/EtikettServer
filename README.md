<div align="center">
<h1>Etikett Server for Vågen Utstyrsbase</h1>
Simple & hacky barcode and QR code label generator API for the Vågen Utstyrsbase.
<br>

Label dimensions: `16x54mm` (Could update this to work for other sizes as well, but for now it's hardcoded with
spaghetti code.)

<img src="demo/qr_long.png" style="" width="300" alt="QR label preview">
<img src="demo/barcode_long.png" style="border-radius: 5px; border: 10px solid white; background-color: white;" width="300" alt="Barcode label preview">

</div>

## Installation

1. Clone the repository
2. Run `pip install -r requirements.txt`
3. Download fonts from the links below, you might have to put them in the `src` folder
4. Configure `app.py` according to the [brother-ql](https://pypi.org/project/brother-ql/) package (or use `.env`)

Fonts:

- https://fonts.google.com/specimen/Lato
- https://fonts.google.com/specimen/JetBrains+Mono

## Usage

Run with `python app.py` and go to `http://ip-address:5000/` in your browser to design and print labels. You can also
integrate in your own application by using the API endpoints.

## Endpoints

### GET `/preview?id={id}&name={name}&variant={variant}&category={category}`

```python
id = "A6500-01"
name = "Sony A6500"
variant = "qr"  # "qr" or "barcode", default: "qr"
category = "Camera"  # Optional, used for audits
```

Returns a preview of the label, useful for getting a preview of the label before printing.

### POST `/print` (JSON)

```json
{
  "id": "A6500-01",
  "name": "Sony A6500",
  "variant": "qr",
  "category": "Camera",
  "count": 1
}
```

Prints the label to the connected printer. (Requires setup of printer in `app.py`)
