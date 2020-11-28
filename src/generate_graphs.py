import matplotlib.pyplot as plt
import seaborn as sns
import os
from src.web.core.session import db_session
import pandas as pd

"""
-- celkovy prirustek
select 
    c.infected_date, 
    count(*), 
    (select count(*) from covidcase c2 where c2.infected_date <= c.infected_date) as cum_sum 
from covidcase c 
group by c.infected_date 
order by c.infected_date;



-- graf poctu nakazenych podle vekovych skupin
select 
    c.infected_date,
    (select count(*) from covidcase c2 where c2.age between 0 and 10 and c2.infected_date = c.infected_date) as `0-10`,
    (select count(*) from covidcase c2 where c2.age between 11 and 20 and c2.infected_date = c.infected_date) as `11-20`,
    (select count(*) from covidcase c2 where c2.age between 21 and 30 and c2.infected_date = c.infected_date) as `21-30`,
    (select count(*) from covidcase c2 where c2.age between 31 and 40 and c2.infected_date = c.infected_date) as `31-40`,
    (select count(*) from covidcase c2 where c2.age between 41 and 50 and c2.infected_date = c.infected_date) as `41-50`,
    (select count(*) from covidcase c2 where c2.age between 51 and 60 and c2.infected_date = c.infected_date) as `51-60`,
    (select count(*) from covidcase c2 where c2.age between 61 and 70 and c2.infected_date = c.infected_date) as `61-70`,
    (select count(*) from covidcase c2 where c2.age between 71 and 80 and c2.infected_date = c.infected_date) as `71-80`,
    (select count(*) from covidcase c2 where c2.age between 81 and 90 and c2.infected_date = c.infected_date) as `81-90`,
    (select count(*) from covidcase c2 where c2.age >= 91 and c2.infected_date = c.infected_date) as `91+`,
    count(*)
from covidcase c
group by c.infected_date
order by c.infected_date;

select 
    c.infected_date, 
    (select country.name, count(*) as `cnt` from covidcase 
    join country on country.code = covidcase.country_code 
    where infected_date = '2020-10-27' and country_code not like 'cz' group by country_code having cnt > 0) 
from covidcase c limit 10;

"""

if __name__ == '__main__':
    fig_dir = os.path.join(os.path.dirname(__file__), 'figures')
    sql_connector = 'mysql+pymysql://root:root@127.0.0.1/upa'

    # TODO opravit popis osy X

