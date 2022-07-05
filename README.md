# merra2pwv
Pipeline to compute integrated water column and atmospheric opacity at millimetre wavelengths from MERRA-2 datasets

## Requirements
  * The am Atmospheric Model [1]

## Outline
  * Download MERRA-2 inst3_3d_asm_Np data [2] in ASCII format into data/merra-2 subfolder
  * Run parse_merra2.py to interpolate atmospheric model input data to the desired locations, stores reduced and interpolated site data in data/sites subfolder
  * Run write_and_run_amc.py to compile input files for and run *am*, produces input/output/error files in data/am subfolder
  * Run extract_columns.sh & extract_tau.sh to extract integrated column and opacity data, produces CSV tables in data/am-reduced subfolder

## References
[1] [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5794521.svg)](https://doi.org/10.5281/zenodo.5794521)
[2] Global Modeling and Assimilation Office (GMAO) (2015), MERRA-2 inst3_3d_asm_Np: 3d,3-Hourly,Instantaneous,Pressure-Level,Assimilation,Assimilated Meteorological Fields V5.12.4, Greenbelt, MD, USA, Goddard Earth Sciences Data and Information Services Center (GES DISC), Online: [10.5067/QBZ6MG944HW0](https://doi.org/10.5067/QBZ6MG944HW0)
