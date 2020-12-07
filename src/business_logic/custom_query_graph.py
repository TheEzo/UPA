import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import scipy
import math 
from sqlalchemy import create_engine   

sql_connector = 'mysql+pymysql://root:root@127.0.0.1/upa'

def generate_custom_query(_from='2019-01-01', _to='2022-12-30', tmp=False):
    categories_nb = 10  
    
    infected_class = [list() for i in range(0, categories_nb)]
    dead_class = [0] * categories_nb    

    all_days_count = 0
    all_cases_count = 0 

    means = [None] * categories_nb
    stds = [None] * categories_nb
    meds = [None] * categories_nb   
    dead_func = [None] * categories_nb 

    hist_data = []

    x = [i for i in range(0, categories_nb)]
    bins = [i for i in range(0, categories_nb + 1)] 

    custom_query = f"""
            select  (CASE
                        WHEN age < 11 THEN 0
                        WHEN age > 90 THEN 9
                        ELSE (age-1) DIV 10
                    END) as age,
                    IF(death_date is not null, DATEDIFF(death_date, infected_date), DATEDIFF(recovered_date, infected_date)) as diff, 
                   (death_date is not null) as isdead
            from covidcase 
            where infected_date between "{_from}" and "{_to}" and (death_date is not null or recovered_date is not null)
            """
       
    engine = create_engine(sql_connector)

    with engine.connect() as con:
        for row in con.execute(custom_query):
            infected_class[row[0]].append(row[1])

            if row[2] == 1:
                dead_class[row[0]] = dead_class[row[0]] + 1 
                
            all_days_count = all_days_count + row[1]
            all_cases_count = all_cases_count + 1   

    all_mean = all_days_count / all_cases_count
    all_std = 0 

    for i, n in enumerate(dead_class):
        hist_data.extend([0.5 + 1 * i] * n)

    for cl, cases in enumerate(infected_class):
        means[cl] = np.mean(cases)
        stds[cl] = np.std(cases)
        meds[cl] = np.median(cases) 
        dead_func[cl] = dead_class[cl] / len(cases) 
        
        for case in cases:
            all_std = all_std + (case - all_mean) ** 2

    all_std = math.sqrt(all_std / all_cases_count)
    all_std = [all_std] * categories_nb 
    all_mean = [all_mean] * categories_nb   

    fig, axs = plt.subplots(2, sharex=True)
    fig.set_figheight(10)
    fig.set_figwidth(10)
    fig.suptitle('Vliv věku na délku nemoci a úmrtnost')  

    axs[0].set_title('Závislost věkové kategorie infikovaných na délce nemoci')
    axs[0].set(ylabel='Délka nemoci')   
    axs[0].tick_params(top=False, bottom=True, left=True, right=False, labelbottom=True)    

    axs[0].plot(x, means, label='Střední hodnota kategorie')
    axs[0].plot(x, stds, label='Směrodatná odchylka kategorie')
    axs[0].plot(x, meds, label='Medián kategorie') 
    axs[0].plot(x, all_std, linestyle='dashed', label='Směrodatná odchylka')
    axs[0].plot(x, all_mean, linestyle='dashed', label='Střední hodnota')

    axs[0].legend()
    
    axs[1].set_title('Závislost věkové kategorie infikovaných na počtu úmrtí')
    axs[1].set_xticks(x) 
    axs[1].set_xticklabels(('0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81-90', '91+'))
    axs[1].set(ylabel='Počet úmrtí')
    axs[1].set(xlabel='Věková kategorie')
    
    arr = axs[1].hist(hist_data, bins, density=True, align='left')  

    for i in x:
        axs[1].text(arr[1][i] - 0.3, arr[0][i] + 0.005, str(dead_class[i])) 

    axs[1].plot(x, dead_func, label='Úmrtnost kategorie')

    axs[1].legend(loc='upper left') 

    prefix = 'tmp_' if tmp is True else ''
    fig.savefig(f'{prefix}custom_query.png')