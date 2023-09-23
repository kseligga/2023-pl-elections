import copy

import pandas as pd
import heapq
import numpy as np

# [pis, ko, lew, psl, konf, mn, inni]
pl_19 = [43.593,27.397,12.560, 8.546,6.805]
pl_23 = [36.9, 30.9, 9.1, 10.2, 11.5]
print(sum(pl_19))

def dhondt(mandaty, lista_wyniki):
    parties = len(lista_wyniki)
    all_dhondt = parties * mandaty * [None]
    for i in range(mandaty):
        for j in range(parties):
            all_dhondt[i * parties + j] = lista_wyniki[j]/(i + 1)
    threshold = sorted(all_dhondt)[-(mandaty)]
    lista_mandaty = [0] * parties
    for i in range(len(all_dhondt)):
        if all_dhondt[i] >= threshold:
            lista_mandaty[i%parties] += 1
    return lista_mandaty

class Okreg:
    __slots__ = ['name', 'num', 'mandaty', 'okreg_19']

    def __init__(self, num, name, mandaty, pis_19, ko_19, lew_19, psl_19, konf_19):
        self.num = num
        self.name = name
        self.mandaty = mandaty
        self.okreg_19 = [pis_19, ko_19, lew_19, psl_19, konf_19]

    def zwroc_mandaty(self, pl_23):
        change = [res23 / res19 for res23, res19 in zip(pl_23, pl_19)]
        okreg_23 = [chng * okr for chng, okr in zip(change, self.okreg_19)]
        print(self.okreg_19)
        print(okreg_23)
        return dhondt(self.mandaty, okreg_23)

res_19 = pd.read_csv('res_19.csv')

mandaty_23 = copy.deepcopy(res_19)
mandaty_23.loc[:,['pis','ko','lew','psl','konf']] = 0

i=0
for index, row in res_19.iterrows():
    i+=1
    okr = Okreg(row['num'], row['nazwa'], row['mandaty'], row['pis'], row['ko'], row['lew'], row['psl'], row['konf'])
    mandaty = okr.zwroc_mandaty(pl_23)
    print(i, mandaty)
