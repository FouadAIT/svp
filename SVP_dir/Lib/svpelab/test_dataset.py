import dataset
import os
import pandas as pd
ds = dataset.Dataset()
path = r"C:\OPAL-RT\WorkspaceFOREVERYONE\IEEE_1547_Fast_Functions\models\IEEE_1547_fast_function\ieee_1547_fast_function_sm_source\OpREDHAWKtarget"
filename = "VRT_mat.csv"

ds = pd.read_csv(os.path.join(path,filename))
print(ds.info())
ds.to_csv(filename)