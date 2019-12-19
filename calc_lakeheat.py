
"""
Author      : Inne Vanderkelen (inne.vanderkelen@vub.be)
Institution : Vrije Universiteit Brussel (VUB)
Date        : November 2019

Subroutine to calculate lake heat content per grid cell 
    - calculates lake heat per layer, and make weighted sum
    - saves output in dictionary per model, per forcing in lake_heat
    - is saved in variable when flag is on 

"""

import os 
import xarray as xr
import numpy as np
from calc_volumes import * 


def calc_lakeheat(models,forcings,future_experiment, indir_lakedata, years_grand, resolution,outdir, years_isimip,start_year, end_year, flag_scenario, flag_savelakeheat, rho_liq, cp_liq):

    # define experiment
    experiment= 'historical_'+future_experiment # can also be set to 'historical' or 'rcp60', but start_year will in this case have to be within year range

    # CLM45 (loop can be expanded) overwritten with other dictionary
    # for the different models
    lakeheat = {}

    for model in models:
        lakeheat_model={} # sub directory for each model
        
        # calculate depth per layer 
        depth_per_layer = calc_depth_per_layer(flag_scenario, indir_lakedata, years_grand, start_year,end_year, resolution, model,outdir)

        for forcing in forcings:

            # define directory and filename
            variable = 'watertemp'                        
            outdir_model = outdir+variable+'/'+model+'/'

            if model == 'CLM45': # load interpolated temperatures
                outfile_annual = model.lower()+'_'+forcing+'_'+experiment+'_'+variable+'_interp_1861_2099'+'_'+'annual'+'.nc4'
            else: 
                outfile_annual = model.lower()+'_'+forcing+'_'+experiment+'_'+variable+'_1861_2099'+'_'+'annual'+'.nc4'

            # if simulation is available 
            if os.path.isfile(outdir_model+outfile_annual): 
                print('Calculating lake heat of '+ model + ' ' + forcing)
                ds_laketemp = xr.open_dataset(outdir_model+outfile_annual,decode_times=False)
                laketemp = ds_laketemp.watertemp.values
        
                if flag_scenario == 'reservoirs': 
                    # use lake temperature from first year of analysis
                    laketemp = laketemp[years_isimip[model].index(start_year),:,:,:]
                else: 
                    # extract years of analysis
                    laketemp = laketemp[years_isimip[model].index(start_year):years_isimip[model].index(end_year),:,:,:]

                lakeheat_layered =  rho_liq  * depth_per_layer * cp_liq * laketemp
                
                # add manual time dimension for reservoir scenario. 
                if flag_scenario == 'reservoirs': lakeheat_layered = np.expand_dims(lakeheat_layered,axis=0)

                # sum up for total layer (less memory)
                lakeheat_perarea = lakeheat_layered.sum(axis=1)
                lakeheat_forcing = calc_lakeheat_area(resolution, indir_lakedata, flag_scenario, lakeheat_perarea,years_grand,start_year,end_year)

                # clean up
                del laketemp, ds_laketemp, lakeheat_layered, lakeheat_perarea

                # save lakeheat in directory structure per forcing
            if not lakeheat_model:
                lakeheat_model = {forcing:lakeheat_forcing}
            else: 
                lakeheat_model.update({forcing:lakeheat_forcing})

        # save lakeheat of forcings in directory structure per model
        if not lakeheat:
            lakeheat = {model:lakeheat_model}
        else:
            lakeheat.update({model:lakeheat_model})    
        
        # clean up   
        del lakeheat_model, lakeheat_forcing
    # save calculated lake heat (this needs to be cleaned up before continuing working on code.)

    # Save according to scenario flag
    if flag_savelakeheat:
        lakeheat_filename = 'lakeheat_'+flag_scenario+'.npy'
        np.save(outdir+lakeheat_filename, lakeheat) 

    return lakeheat
