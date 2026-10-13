import numpy as np
import pandas as pd
df = pd.DataFrame({
    'trip' : ["a"]*5 + ["b"] * 5,
    't' : list(range(5))*2,
    'x' : [0, 10, 21, 29, 41, 0, 3, 5, 9, 12], 
    'y' : [0, 1, 0, -1, 0, 5, 5, 6, 5, 5],
})
g = df.groupby('trip')
df['step'] = np.hypot(g['x'].diff(), g['y'].diff())
df['speed'] = df['step'] / g['t'].diff()
print(df)
print(df.groupby('trip')['speed'].agg(['mean', 'std', 'max']))