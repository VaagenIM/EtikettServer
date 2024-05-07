from src.LabelGenerator import create_label, InventoryItem, LabelType

label = create_label(InventoryItem("A6500-01", "Sony A6500"))
label.save("qr.png")

label_long = create_label(InventoryItem("Manfrotto-Video-Tripod-01", "Manfrotto Videostativ"))
label_long.save("qr_long.png")

label_extra_long = create_label(InventoryItem("Aputure-Light-Kit-Fixture-Power-Supply-01", "Aputure Lampe Strømforsyning"))
label_extra_long.save("qr_extra_long.png")

label = create_label(InventoryItem("A6500-01", "Sony A6500"), variant=LabelType.BARCODE)
label.save("barcode.png")

label_long = create_label(InventoryItem("Manfrotto-Video-Tripod-01", "Manfrotto Videostativ"), variant=LabelType.BARCODE)
label_long.save("barcode_long.png")

label_extra_long = create_label(InventoryItem("Aputure-Light-Kit-Fixture-Power-Supply-01", "Aputure Lampe Strømforsyning"), variant=LabelType.BARCODE)
label_extra_long.save("barcode_extra_long.png")

label = create_label(InventoryItem("A6500-01", "Sony A6500"), variant=LabelType.TEXT)
label.save("text.png")

label = create_label(InventoryItem("A6500-01", "Sony A6500"), variant=LabelType.TEXT_2_LINES)
label.save("text2.png")