#
#         labels = ['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81-99', '90+']
#         ranges = {i: [] for i in range(len(labels))}
#         for record in enumerate(q2):
#             for i in range(len(labels)):
#                 ranges[i].append(record[1][f'r{i}'])
#         x = [i+1 for i in range(len(ranges[0]))]
#         for i in range(len(labels)):
#             plt.plot(x, ranges[i], label=labels[i])
#         plt.legend()
#         plt.show()
#
#         fig, ax = plt.subplots(1, 1)
#         for i in range(len(labels)):
#             ax.plot(x, ranges[i], label=labels[i])
#         fig.savefig(os.path.join(fig_dir, 'increase_by_age.png'))
#         plt.close(fig)
#
#         #######################
#         tips = sns.load_dataset("tips")
#         sns.relplot(x="total_bill", y="tip", data=tips)

    q1 = """select
    c.infected_date,
    count(*),
    (select count(*) from covidcase c2 where c2.infected_date <= c.infected_date) as cum_sum
from covidcase c
group by c.infected_date
order by c.infected_date;"""

    # data = pd.read_sql_query(q1, 'mysql+pymysql://root:root@127.0.0.1/upa')
    # data.plot(x='infected_date', y='cum_sum')
    # plt.fill_between(data['infected_date'].values, data['cum_sum'].values, y2=0)
    # plt.savefig(os.path.join(fig_dir, 'cumulative_cases.png'))
    # plt.show()

    q2 = """select 
    c.infected_date,
    (select count(*) from covidcase c2 where c2.age between 0 and 10 and c2.infected_date = c.infected_date) as `0-10`,
    (select count(*) from covidcase c2 where c2.age between 11 and 20 and c2.infected_date = c.infected_date) as `11-20`,
    (select count(*) from covidcase c2 where c2.age between 21 and 30 and c2.infected_date = c.infected_date) as `21-30`,
    (select count(*) from covidcase c2 where c2.age between 31 and 40 and c2.infected_date = c.infected_date) as `31-40`,
    (select count(*) from covidcase c2 where c2.age between 41 and 50 and c2.infected_date = c.infected_date) as `41-50`,
    (select count(*) from covidcase c2 where c2.age between 51 and 60 and c2.infected_date = c.infected_date) as `51-60`,
    (select count(*) from covidcase c2 where c2.age between 61 and 70 and c2.infected_date = c.infected_date) as `61-70`,
    (select count(*) from covidcase c2 where c2.age between 71 and 80 and c2.infected_date = c.infected_date) as `71-80`,
    (select count(*) from covidcase c2 where c2.age >= 81 and c2.infected_date = c.infected_date) as `81+`,
    count(*)
from covidcase c
group by c.infected_date
order by c.infected_date;"""

    labels = ['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81+']
    # data = pd.read_sql_query(q2, sql_connector)
    # for label in labels:
    #     data.plot(x='infected_date', y=label, label=label, c=label)
    # plt.legend()
    # plt.savefig(os.path.join(fig_dir, 'increase_by_age.png'))

    q3 = """select c.infected_date, country.name, count(*) as `total` 
from covidcase c 
join country on country.code = c.country_code 
where c.infected_date between date('2020-10-05') and date('2020-10-15') and country_code not like 'cz' 
group by c.infected_date, c.country_code 
having total > 5 
order by c.infected_date;
"""
    # data = pd.read_sql_query(q3, sql_connector)
    # sns.relplot(data=data, x='infected_date', y='total', hue='name')
    # plt.xticks(rotation='vertical')
    # plt.show()
    # plt.savefig(os.path.join(fig_dir, 'external_country.png'))

    q4 = """select 
    (select (select count(*) from covidcase where age between 0 and 10 and death_date is not null) / count(*) from covidcase where age between 0 and 10) as `0-10`,
    (select (select count(*) from covidcase where age between 11 and 10 and death_date is not null) / count(*) from covidcase where age between 11 and 20) as `11-20`,
    (select (select count(*) from covidcase where age between 21 and 10 and death_date is not null) / count(*) from covidcase where age between 21 and 30) as `21-30`,
    (select (select count(*) from covidcase where age between 31 and 10 and death_date is not null) / count(*) from covidcase where age between 31 and 40) as `31-40`,
    (select (select count(*) from covidcase where age between 41 and 10 and death_date is not null) / count(*) from covidcase where age between 41 and 50) as `41-50`,
    (select (select count(*) from covidcase where age between 51 and 10 and death_date is not null) / count(*) from covidcase where age between 51 and 60) as `51-60`,
    (select (select count(*) from covidcase where age between 61 and 10 and death_date is not null) / count(*) from covidcase where age between 61 and 70) as `61-70`,
    (select (select count(*) from covidcase where age between 71 and 10 and death_date is not null) / count(*) from covidcase where age between 71 and 80) as `71-80`,
    (select (select count(*) from covidcase where age >= 81 and death_date is not null) / count(*) from covidcase where age >= 81) as `81+`;
"""
    # TODO needs test
    # data = pd.read_sql_query(q4, sql_connector)
    # data.plot.hist(orientation='horizontal')
    # plt.show()
    # plt.savefig(os.path.join(fig_dir, 'mortality_by_age.png'))


    q5 = """select 
    c.infected_date as `infected_date`,
    (select count(*) from covidcase where infected_date = c.infected_date and gender = 'm') as `muzi`,
    (select count(*) from covidcase where infected_date = c.infected_date and gender = 'f') as `zeny`,
    count(*)
    from covidcase c
    group by c.infected_date
    order by c.infected_date;
    """

    fig, ax = plt.subplots()
    data = pd.read_sql_query(q5, sql_connector)
    data.plot.bar(x='infected_date', y=['muzi', 'zeny'], label=['Muži', 'Ženy'], color=['g', 'r'])
    plt.xticks(rotation='vertical')

    plt.legend(loc='best')
    plt.show()
    # plt.savefig(os.path.join(fig_dir, 'increase_by_sex.png'))

