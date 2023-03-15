<div align="center">
<h1>EtikettServer for Vågen Utstyrsbase</h1>
Simple barcode and QR code label generator for the Vågen Utstyrsbase. Adds an API endpoint to preview and print labels with Brother labelprinters.
<br>
<img src="barcode.png" width="300" alt="Barcode label preview">
<img src="qr.png" width="300" alt="QR label preview">

Label dimensions: `29x90mm`

</div>

## Installation
1. Clone the repository
2. Run `pip install -r requirements.txt`

## Usage
Run with `python api.py` and go to `http://localhost:5000/` in your browser. You can also use the API directly.

## Endpoints
The following parameters is used by every endpoint:
```python
id = "6500-01"
name = "Sony A6500"
variant = "qr"  # "qr" or "barcode", default: "qr"
```

### GET `/preview`
Returns a preview of the label in the browser, with a button to print it.

### POST `/preview`
Same as above, but only returns the image data. Useful for embedding in other applications.

### POST `/print`
Prints the label to the connected printer. (Requires setup of printer in `api.py`)

## TODO
`api.py` add connection to brother printers