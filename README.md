# kicad-parts-placer

## Uses

## Pogo pin & test pad placement
### Existing board needs a tester
1. Export test pad locations & type to a spreadsheet
2. Plugin exports pad type, position, ref des, & value from DUT
3. Extend the exported data, choosing the pogo pin footprint, mounting holes, connectors, etc. This is useful for the placement of mechanically important parts and form factor compliance. 
4. Batch load parts into schematic
5. Complete schematic as needed, batch loading can be repeated or bom exported & checked for consistency
6. Update PCB from schematic (f8)
7. Run script which moves existing ref des to the location in config
8. Put label on silkscreen, additional notes could also be added

### Placing Test Pads to Reuse a Tester
+ Can follow same workflow as making a tester or copy from the existing board that uses the tester
+ Script should have a check placement function that is read only

## Matching Form Factor
+ Ensure position, type, & rotation match a certain description. 
+ The grouped components then only need 2 dimensions locked to a reference to get correct. 

## Critical component placement
+ Exact placement of mounting holes, sensors, connectors, etc

## Notes
 
+ Place parts in pcb layout from a configuration table. 
+ Allows writing a config script which fully defines the parts
+ Connections are made either by updating from a schematic or passing a netlist
+ Use example of schematic to pcb placement
+ All parts are grouped together, locking their relative placement
+ Internal configuration is a dataframe with ref des, label/value, footprint, position x, position y. Notes fields can be added for documentation generation. 
+ A separate config object can be that could pull in a board outline, stackup, etc describing the board. 
+ Position, rotation, & ref des are available in the centroid file, that avoids requiring the source board be kicad. 


## Requirements
+ Read spreadsheet to dataframe (use spreadsheet-wrangler)
+ Export filtered ref des to dataframe (pcbnew wrangling)
+ Dataframe to spreadsheet (pandas)
+ Pull parts data to dataframe, check data matches
+ Update part positions from dataframe (schematic to pcb position example)
+ Group components


## References
+ Openscad test jig generator: https://tinylabs.io/openfixture-config/
+ Manual kicad location extraction: https://tinylabs.io/openfixture-kicad-export/
+ Hackaday test jigs: https://hackaday.com/2016/08/24/tools-of-the-trade-test-and-programming/#more-218337
+ https://www.testjigfactory.com/
+ https://climbers.net/sbc/home-lab-pcb-programming-test-jig/
+ Kicad schematic to pcb position: https://github.com/ian-ross/kicad-plugins
