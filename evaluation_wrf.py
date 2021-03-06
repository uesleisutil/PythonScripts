#!/home/uesleisutil/anaconda3/bin/python python
# -*- coding: utf-8 -*-

"""
File name:      evaluation_wrf.py
Author:         Ueslei Adriano Sutil
Email:          uesleisutil1@gmail.com
Created:        03 April 2019
Last modified:  17 April 2019
Version:        2.0.1
Python:         3.7.1

Evaluate WRF output using:
    - Bias (Contour);
    - Root Mean Square Error (RMSE; Contour);
    - Mean Absolute Percentage Error (MAPE; Contour);

Compare: 
    - ERA5 (Hersbach et al., 2018; https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels?tab=overview):
        Temperature at 2 meters height (°C);
        Wind Speed at 10 m height (m/s);
        Sea Level Pressure (hPa);

    - CFSR (Saha et al., 2010; https://rda.ucar.edu/datasets/ds093.0/):
        Temperature at 2 meters height (°C);
        Wind Speed at 10 m height (m/s);
        Sea Level Pressure (hPa);

Post-process the WRF simulation to match with the databases:
    cdo seltimestep,169/336 wrf.nc wrf_ts.nc
    cdo timselmean,6 wrf_ts.nc wrf_6h_ncks.nc
    cdo daymean wrf_6h_ncks.nc wrf_daymean_ncks.nc
"""

# Library import.
import numpy                as np
import matplotlib.pyplot    as plt
from   mpl_toolkits.basemap import Basemap
from   roms_libs            import *
from   wrf                  import getvar
from   progress.bar         import IncrementalBar
import netCDF4
import pyresample
import cmocean
import os
matplotlib.use('Agg')

# Customizations.
bbox            = [-53,-40,-32,-23]
lonbounds       = [-53,-40] 
latbounds       = [-32,-23]
wrf_file        = '/media/ueslei/Ueslei/INPE/PCI/Projetos/SC_2008/Outputs/normal/wrf_ts.nc'
wrf_file_cfsr   = '/media/ueslei/Ueslei/INPE/PCI/Projetos/SC_2008/Outputs/normal/wrf_6h_ncks.nc'
era_file        = '/media/ueslei/Ueslei/INPE/PCI/Projetos/SC_2008/Dados/Evaluation/ERA5/era5_novo.nc'
cfsr_file       = '/media/ueslei/Ueslei/INPE/PCI/Projetos/SC_2008/Dados/Evaluation/CFSR/cfsr.nc'

clevs_rmse_t2   = np.arange(0,5.05,0.01)
ticks_rmse_t2   = np.arange(min(clevs_rmse_t2),max(clevs_rmse_t2),1)
clevs_mape_t2   = np.arange(0,18.02,0.01)
ticks_mape_t2   = np.arange(min(clevs_mape_t2),max(clevs_mape_t2),2)
clevs_bias_t2   = np.arange(-3,3.1,0.01)
ticks_bias_t2   = np.arange(min(clevs_bias_t2),max(clevs_bias_t2),1)

clevs_rmse_wind = np.arange(0,4.1,0.01)
ticks_rmse_wind = np.arange(min(clevs_rmse_wind),max(clevs_rmse_wind),1)
clevs_mape_wind = np.arange(0,101,0.2)
ticks_mape_wind = np.arange(min(clevs_mape_wind),max(clevs_mape_wind),20)
clevs_bias_wind = np.arange(-2,9.1,0.1)
ticks_bias_wind = np.arange(min(clevs_bias_wind),max(clevs_bias_wind),1)

clevs_rmse_slp  = np.arange(0,2.05,0.01)
ticks_rmse_slp  = np.arange(min(clevs_rmse_slp),max(clevs_rmse_slp),0.5)
clevs_mape_slp  = np.arange(0,0.205,0.001)
ticks_mape_slp  = np.arange(min(clevs_mape_slp),max(clevs_mape_slp),0.05)
clevs_bias_slp  = np.arange(-2,2.01,0.01)
ticks_bias_slp  = np.arange(min(clevs_bias_slp),max(clevs_bias_slp),1)

print('Which data? (1) ERA5 or (2) CFSR?')      
dataset  = input()

