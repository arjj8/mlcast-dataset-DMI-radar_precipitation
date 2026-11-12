import argparse

from pre_coords import ConfigBase
from numcodecs import Zstd
from extract_data import ExtractData


def main(args):
    config = ConfigBase(**vars(args))
    return ExtractData(pars=config)()


if __name__=="__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--basedir', type=str, help='Base of path to the get new files', default='/dmidata/archive/arch1/home/radman/products/composite/')
    parser.add_argument('--version', type=str, help='The version of the new dataset', default='v0.1.3')
    parser.add_argument('--zarredir', type=str, help='Path of the zarr local database', default='/dmidata/projects/radar/products/composite/zarrComposite/products/')
    parser.add_argument('--last_date', type=str, help='Date time of the last date recorded in the zarr database', default='20251231')
    parser.add_argument('--type', type=str, help='Type of the composite to be extracted, either "max" or "near"', default='max')
    parser.add_argument('--old_database', type=str, help='Path of the old zarr database', default='')

    args = parser.parse_args()
    encoding = {"dbz": {"compressor":Zstd(level=3)}}
    ds = main(args)
    ds.to_zarr(f"{args.zarredir}DMI_10_min_{args.version}.zarr", mode='w', encoding=encoding,consolidated=True,zarr_format="2")



    

    



