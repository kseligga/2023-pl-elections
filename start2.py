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


def zwroc_mandaty(mandaty_okr, okreg_19, pl_23, okreg23):
    '''
    Wylicza poparcie dla konkretnych okregow i zwraca przydzial mandatow
    :param mandaty_okr: liczba mandatow
    :param okreg_19: lista wynikow w okregu w 2019
    :param pl_23: lista przewidzianych wynikow ogolnopolskich w 2023
    :param okreg23: lista przewidzianych wynikow w okregu w 2023
    '''
    change = [res23 / res19 for res23, res19 in zip(pl_23, pl_19)]

    # waga, z jaka uwzgledniony jest wynik z pliku "predykcja_okregi.csv" - reszta to wyliczenie na podstawie 2019
    waga_predykcji = 0.3

    okreg_23 = [(chng * okr19)*(1-waga_predykcji) + waga_predykcji*okr23 if chng>0 else 0.0 for chng, okr19, okr23 in zip(change, okreg_19, okreg23)]

    for i in range(len(okreg_23)):
        f.write(',' + str(round(okreg_23[i],3)))

    return dhondt(mandaty_okr, okreg_23)


### SYMULACJE ###

# symulacje wyborow z uwzglednionymi odchyleniami w wynikach komitetow
for sym in range(10):

    if sym==0: # symulacja nr 0 to symulacja dla wynikow rownym wyliczonym srednim z sondazy
        normalized_pl = [100 * sr for sr in pl_23]
    else:
        # losowanko wynikow zgodnie z wyliczonymi srednimi i mozliwymi odchyleniami
        randomized_pl = [abs(np.random.normal(sr, sd)) for sr, sd in zip(pl_23, odchylenia)]
        normalized_pl = [100 * float(i) / sum(randomized_pl) for i in randomized_pl]

    z_progiem = normalized_pl
    g.write(str(sym))

    for i in range(len(normalized_pl)):
        g.write(','+str(round(normalized_pl[i],3)))

        # bierzemy pod uwage prog wyborczy
        if normalized_pl[i] < 5 or ((i==1 or i==2) and normalized_pl[i]<8):
            z_progiem[i] = 0
    g.write('\n')

    # jedna symulacja:
    for (index, okreg19),(_, okreg23) in zip(res_19.iterrows(), pred_23.iterrows()):
        okreg = okreg19
        #okr = (okreg19['num'], okreg19['nazwa'],)
        f.write(str(okreg19['num']) + ',' + okreg19['nazwa'])
        h.write(str(okreg19['num']) + ',' + okreg19['nazwa'])

        mandaty_okr = zwroc_mandaty(okreg19['mandaty'],
                                    [okreg19['pis'], okreg19['ko'], okreg19['psl'], okreg19['konf'], okreg19['lew']],
                                    z_progiem,
                                    [okreg23['pis'], okreg23['ko'], okreg23['psl'], okreg23['konf'],okreg23['lew']])

        if sum(mandaty_okr) != okreg19['mandaty']: print('ZESRALO SIE!!!!!') # zle policzylo cos, tzw dupa debugging
        for i in range(len(mandaty_okr)):
            h.write(',' + str(mandaty_okr[i]))

        h.write(',' + str(sym) + '\n')
        f.write(',' + str(sym) + '\n')
