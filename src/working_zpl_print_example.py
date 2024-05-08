from zebra import Zebra
import zpl
import LabelGenerator

z = Zebra()
z.setqueue(z.getqueues()[0])
l = zpl.Label(50,50)
l.origin(9.5,0)
l.write_graphic(LabelGenerator.create_label(LabelGenerator.InventoryItem("A6500-01", "Sony A6500")), 32)
l.endorigin()
z.output(l.dumpZPL())