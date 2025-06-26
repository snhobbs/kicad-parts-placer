# kicad-parts-placer
**Tool for precise, batch placement of components in a KiCad PCB layout.**

+ [Blog Post](https://maskset.net/kicad-parts-placer.html)

## Features
+ Exact batch placement of components in a layout
+ Groups the components allowing them to be moved and positioned as a group, easily ensuring exact alignment
+ Useful for:
  + Creating bed of nails tester
  + Positioning mechanically important parts
  + Maintaining a form factor across different designs
+ Similar in function to this [Altium feature](https://www.altium.com/documentation/altium-designer/pcb-cmd-placecomponentsfromfileplacecomponentsfromfile-ad)

## Example Use: Pogo pin & test pad placement
An example is provided at [example/example-placement](example/example-placement).
This example starts from a centroid file generated from an existing design, which is edited to serve as the input configuration:

![Config file from centroid](documents/config_placements.png)

A schematic is drawn up with matching reference designators:

![tester schematic](documents/example-placement.svg)

The schematic is exported to a PCB which will look like this:

![Exported PCB](documents/exported_board.png)

Running the script on this board with this command exports the following board with the components exactly aligned ready for layout. The group can be treated as a footprint, placed where ever is useful. During layout you only have to deal with a single coordinate as the position within the group is locked.

```{python}
kicad-parts-placer --pcb example-placement.kicad_pcb --config centroid-all-pos.csv --out example-placement_placed.kicad_pcb --drill_center
```

![Generated PCB](documents/placed_components_board.png)

## Uses
    + Critical component placement: Exact placement of mounting holes, sensors, connectors, etc
    + Maintaining a form factor: Use the spreadsheet representation to either start a new project of a certain form factor or to ensure no parts have moved during layout
    + Reusing a bed-of-nails: Place the board outline and test pads the exact same way between versions to ensure the same jig can be used.
    
## Notes
+ Place parts in pcb layout from a configuration table.
+ Allows writing a config script which fully defines the parts
+ Connections are made either by updating from a schematic or passing a netlist
+ Use example of schematic to pcb placement
+ All parts are grouped together, locking their relative placement
+ Internal configuration is a dataframe with ref des, label/value, footprint, position x, position y. Notes fields can be added for documentation generation.
+ A separate config object can be that could pull in a board outline, stackup, etc describing the board.
+ Position, rotation, & ref des are available in the centroid file, that avoids requiring the source board be kicad.


## Installation
### PyPi
```
pip install kicad-parts-placer
```

### From Source
```
git clone https://github.com/snhobbs/kicad-parts-placer
cd kicad-parts-placer
pip install .
```

### KiCad Plugin
This tool is also available as a plugin via KiCad’s Plugin and Content Manager (PCM).

## References
+ [OpenFixture: Manual KiCad Location Export](https://tinylabs.io/openfixture-kicad-export)
+ [KiCad Schematic-to-PCB Position Plugin by Ian Ross](https://github.com/ian-ross/kicad-plugins)
