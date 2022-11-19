---
title:kicad-parts-placement Design Discussion
author:Simon Hobbs
date:11/18/2022
---
# File Formats

+ cmp file convertor: https://github.com/nmz787/kicad-bom-tool

## Importing To Schematic
+ No obvious way to import automatically
+ Add test points manually for now
+ Add symbols, use bulk edit field, copy and paste spreadsheet column directly into value


## Send To PCB
+ Choose footprints, update board from schematic


## Place Parts
+ Run script on PCB, currently command line only
+ If no x,y offset is passed in then the parts are centered on the board outline
+ All parts are grouped when added, future version could add different groups, the script could also be run multiple times if the group name is changed to be none global


## Requirements
+ Read spreadsheet to dataframe (use spreadsheet-wrangler)
+ Export filtered ref des to dataframe (pcbnew wrangling)
+ Dataframe to spreadsheet (pandas)
+ Pull parts data to dataframe, check data matches
+ Update part positions from dataframe (schematic to pcb position example)
+ Group components