if dataset == '1':
    print('Evaluate which WRF-ARW variable? (1) Temperature at 2 meters, (2) Wind Speed at 10m, (3) Sea Level Pressure?')
    contourf_var = input()
    if contourf_var == '1':
        nc_era      = netCDF4.Dataset(era_file)
        lon_era     = nc_era.variables['longitude'][:]-360
        lat_era     = nc_era.variables['latitude'][:]
        latli       = np.argmin(np.abs(lat_era-latbounds[1]))
        latui       = np.argmin(np.abs(lat_era-latbounds[0])) 
        lonli       = np.argmin(np.abs(lon_era-lonbounds[0]))
        lonui       = np.argmin(np.abs(lon_era-lonbounds[1]))  
        lon_era     = nc_era.variables['longitude'][lonli:lonui]-360
        lat_era     = nc_era.variables['latitude'][latli:latui]
        lon_era,lat_era = np.meshgrid(lon_era,lat_era)
        era_lat_len = len(lat_era[:,0])
        era_lon_len = len(lon_era[0, :])
        era_loop    = len(nc_era.variables['time'][:])
        observed    = np.zeros([era_loop,era_lat_len,era_lon_len])
        bar         = IncrementalBar('Processing Air Temperature at 2 m from ERA5', max=era_loop)
        for i in range(0,era_loop):
            temp_era        = nc_era.variables['t2m'][i,latli:latui,lonli:lonui]-273.15
            observed[i,:,:] = temp_era
            bar.next()
        bar.finish()
                       
        nc_wrf      = netCDF4.Dataset(wrf_file)
        lon_wrf     = nc_wrf.variables['XLONG'][0,:]
        lat_wrf     = nc_wrf.variables['XLAT'][:,0]               
        latli       = np.argmin(np.abs(lat_wrf-latbounds[1]))
        latui       = np.argmin(np.abs(lat_wrf-latbounds[0])) 
        lonli       = np.argmin(np.abs(lon_wrf-lonbounds[0]))
        lonui       = np.argmin(np.abs(lon_wrf-lonbounds[1]))
        lon_wrf     = lon_wrf[lonli:lonui]
        lat_wrf     = lat_wrf[latui:latli]
        lon_wrf,lat_wrf = np.meshgrid(lon_wrf,lat_wrf)      
        wrf_loop    = len(nc_wrf.variables['LH'][:,0,0])
        wrf_lat_len = len(lat_wrf[:,0])
        wrf_lon_len = len(lon_wrf[0,:])
        orig_def    = pyresample.geometry.SwathDefinition(lons=lon_wrf, lats=lat_wrf)
        targ_def    = pyresample.geometry.SwathDefinition(lons=lon_era, lats=lat_era)
        expected    = np.zeros([era_loop,era_lat_len,era_lon_len])
        bar         = IncrementalBar('Processing Air Temperature at 2 m from WRF', max=wrf_loop)
        for i in range(0,wrf_loop):  
            temp_wrf        = nc_wrf.variables['T2'][i,latui:latli,lonli:lonui]-273.15
            expected[i,:,:] = pyresample.kd_tree.resample_gauss(orig_def, temp_wrf, targ_def,radius_of_influence=50000, sigmas=25000, fill_value=None)
            bar.next()
        bar.finish()
   
    if contourf_var=='2':
        nc_era      = netCDF4.Dataset(era_file)
        lon_era     = nc_era.variables['longitude'][:]-360
        lat_era     = nc_era.variables['latitude'][:]
        latli       = np.argmin(np.abs(lat_era-latbounds[1]))
        latui       = np.argmin(np.abs(lat_era-latbounds[0])) 
        lonli       = np.argmin(np.abs(lon_era-lonbounds[0]))
        lonui       = np.argmin(np.abs(lon_era-lonbounds[1]))  
        lon_era     = nc_era.variables['longitude'][lonli:lonui]-360
        lat_era     = nc_era.variables['latitude'][latli:latui]
        lon_era,lat_era = np.meshgrid(lon_era,lat_era)
        era_lat_len = len(lat_era[:,0])
        era_lon_len = len(lon_era[0, :])
        era_loop    = len(nc_era.variables['time'][:])
        u10_era2    = np.zeros([era_loop,era_lat_len,era_lon_len])
        v10_era2    = np.zeros([era_loop,era_lat_len,era_lon_len]) 
        bar         = IncrementalBar('Processing Wind Magnitude at 10 m from ERA5', max=era_loop)      
        for i in range(0,era_loop):
            u10_era         = nc_era.variables['u10'][i,latli:latui,lonli:lonui]
            v10_era         = nc_era.variables['v10'][i,latli:latui,lonli:lonui]
            u10_era2[i,:,:] = u10_era
            v10_era2[i,:,:] = v10_era  
            bar.next()
        bar.finish()
        nc_wrf      = netCDF4.Dataset(wrf_file)
        lon_wrf     = nc_wrf.variables['XLONG'][0,:]
        lat_wrf     = nc_wrf.variables['XLAT'][:,0]               
        latli       = np.argmin(np.abs(lat_wrf-latbounds[1]))
        latui       = np.argmin(np.abs(lat_wrf-latbounds[0])) 
        lonli       = np.argmin(np.abs(lon_wrf-lonbounds[0]))
        lonui       = np.argmin(np.abs(lon_wrf-lonbounds[1]))
        lon_wrf     = lon_wrf[lonli:lonui]
        lat_wrf     = lat_wrf[latui:latli]
        lon_wrf,lat_wrf = np.meshgrid(lon_wrf,lat_wrf)      
        wrf_loop    = len(nc_wrf.variables['LH'][:,0,0])
        wrf_lat_len = len(lat_wrf[:,0])
        wrf_lon_len = len(lon_wrf[0,:])

        orig_def    = pyresample.geometry.SwathDefinition(lons=lon_wrf, lats=lat_wrf)
        targ_def    = pyresample.geometry.SwathDefinition(lons=lon_era, lats=lat_era)

        u10_wrf2   = np.zeros([era_loop,era_lat_len,era_lon_len])
        v10_wrf2   = np.zeros([era_loop,era_lat_len,era_lon_len])       
        bar        = IncrementalBar('Processing Wind Magnitude at 10 m from WRF', max=wrf_loop)    
        for i in range(0,wrf_loop):  
            u10_wrf         = nc_wrf.variables['U10'][i,latui:latli,lonli:lonui]
            u10_wrf2[i,:,:] = pyresample.kd_tree.resample_gauss(orig_def, u10_wrf, targ_def, radius_of_influence=50000, neighbours=10,sigmas=25000, fill_value=None)
            v10_wrf         = nc_wrf.variables['V10'][i,latui:latli,lonli:lonui]
            v10_wrf2[i,:,:] = pyresample.kd_tree.resample_gauss(orig_def, v10_wrf, targ_def, radius_of_influence=50000, neighbours=10,sigmas=25000, fill_value=None)
            bar.next()
        bar.finish()     

        expected = np.sqrt(u10_wrf2**2 + v10_wrf2**2)
        observed = np.sqrt(u10_era2**2 + v10_era2**2)

    if contourf_var=='3':
        nc_era      = netCDF4.Dataset(era_file)
        lon_era     = nc_era.variables['longitude'][:]-360
        lat_era     = nc_era.variables['latitude'][:]
        latli       = np.argmin(np.abs(lat_era-latbounds[1]))
        latui       = np.argmin(np.abs(lat_era-latbounds[0])) 
        lonli       = np.argmin(np.abs(lon_era-lonbounds[0]))
        lonui       = np.argmin(np.abs(lon_era-lonbounds[1]))  
        lon_era     = nc_era.variables['longitude'][lonli:lonui]-360
        lat_era     = nc_era.variables['latitude'][latli:latui]
        lon_era,lat_era = np.meshgrid(lon_era,lat_era)
        era_lat_len = len(lat_era[:,0])
        era_lon_len = len(lon_era[0, :])
        era_loop    = len(nc_era.variables['time'][:])
        observed    = np.zeros([era_loop,era_lat_len,era_lon_len])
        bar         = IncrementalBar('Processing Sea Level Pressure from ERA5', max=era_loop)    
        for i in range(0,era_loop):
            slp_era         = nc_era.variables['msl'][i,latli:latui,lonli:lonui]/100
            observed[i,:,:] = slp_era
            bar.next()
        bar.finish()  

        nc_wrf      = netCDF4.Dataset(wrf_file)
        lon_wrf     = nc_wrf.variables['XLONG'][0,:]
        lat_wrf     = nc_wrf.variables['XLAT'][:,0]               
        latli       = np.argmin(np.abs(lat_wrf-latbounds[1]))
        latui       = np.argmin(np.abs(lat_wrf-latbounds[0])) 
        lonli       = np.argmin(np.abs(lon_wrf-lonbounds[0]))
        lonui       = np.argmin(np.abs(lon_wrf-lonbounds[1]))
        lon_wrf     = lon_wrf[lonli:lonui]
        lat_wrf     = lat_wrf[latui:latli]
        lon_wrf,lat_wrf = np.meshgrid(lon_wrf,lat_wrf)      
        wrf_loop    = len(nc_wrf.variables['LH'][:,0,0])
        wrf_lat_len = len(lat_wrf[:,0])
        wrf_lon_len = len(lon_wrf[0,:])
        orig_def    = pyresample.geometry.SwathDefinition(lons=lon_wrf, lats=lat_wrf)
        targ_def    = pyresample.geometry.SwathDefinition(lons=lon_era, lats=lat_era)
        expected    = np.zeros([era_loop,era_lat_len,era_lon_len])
        bar         = IncrementalBar('Processing Sea Level Pressure from WRF', max=wrf_loop)    
        for i in range(0,wrf_loop):  
            slp_wrf         = getvar(nc_wrf, "slp", i, units="hPa",meta=False)[latui:latli,lonli:lonui]
            expected[i,:,:] = pyresample.kd_tree.resample_gauss(orig_def, slp_wrf, targ_def, radius_of_influence=50000, neighbours=10,sigmas=25000, fill_value=None)
            bar.next()
        bar.finish()  
        
