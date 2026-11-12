from datetime import datetime, timedelta
import os
import tarfile
import xarray as xr
import numpy as np
import dask.array as da
from pre_coords import get_coords
class ExtractData:
    def __init__(self, pars):
        self.basedir = pars.basedir
        self.version = pars.version
        self.zarredir = pars.zarredir
        self.last_date = pars.last_date
        self.type = pars.type
        self.sp_resolution = pars.sp_resolution
        self.x_pixels = pars.x_pixels
        self.y_pixels = pars.y_pixels
        self.internal_path = 'data/radman/archive/prd/composite/'
        self.time_resolution = pars.time_resolution
        self.gain = 0.5
        self.offset = -32
        self.X, self.Y, self.lat, self.lon, self.crs_attrs = get_coords(self.x_pixels, self.y_pixels)
        self.old_database = pars.old_database
        
    
    def __call__(self):
        ds = self.extract()
        return self.AddCoordsAttrs(ds)


    def get_dates(self):
        last_date = datetime.strptime(self.last_date, "%Y%m%d")
        start_date = last_date + timedelta(days=1)
        end_date = datetime.now() - timedelta(days=1)
        end_date = end_date.date()
        #end_date = datetime.combine(end_date.date(), datetime.min.time().replace(hour=23,minute=50,second=0))
        self.dates = []
        current = start_date
        while current <= end_date:
             self.dates.append(current)
             current += timedelta(days=1)
    # /max/2016/2016-07-05/dk.com.201607052355.500_max.h5
    def get_10min_intervals(self, date):
        start_time = datetime.combine(date, datetime.min.time())
        end_time = start_time + timedelta(days=1) - timedelta(minutes=10)
        intervals = []
        times = []
        current_time = start_time
        while current_time <= end_time:
            intervals.append(current_time.strftime(f"{self.internal_path}{self.type}/%Y/%Y-%m-%d/dk.com.%Y%m%d%H%M.{self.sp_resolution}_{self.type}.h5"))
            times.append(current_time)
            current_time += timedelta(minutes=self.time_resolution)
        return intervals, times
    def create_dataset_from_h5(self, tarFile, dateTime):
            ds = xr.open_dataset(tarFile,group='dataset1/data1',engine="h5netcdf", chunks = -1,phony_dims='sort')
            ds = ds.rename({'data':'dbz','phony_dim_0':'y','phony_dim_1':'x'})
            ds['dbz'] = ds['dbz'].where((ds['dbz']!=255),other=np.nan)
            ds['dbz'] = ds['dbz']*self.gain +self.offset
            ds['dbz'] = ds['dbz'].astype(np.float32)
            ds = ds.expand_dims(time=dateTime)
            ds['time'].attrs = {'long_name': 'Time','standard_name':'time'}
            ds.load()
            return ds
        
    def create_empty_timestep(self, dateTime):
        ds = np.ones((self.y_pixels,self.x_pixels))*np.nan
        ds = da.from_array(ds,chunks=-1)
        ds = xr.Dataset(data_vars={'dbz':(("y","x"), ds)})
        ds = ds.expand_dims(time=dateTime)
        ds['time'].attrs = {'long_name': 'Time','standard_name':'time'}
        return ds
    def AddCoordsAttrs(self,ds):
        ds.coords['y'] = self.Y
        ds['y'].attrs={'units':'m','standard_name':'projection_y_coordinate','axis':'Y'}
        ds.coords['x'] = self.X
        ds['x'].attrs={'units':'m','standard_name':'projection_x_coordinate','axis':'X'}
        lat = da.from_array(self.lat,chunks=(self.y_pixels,self.x_pixels))
        lon = da.from_array(self.lon,chunks=(self.y_pixels,self.x_pixels))#864,992
        ds = ds.assign_coords(lon=(('y','x'),lon),lat=(('y','x'),lat))
        ds['lat'].attrs = {'long_name': 'Latitude', 'standard_name': 'latitude', 'units': 'degrees_north'}
        ds['lon'].attrs = {'long_name': 'Longitude', 'standard_name': 'longitude', 'units': 'degrees_east'}
        ds = ds.chunk({"time":1,"y":self.y_pixels,"x":self.x_pixels})
        ds['crs'] = xr.DataArray(attrs=self.crs_attrs)
        ds['dbz'].attrs = {'grid_mapping': 'crs','long_name':'10 min radar reflectivity','standard_name': 'equivalent_reflectivity_factor', 'units':'dBZ'}
        ds.attrs = {'Author': 'Thomas Bøvith (tbh@dmi.dk)', 'Conventions': 'CF-1.6', 'consistent_timestep_start': '2016-02-29T00:00:00.000000000', 'institution': 'Danmarks Meteorologiske Institute (DMI)', 'license': 'CC-BY-4.0', 'mlcast_created_by': 'Ricardo Jara <arjj@dmi.dk>', 'mlcast_created_on': '2026-02-24T09:00:17.521323', 'mlcast_created_with': 'https://github.com/mlcast-community/mlcast-dataset-DMI-radar_precipitation@0.1.0', 'mlcast_dataset_identifier': 'DK-DMI-precipitation', 'mlcast_dataset_version': f'{self.version}', 'title': 'radar-based precipitation'}
        ds.attrs['mlcast_dataset_version'] = self.version
        ds.attrs['mlcast_created_with'] = f'https://github.com/mlcast-community/mlcast-dataset-DMI-radar_precipitation@{self.version}'
        now = datetime.datetime.now().isoformat()
        ds.attrs['mlcast_created_on'] = now

        return ds

    def extract(self):

        self.get_dates()
        period_ds = []
        if self.old_database:
            old_ds = xr.open_zarr(self.old_database,consolidated=True)
            period_ds.append(old_ds)
        for date in self.dates:
            path = date.strftime(f"{self.basedir}/%Y/composite.%Y%m%d.{self.type}.h5.tar")
            intervals, times = self.get_10min_intervals(date)
            if os.path.exists(path):
                day_ds = []
                with tarfile.open(path, 'r') as tar:
                    for i, interval in enumerate(intervals):
                        try:
                            with tar.extractfile(interval) as tarFile:
                                data_set = self.create_dataset_from_h5(tarFile,times[i])
                                day_ds.append(data_set)
                            
                        except KeyError:
                            empty_dataset = self.create_empty_timestep(times[i])      
                            day_ds.append(empty_dataset)
                day_ds = xr.concat(day_ds, dim='time')
                period_ds.append(day_ds)
            else:
                day_ds = []
                for time in times:
                    empty_dataset = self.create_empty_timestep(time)
                    day_ds.append(empty_dataset)
                day_ds = xr.concat(day_ds, dim='time')
                period_ds.append(day_ds)
        period_ds = xr.concat(period_ds, dim='time')
        return period_ds





        



