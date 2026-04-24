# W. M. KECK Observatory Slitmask Design Tool

This software is still in active development but released for both LRIS and DEIMOS.  Please report any bugs and any feedback is also welcome.

### Installation
Several python modules may need to be installed including flask, astropy, numpy, etc.

Launch using `python app.py --lris` or `python app.py --deimos`

### Instructions
- Select catalog file with [dsimulator format](https://www2.keck.hawaii.edu/inst/deimos/smdt.html) and click load targets.  
- Set parameters like field center and mask PA.
- Click update parameters to save parameters.
- Press the Auto-select button to populate the target table and display targets
- Select targets manually by clicking on a target/table row and updating select from 0 to 1 or vice versa.
- Click the Generate Slits button to visualize slits.
- Click save mask design file to save the file.
- Upload the generated .fits file to the slitmask database.

### Other items
- Auto-select, generate slits, and the save mask buttons do not automatically update the parameters, instead they require the update parameters button to be pressed first to lock in the selection.