if dataset == '2':
    print('Evaluate which WRF-ARW variable? (1) Temperature at 2 meters, (2) Wind Speed at 10m or (3) Sea Level Pressure?')
    contourf_var  = input()
    if contourf_var=='1':
        nc_cfsr      = netCDF4.Dataset(cfsr_file)
        lon_cfsr     = nc_cfsr.variables['lon'][:]
        lat_cfsr     = nc_cfsr.variables['lat'][:]
        latli        = np.argmin(np.abs(lat_cfsr-latbounds[1]))
        latui        = np.argmin(np.abs(lat_cfsr-latbounds[0])) 
        lonli        = np.argmin(np.abs(lon_cfsr-lonbounds[0]))
        lonui        = np.argmin(np.abs(lon_cfsr-lonbounds[1]))
        lon_cfsr     = nc_cfsr.variables['lon'][lonli:lonui]
        lat_cfsr     = nc_cfsr.variables['lat'][latli:latui]
        lon_cfsr,lat_cfsr = np.meshgrid(lon_cfsr,lat_cfsr)
        cfsr_loop    = len(nc_cfsr.variables['time'][:])
        cfsr_lat_len = len(lat_cfsr[:,0])
        cfsr_lon_len = len(lon_cfsr[0, :])
        observed     = np.zeros([cfsr_loop,cfsr_lat_len,cfsr_lon_len])
        bar          = IncrementalBar('Processing Air Temperature at 2 m from CFSR', max=cfsr_loop)    
        for i in range(0,cfsr_loop):
            temp_cfsr       = nc_cfsr.variables['TMP_L103'][i,latli:latui,lonli:lonui]-273.15              
            observed[i,:,:] = temp_cfsr
            bar.next()
        bar.finish()  

        nc_wrf      = netCDF4.Dataset(wrf_file_cfsr)
        lon_wrf     = nc_wrf.variables['XLONG'][0,:]
        lat_wrf     = nc_wrf.variables['XLAT'][:,0]               
        latli       = np.argmin(np.abs(lat_wrf-latbounds[1]))
        latui       = np.argmin(np.abs(lat_wrf-latbounds[0])) 
        lonli       = np.argmin(np.abs(lon_wrf-lonbounds[0]))
        lonui       = np.argmin(np.abs(lon_wrf-lonbounds[1]))
        lon_wrf     = lon_wrf[lonli:lonui]
        lat_wrf     = lat_wrf[latui:latli]
        lon_wrf,lat_wrf = np.meshgrid(lon_wrf,lat_wrf)      
        wrf_loop    = nc_wrf.variables['LH'][:,0,0]
        wrf_loop    = len(wrf_loop)
        wrf_lat_len = len(lat_wrf[:,0])
        wrf_lon_len = len(lon_wrf[0,:])
        orig_def    = pyresample.geometry.SwathDefinition(lons=lon_wrf, lats=lat_wrf)
        targ_def    = pyresample.geometry.SwathDefinition(lons=lon_cfsr, lats=lat_cfsr)
        expected    = np.zeros([cfsr_loop,cfsr_lat_len,cfsr_lon_len])
        bar         = IncrementalBar('Processing Air Temperature at 2 m from WRF', max=wrf_loop)    
        for i in range(0,wrf_loop):  
            temp_wrf        = nc_wrf.variables['T2'][i,latui:latli,lonli:lonui]-273.15
            expected[i,:,:] = pyresample.kd_tree.resample_gauss(orig_def, temp_wrf, targ_def, radius_of_influence=50000, neighbours=10,sigmas=25000, fill_value=None)
            bar.next()
        bar.finish()

    if contourf_var=='2':
        nc_cfsr      = netCDF4.Dataset(cfsr_file)
        lon_cfsr     = nc_cfsr.variables['lon'][:]
        lat_cfsr     = nc_cfsr.variables['lat'][:]
        latli        = np.argmin(np.abs(lat_cfsr-latbounds[1]))
        latui        = np.argmin(np.abs(lat_cfsr-latbounds[0])) 
        lonli        = np.argmin(np.abs(lon_cfsr-lonbounds[0]))
        lonui        = np.argmin(np.abs(lon_cfsr-lonbounds[1]))
        lon_cfsr     = nc_cfsr.variables['lon'][lonli:lonui]
        lat_cfsr     = nc_cfsr.variables['lat'][latli:latui]
        lon_cfsr,lat_cfsr = np.meshgrid(lon_cfsr,lat_cfsr)
        cfsr_loop    = len(nc_cfsr.variables['time'][:])
        cfsr_lat_len = len(lat_cfsr[:,0])
        cfsr_lon_len = len(lon_cfsr[0, :])
        u10_cfsr2   = np.zeros([cfsr_loop,cfsr_lat_len,cfsr_lon_len])  
        v10_cfsr2   = np.zeros([cfsr_loop,cfsr_lat_len,cfsr_lon_len])  
        bar         = IncrementalBar('Processing Wing Magnitude at 10 m from CFSR', max=cfsr_loop)  
        for i in range(0,cfsr_loop):
            u10_cfsr         = nc_cfsr.variables['U_GRD_L103'][i,latli:latui,lonli:lonui]
            v10_cfsr         = nc_cfsr.variables['V_GRD_L103'][i,latli:latui,lonli:lonui]
            u10_cfsr2[i,:,:] = u10_cfsr
            v10_cfsr2[i,:,:] = v10_cfsr
            bar.next()
        bar.finish()

        nc_wrf      = netCDF4.Dataset(wrf_file_cfsr)
        lon_wrf     = nc_wrf.variables['XLONG'][0,:]
        lat_wrf     = nc_wrf.variables['XLAT'][:,0]               
        latli       = np.argmin(np.abs(lat_wrf-latbounds[1]))
        latui       = np.argmin(np.abs(lat_wrf-latbounds[0])) 
        lonli       = np.argmin(np.abs(lon_wrf-lonbounds[0]))
        lonui       = np.argmin(np.abs(lon_wrf-lonbounds[1]))
        lon_wrf     = lon_wrf[lonli:lonui]
        lat_wrf     = lat_wrf[latui:latli]
        lon_wrf,lat_wrf = np.meshgrid(lon_wrf,lat_wrf)      
        wrf_loop    = len(nc_wrf.variables['Times'][:])
        wrf_lat_len = len(lat_wrf[:,0])
        wrf_lon_len = len(lon_wrf[0,:])
        orig_def    = pyresample.geometry.SwathDefinition(lons=lon_wrf, lats=lat_wrf)
        targ_def    = pyresample.geometry.SwathDefinition(lons=lon_cfsr, lats=lat_cfsr)
        u10_wrf2   = np.zeros([cfsr_loop,cfsr_lat_len,cfsr_lon_len])
        v10_wrf2   = np.zeros([cfsr_loop,cfsr_lat_len,cfsr_lon_len])  
        bar         = IncrementalBar('Processing Wing Magnitude at 10 m from WRF', max=wrf_loop)       
        for i in range(0,wrf_loop):  
            u10_wrf         = nc_wrf.variables['U10'][i,latui:latli,lonli:lonui]
            u10_wrf2[i,:,:] = pyresample.kd_tree.resample_gauss(orig_def, u10_wrf, targ_def, radius_of_influence=50000, neighbours=10,sigmas=25000, fill_value=None)
            v10_wrf         = nc_wrf.variables['V10'][i,latui:latli,lonli:lonui]
            v10_wrf2[i,:,:] = pyresample.kd_tree.resample_gauss(orig_def, v10_wrf, targ_def, radius_of_influence=50000, neighbours=10,sigmas=25000, fill_value=None)
            bar.next()
        bar.finish()       
        expected = np.sqrt(u10_wrf2**2 + v10_wrf2**2)
        observed = np.sqrt(u10_cfsr2**2 + v10_cfsr2**2)

    if contourf_var=='3':
        nc_cfsr      = netCDF4.Dataset(cfsr_file)
        lon_cfsr     = nc_cfsr.variables['lon'][:]
        lat_cfsr     = nc_cfsr.variables['lat'][:]
        latli        = np.argmin(np.abs(lat_cfsr-latbounds[1]))
        latui        = np.argmin(np.abs(lat_cfsr-latbounds[0])) 
        lonli        = np.argmin(np.abs(lon_cfsr-lonbounds[0]))
        lonui        = np.argmin(np.abs(lon_cfsr-lonbounds[1]))
        lon_cfsr     = nc_cfsr.variables['lon'][lonli:lonui]
        lat_cfsr     = nc_cfsr.variables['lat'][latli:latui]
        lon_cfsr,lat_cfsr = np.meshgrid(lon_cfsr,lat_cfsr)
        cfsr_loop    = len(nc_cfsr.variables['time'][:])
        cfsr_lat_len = len(lat_cfsr[:,0])
        cfsr_lon_len = len(lon_cfsr[0, :])
        observed     = np.zeros([cfsr_loop,cfsr_lat_len,cfsr_lon_len])
        bar          = IncrementalBar('Processing Sea Level Pressure from CFSR', max=cfsr_loop)  
        for i in range(0,cfsr_loop):
            slp_cfsr        = nc_cfsr.variables['PRES_L101'][i,latli:latui,lonli:lonui]/100              
            observed[i,:,:] = slp_cfsr
            bar.next()
        bar.finish()   

        nc_wrf      = netCDF4.Dataset(wrf_file_cfsr)
        lon_wrf     = nc_wrf.variables['XLONG'][0,:]
        lat_wrf     = nc_wrf.variables['XLAT'][:,0]               
        latli       = np.argmin(np.abs(lat_wrf-latbounds[1]))
        latui       = np.argmin(np.abs(lat_wrf-latbounds[0])) 
        lonli       = np.argmin(np.abs(lon_wrf-lonbounds[0]))
        lonui       = np.argmin(np.abs(lon_wrf-lonbounds[1]))
        lon_wrf     = lon_wrf[lonli:lonui]
        lat_wrf     = lat_wrf[latui:latli]
        lon_wrf,lat_wrf = np.meshgrid(lon_wrf,lat_wrf)      
        wrf_loop    = len(nc_wrf.variables['Times'][:])
        wrf_lat_len = len(lat_wrf[:,0])
        wrf_lon_len = len(lon_wrf[0,:])
        orig_def    = pyresample.geometry.SwathDefinition(lons=lon_wrf, lats=lat_wrf)
        targ_def    = pyresample.geometry.SwathDefinition(lons=lon_cfsr, lats=lat_cfsr)
        expected    = np.zeros([cfsr_loop,cfsr_lat_len,cfsr_lon_len])
        bar         = IncrementalBar('Processing Sea Level Pressure from WRF', max=wrf_loop)  
        for i in range(0,wrf_loop):  
            slp_wrf         = getvar(nc_wrf, "slp", i, units="hPa",meta=False)[latui:latli,lonli:lonui]
            expected[i,:,:] = pyresample.kd_tree.resample_gauss(orig_def, slp_wrf, targ_def, radius_of_influence=50000, neighbours=10,sigmas=25000, fill_value=None)
            bar.next()
        bar.finish() 

