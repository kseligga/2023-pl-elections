import copy
import math
import pandas as pd
import numpy as np

# przygotowanie pliczkow do wpisania
h = open("sims_okr.csv", "w+")
h.write('okr_num,nazwa,pis,ko,psl,konf,lew,sym_nr' + '\n')
g = open("sims_pl.csv", "w+")
g.write('sym_nr,pis,ko,psl,konf,lew,bs,inni' + '\n')
f = open("sims_okr_poparcie.csv", "w+")
f.write('okr_num,nazwa,pis,ko,psl,konf,lew,sym_nr' + '\n')

# WYBORY 2019 - [pis, ko, psl, konf, lew]
pl_19 = [43.593, 27.397, 8.546, 6.805, 12.560]

# wyniki wg okregow i predykcja na tegoroczne wyniki w okregach
res_19 = pd.read_csv('res_19.csv')
pred_23 = pd.read_csv('predykcja_okregi.csv')

# sondaze zczytane z pliku w excelu
df = pd.read_excel('sondaze.xlsx')

#df = df[6:] # ktore sondaze brac pod uwage
pd.set_option('display.max_columns', None)

n_parties = int((len(list(df.columns))-5)/2)
parties = (list(df.columns))[3:n_parties+3]

# wykluczenie niezdecydowanych
df['N_real'] = df.apply(lambda x: x['N'] - x['N']*x['NIEZDECYDOWANI'], axis=1)

for partia in parties:
    # kolumny PARTIA_n - ilosc glosow oddanych w danym sondazu na partie
    df[partia + '_n'] = df.apply(lambda x: x['N'] * x[partia] if x[partia]!='ND' else 0, axis=1)

    # PARTIA_populacja - potrzebne do wyliczania poparcia dla ugrupowan nie zawsze uwzglednianych
    df[partia + '_populacja'] = df.apply(lambda x: x['N_real'] if x[partia]!='ND' else 0, axis=1)

    # PARTIA_real - poparcie dla partii nie liczac niezdecydowanych
    df[partia + '_real'] = df.apply(lambda x: x[partia+'_n']/x['N_real'] if x[partia]!='ND' else 0, axis=1)

    # PARTIA_var - wariancja probkowa dla partii pomnozona przez N (dla dodania wagi sondazu)
    df[partia + '_var'] = df.apply(lambda x: x[partia + '_real']*(1-x[partia+'_real']) if x[partia]!='ND' else 0, axis=1)

suma_glosow=0
sumy_partii=[['pis','ko','psl','konf','lew'], [0.0]*5]



# symboliczne dodanie do predykcji z ewybory wyniku z poprzednich wyborow, zeby nie bylo remisow ktore psuja przeliczanie
for partia in sumy_partii[0]:
    pred_23[partia] = pred_23[partia]*0.99 + res_19[partia]*0.01

for (_, okreg) in pred_23.iterrows():
    for i in range(len(sumy_partii[0])):
        sumy_partii[1][i] += okreg[str(sumy_partii[0][i])] / 100 * okreg['populacja'] * okreg['frekwencja']
    suma_glosow+=okreg['populacja']*okreg['frekwencja']


poparcie_zokregow = []
for i in range (len(sumy_partii[0])):
    poparcie_zokregow.append(sumy_partii[1][i]/suma_glosow)

pred_23_origin = copy.deepcopy(pred_23)

print(pred_23_origin)
print(sumy_partii)

srednie=[]
odchylenia=[]

sumka=0
for partia in parties:
    n = (df[partia + '_n'].sum())
    total = df[partia + '_populacja'].sum()
    poparcie = n/total
    sumka += poparcie

    std = math.sqrt(df[partia+'_var'].sum() / total)

    srednie.append(poparcie)
    odchylenia.append(std)

# normalizacja
pl_23 = [x/sumka for x in srednie]

# edytujemy poparcie w okregach, tak zeby zsumowalo sie do sredniej ogolnopolskiej z sondazy

def przelicz_okregi(srednie):
    tmppred_23 = copy.deepcopy(pred_23_origin)

    diff = []
    for i in range(len(poparcie_zokregow)):
        diff.append(srednie[i] / poparcie_zokregow[i]/100)

    i = 0

    for partia in sumy_partii[0]:
        tmppred_23[partia] = tmppred_23.apply(lambda x: x[partia] * diff[i], axis=1)
        i += 1
    return tmppred_23



def dhondt(mandaty, lista_wyniki):
    '''
    Zwraca rozklad mandatow wg dHondta
    :param mandaty: liczba mandatow
    :param lista_wyniki: lista wynikow komitetow
    :return: lista liczb mandatow komitetow
    '''
    parties = len(lista_wyniki)  # liczba partii
    all_dhondt = parties * mandaty * [None]
    for i in range(mandaty):
        for j in range(parties):
            all_dhondt[i * parties + j] = lista_wyniki[j] / (i + 1)
    threshold = sorted(all_dhondt)[-(mandaty)]
    lista_mandaty = [0] * parties
    for i in range(len(all_dhondt)):
        if all_dhondt[i] >= threshold:
            lista_mandaty[i % parties] += 1
    return lista_mandaty


print(pl_23)
print(odchylenia)


for sym in range(10000):
    if sym == 0:  # symulacja nr 0 to symulacja dla wynikow rownym wyliczonym srednim z sondazy
        normalized_pl = [100 * sr for sr in pl_23]
        #print("kotek")
    else:
        # losowanko wynikow zgodnie z wyliczonymi srednimi i mozliwymi odchyleniami
        randomized_pl = [abs(np.random.normal(sr, sd)) for sr, sd in zip(pl_23, odchylenia)]
        normalized_pl = [100 * float(i) / sum(randomized_pl) for i in randomized_pl]

    z_progiem = normalized_pl
    g.write(str(sym))

    for i in range(len(normalized_pl)):
        g.write(',' + str(round(normalized_pl[i], 3)))

        # bierzemy pod uwage prog wyborczy
        if normalized_pl[i] < 5 or ((i == 1 or i == 2) and normalized_pl[i] < 8):
            z_progiem[i] = 0
    g.write('\n')

    # jedna symulacja:
    wyniki = przelicz_okregi(z_progiem)
    for (_, okreg) in wyniki.iterrows():
        f.write(str(okreg['num']) + ',' + okreg['nazwa'])
        h.write(str(okreg['num']) + ',' + okreg['nazwa'])

        for partia in sumy_partii[0]:
            f.write(',' + str(round(okreg[partia], 3)))

        mandaty_okr = dhondt(okreg['mandaty'], [okreg['pis'], okreg['ko'], okreg['psl'], okreg['konf'], okreg['lew']])
        if sum(mandaty_okr) != okreg['mandaty']: print('ZESRALO SIE!!!!!')  # zle policzylo cos, tzw dupa debugging
        for i in range(len(mandaty_okr)):
            h.write(',' + str(mandaty_okr[i]))
        h.write(',' + str(sym) + '\n')
        f.write(',' + str(sym) + '\n')
