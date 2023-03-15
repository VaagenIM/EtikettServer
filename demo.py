from LabelGenerator import create_label, InventoryItem

label = create_label(InventoryItem("A6500-01", "Sony A6500", "Kamera"))

label.save("label.png")