print('Which statistical metric? (1) Root Mean Square Error, (2) Mean Absolute Error or (3) Bias.')
metric  = input()
if metric=='1':
    differences         = expected-observed
    differences_squared = differences ** 2 
    mean_of_differences_squared = np.average(differences_squared,axis=0)
    val                 = np.sqrt(mean_of_differences_squared)

if metric=='2':
    val = np.abs((observed-expected)/observed).mean(axis=0)*100

if metric=='3':
    expected1 = np.average(expected,axis=0) 
    observed1 = np.average(observed,axis=0)
    val       = expected1-observed1

# Create and plot map.
m    = Basemap(projection='merc',llcrnrlat=bbox[2],urcrnrlat=bbox[3],llcrnrlon=bbox[0],urcrnrlon=bbox[1], lat_ts=30,resolution='i')
fig  = plt.figure(1,figsize=(10,8))
plt.xlabel('Longitude'u' [\N{DEGREE SIGN}]',labelpad=18,size=10)
plt.ylabel('Latitude'u' [\N{DEGREE SIGN}]',labelpad=33,size=10)
ax   = fig.add_subplot(111)
m.drawparallels(np.arange(-90.,120.,1), linewidth=0.00, color='black', labels=[1,0,0,1],labelstyle="N/S",fontsize=10)
m.drawmeridians(np.arange(-180.,180.,2), linewidth=0.00,color='black', labels=[1,0,0,1],labelstyle="N/S",fontsize=10)
m.drawcountries(color = '#000000',linewidth=0.5)
m.drawcoastlines(color = '#000000',linewidth=0.5)

