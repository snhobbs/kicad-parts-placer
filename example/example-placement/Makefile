CENTROID=centroid-all-pos.csv
PCBIN=example-placement.kicad_pcb
PCBOUT=example-placement_placed.kicad_pcb
COMMAND=kicad_parts_placer

all: place view

view:
	pcbnew $(PCBOUT)

place:
	$(COMMAND) --pcb $(PCBIN) --config $(CENTROID) --out $(PCBOUT) --debug -x 117.5 -y 53
