import math

import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportion_confint

# read by default 1st sheet of an excel file
df = pd.read_excel('sondaze.xlsx')
pd.set_option('display.max_columns', None)

#print(df)

n_parties = int((len(list(df.columns))-5)/2)
parties = (list(df.columns))[3:n_parties+3]
print(parties)

df['N_real'] = df.apply(lambda x: x['N'] - round(x['N']*x['NIEZDECYDOWANI'],0), axis=1)
for partia in parties:
    # kolumny PARTIA_n - ilosc glosow w danym sondazu
    df[partia + '_n'] = df.apply(lambda x: x['N'] * x[partia] if x[partia]!='ND' else 0, axis=1)
    # kolumny PARTIA_populacja - potrzebne do wyliczania dla ugrupowan nie zawsze uwzglednianych
    df[partia + '_populacja'] = df.apply(lambda x: x['N_real'] if x[partia]!='ND' else 0, axis=1)

print(df)
#print(df['N'].sum())


srednie=[]
downs = []
ups = []


summ=0
for partia in parties:
    n = (df[partia + '_n'].sum())
    total = df[partia + '_populacja'].sum()
    poparcie = n/total
    summ+=poparcie
    std = math.sqrt(poparcie*(1-poparcie)/n)
    down, up = proportion_confint(count=n, nobs=total)
    #print(partia, round(poparcie,4), down, up, std)
    srednie.append(poparcie)
    downs.append(down)
    ups.append(up)

print(summ)

srednie_norm = [x/summ for x in srednie]
downs_norm = [x/summ for x in downs]
ups_norm = [x/summ for x in ups]

stds = [(u-d)/4 for d,u in zip(downs_norm, ups_norm)]

print(stds)
print(srednie_norm)