if metric=='1' and contourf_var=='1':
    clevs = clevs_rmse_t2
    ticks = ticks_rmse_t2
if metric=='2' and contourf_var=='1':
    clevs = clevs_mape_t2
    ticks = ticks_mape_t2
if metric=='3' and contourf_var=='1':
    clevs = clevs_bias_t2
    ticks = ticks_bias_t2
if metric=='1' and contourf_var=='2':
    clevs = clevs_rmse_wind
    ticks = ticks_rmse_wind
if metric=='2' and contourf_var=='2':
    clevs = clevs_mape_wind
    ticks = ticks_mape_wind
if metric=='3' and contourf_var=='2':
    clevs = clevs_bias_wind
    ticks = ticks_bias_wind
if metric=='1' and contourf_var=='3':
    clevs = clevs_rmse_slp
    ticks = ticks_rmse_slp
if metric=='2' and contourf_var=='3':
    clevs = clevs_mape_slp
    ticks = ticks_mape_slp
if metric=='3' and contourf_var=='3':
    clevs = clevs_bias_slp
    ticks = ticks_bias_slp

if dataset == '1':
    if metric=='1' or metric=='2':
        cmap  = cmocean.cm.thermal
        h1    = m.contourf(lon_era, lat_era, val, clevs,latlon=True,cmap=cmap,extend="both")
    if metric=='3':
        cmap  = cmocean.cm.balance
        h1    = m.contourf(lon_era, lat_era, val, clevs,latlon=True,cmap=cmap,norm=MidpointNormalize(midpoint=0),extend="both")          
