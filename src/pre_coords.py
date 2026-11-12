import numpy as np
import cartopy.crs as ccrs
from pyproj import CRS
from dataclasses import dataclass, field

def get_coords(Xpixels, Ypixels):
        proj_str = '+proj=stere +ellps=WGS84 +lat_0=56 +lon_0=10.5666 +lat_ts=56'
        proj = ccrs.CRS(CRS.from_proj4(str(proj_str)))
        src_crs = ccrs.PlateCarree()
        coordArr = np.array([[52.29427206,4.3790827],
                            [52.29427206,18.89328087],[60.,3.],[59.82770843,20.73514017]])
        XY_corners = np.empty(coordArr.shape)
        for n_row in range(4):
            lat,lon = coordArr[n_row,:]
            XY_corners[n_row,:] = proj.transform_point(lon, lat, src_crs)
        Xs = np.linspace(XY_corners[:,0].min(),XY_corners[:,0].max(),Xpixels)
        Ys = np.linspace(XY_corners[:,1].min(),XY_corners[:,1].max(),Ypixels)
        X,Y = np.meshgrid(Xs,Ys)
        lonlat = src_crs.transform_points(proj, X, Y)
        lon = lonlat[..., 0]
        lat = lonlat[..., 1]
        crs_wkt = proj.to_wkt()
        last_bracket_index = crs_wkt.rfind("]")
        min_lat = np.min(lat)
        min_lon = np.min(lon)
        max_lat = np.max(lat)
        max_lon = np.max(lon)
        bbox_str = f"BBOX[{min_lat}, {min_lon}, {max_lat}, {max_lon}]"
        crs_wkt = crs_wkt[:last_bracket_index] + f", {bbox_str}" + crs_wkt[last_bracket_index:]
        crs_attrs = {'spatial_ref':proj.proj4_init,'proj4':proj_str,'crs_wkt':crs_wkt,'grid_mapping_name':'polar_stereographic'}
        return Xs,Ys,lat,lon,crs_attrs

@dataclass
class ConfigBase:
    basedir: str = field(default='/dmidata/archive/arch1/home/radman/products/composite/', metadata={"help": "Base of path to the get new files"})
    version: str = field(default='v0.1.3', metadata={"help": "The version of the new dataset"})
    zarredir: str = field(default='/dmidata/projects/radar/products/composite/zarrComposite/products/', metadata={"help": "Path of the zarr local database"})
    last_date: str = field(default='20251231', metadata={"help": "Date time of the last date recorded in the zarr database"})
    type: str = field(default='max', metadata={"help": "Type of the composite to be extracted, either 'max' or 'near'"})
    sp_resolution: float = field(default=500, metadata={"help": "Spatial resolution of the dataset in meters"})
    x_pixels: int = field(default=1984, metadata={"help": "Number of pixels in the x direction"})
    y_pixels: int = field(default=1728, metadata={"help": "Number of pixels in the y direction"})
    time_resolution: int = field(default=10, metadata={"help": "Time resolution of the dataset in minutes"})
    old_database: str = field(default='', metadata={"help": "Path of the old zarr database"})