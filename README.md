<div align="center">
<h1>Etikett Server for Vågen Utstyrsbase</h1>
Simple barcode and QR code label generator for the Vågen Utstyrsbase. (with API endpoints)
<br>

Label dimensions: `29x90mm`

<img src="demo/barcode_long.png" width="300" alt="Barcode label preview">
<img src="demo/qr_long.png" width="300" alt="QR label preview">


</div>

## Installation
1. Clone the repository
2. Run `pip install -r requirements.txt`

## Usage
Run with `python api.py` and go to `http://localhost:5000/` in your browser. You can also use the API directly.

## Endpoints
The following parameters is used by every endpoint:
```python
id = "A6500-01"
name = "Sony A6500"
variant = "qr"  # "qr" or "barcode", default: "qr"
```

### GET `/preview`
Returns a preview of the label in the browser, with a button to print it.

### GET `/preview_raw`
Same as above, but only returns the image. Useful for embedding in other applications.

### POST `/print`
Prints the label to the connected printer. (Requires setup of printer in `api.py`)

Adds the `count` parameter, which specifies how many labels to print. Default: `1`
```python
count = 2  # Print 2 labels, default: 1
```

## TODO
`api.py` add connection to brother printers