if dataset =='2':
    if metric=='2' or metric=='3':
        cmap  = matplotlib.pyplot.jet()
        h1    = m.contourf(lon_cfsr, lat_cfsr, val, clevs,latlon=True,cmap=cmap)   
    if metric=='1':
        cmap  = cmocean.cm.balance
        h1    = m.contourf(lon_cfsr, lat_cfsr, val, clevs,latlon=True,cmap=cmap,norm=MidpointNormalize(midpoint=0),extend="both") 
cax   = fig.add_axes([0.37, 0.025, 0.27, 0.025])     
cb    = fig.colorbar(h1, cax=cax, orientation="horizontal",panchor=(0.5,0.5),shrink=0.3,ticks=ticks,pad=-10.5)

if metric=='1':
    if contourf_var=='1':
        cb.set_label(r'Air Temperature at 2 meters Root Mean Square Error [$^\circ\!$C]', fontsize=9, color='0.2',labelpad=0)
    if contourf_var=='2':
        cb.set_label(r'Wind Speed at 10 meters Root Mean Square Error [m.s⁻¹]', fontsize=9, color='0.2',labelpad=0)
    if contourf_var=='3':
         cb.set_label(r'Sea Level Pressure Root Mean Square Error [hPa]', fontsize=9, color='0.2',labelpad=0)       
if metric=='2':
    if contourf_var=='1':
        cb.set_label(r'Air Temperature at 2 meters Mean Absolute Percentage Error [%]', fontsize=9, color='0.2',labelpad=-0.2)
    if contourf_var=='2':
        cb.set_label(r'Wind Speed at 10 meters Mean Absolute Percentage Error [%]', fontsize=9, color='0.2',labelpad=-0.2)
    if contourf_var=='3':
        cb.set_label(r'Sea Level Pressure Mean Absolute Percentage Error [%]', fontsize=9, color='0.2',labelpad=-0.2)     
if metric=='3':
    if contourf_var=='1':
        cb.set_label(r'Air Temperature at 2 meters Bias [$^\circ\!$C]', fontsize=9, color='0.2',labelpad=-0.2)
    if contourf_var=='2':
        cb.set_label(r'Wind Speed at 10 meters Bias [m.s⁻¹]', fontsize=9, color='0.2',labelpad=-0.2)
    if contourf_var=='3':
        cb.set_label(r'Sea Level Pressure Bias [hPa]', fontsize=9, color='0.2',labelpad=-0.2)  
            
cb.ax.tick_params(labelsize=9, length=2, color='0.2', labelcolor='0.2',direction='in') 
cb.set_ticks(ticks)
try:
    os.makedirs("wrf_evaluation")
except FileExistsError:
    pass 
if metric == '1' and dataset == '1' and contourf_var == '1':
        plt.savefig('./wrf_evaluation/t2_rmse_wrf_era5.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)              
if metric == '1' and dataset == '1' and contourf_var == '2':
        plt.savefig('./wrf_evaluation/wind_rmse_wrf_era5.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)              
if metric == '1' and dataset == '1' and contourf_var == '3':
        plt.savefig('./wrf_evaluation/slp_rmse_wrf_era5.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)
if metric == '2' and dataset == '1' and contourf_var == '1':
        plt.savefig('./wrf_evaluation/t2_mape_wrf_era5.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)              
if metric == '2' and dataset == '1' and contourf_var == '2':
        plt.savefig('./wrf_evaluation/wind_mape_wrf_era5.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)              
if metric == '2' and dataset == '1' and contourf_var == '3':
        plt.savefig('./wrf_evaluation/slp_mape_wrf_era5.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)   
if metric == '3' and dataset == '1' and contourf_var == '1':
        plt.savefig('./wrf_evaluation/t2_bias_wrf_era5.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)              
if metric == '3' and dataset == '1' and contourf_var == '2':
        plt.savefig('./wrf_evaluation/wind_bias_wrf_era5.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)              
if metric == '3' and dataset == '1' and contourf_var == '3':
        plt.savefig('./wrf_evaluation/slp_bias_wrf_era5.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)
if metric == '1' and dataset == '2' and contourf_var == '1':
        plt.savefig('./wrf_evaluation/t2_rmse_wrf_cfsr.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)              
if metric == '1' and dataset == '2' and contourf_var == '2':
        plt.savefig('./wrf_evaluation/wind_rmse_wrf_cfsr.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)              
if metric == '1' and dataset == '2' and contourf_var == '3':
        plt.savefig('./wrf_evaluation/slp_rmse_wrf_cfsr.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)
if metric == '2' and dataset == '2' and contourf_var == '1':
        plt.savefig('./wrf_evaluation/t2_mape_wrf_cfsr.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)              
if metric == '2' and dataset == '2' and contourf_var == '2':
        plt.savefig('./wrf_evaluation/wind_mape_wrf_cfsr.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)              
if metric == '2' and dataset == '2' and contourf_var == '3':
        plt.savefig('./wrf_evaluation/slp_mape_wrf_cfsr.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)
if metric == '3' and dataset == '2' and contourf_var == '1':
        plt.savefig('./wrf_evaluation/t2_bias_wrf_cfsr.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)              
if metric == '3' and dataset == '2' and contourf_var == '2':
        plt.savefig('./wrf_evaluation/wind_bias_wrf_cfsr.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)              
if metric == '3' and dataset == '2' and contourf_var == '3':
        plt.savefig('./wrf_evaluation/slp_bias_wrf_cfsr.png', transparent=False, bbox_inches = 'tight', pad_inches=0, dpi=250)              
