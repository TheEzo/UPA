import matplotlib.pyplot as plt
import seaborn as sns
import os
import pandas as pd
import numpy as np


def generate(_from='2019-01-01', _to='2022-12-30', tmp=False):
    fig_dir = os.path.join(os.path.dirname(__file__), 'web', 'static')
    sql_connector = 'mysql+pymysql://root:root@127.0.0.1/upa'

    ext = 'tmp_' if tmp else ''

    q1 = f"""select
        c.infected_date,
        count(*),
        (select count(*) from covidcase c2 where c2.infected_date <= c.infected_date) as cum_sum
    from covidcase c
    where c.infected_date between DATE("{_from}") and DATE("{_to}")
    group by c.infected_date
    order by c.infected_date;"""

    fig, ax = plt.subplots()
    data = pd.read_sql_query(q1, 'mysql+pymysql://root:root@127.0.0.1/upa')
    ax = data.plot(ax=ax, x='infected_date', y='cum_sum', label='Kumulativní počet')
    plt.fill_between(data['infected_date'].values, data['cum_sum'].values, y2=0)
    plt.xticks(rotation='vertical')
    plt.legend().remove()
    ax.set_xlabel('')
    # plt.show()
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, f'{ext}cumulative_cases.png'))

    q2 = f"""select 
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
    where c.infected_date between "{_from}" and "{_to}"
    group by c.infected_date
    order by c.infected_date;"""

    labels = ['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81+']
    fig, ax = plt.subplots()
    data = pd.read_sql_query(q2, sql_connector)
    for label in labels:
        ax = data.plot(ax=ax, x='infected_date', y=label, label=label)
    plt.legend()
    ax.set_xlabel('')
    plt.xticks(rotation='vertical')
    # plt.show()
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, f'{ext}increase_by_age.png'))

    q3 = f"""select c.infected_date, country.name, count(*) as `total` 
    from covidcase c 
    join country on country.code = c.country_code 
    where country_code not like 'cz' and c.infected_date between "{_from}" and "{_to}"
    group by c.infected_date, c.country_code 
    having total >= 10
    order by c.infected_date;
    """
    data = pd.read_sql_query(q3, sql_connector)
    g = sns.relplot(data=data, x='infected_date', y='total', hue='name')
    g.legend.remove()
    g.set_xlabels('')
    g.set_ylabels('')
    plt.xticks(rotation='vertical')
    plt.legend(bbox_to_anchor=(1.0, 1.))
    # plt.show()
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, f'{ext}external_country.png'))

    q4 = f"""select
        (select count(*) from covidcase where age between 0 and 10 and death_date is not null and infected_date between "{_from}" and "{_to}") as `0-10`,
        (select count(*) from covidcase where age between 11 and 20 and death_date is not null and infected_date between "{_from}" and "{_to}") as `11-20`,
        (select count(*) from covidcase where age between 21 and 30 and death_date is not null and infected_date between "{_from}" and "{_to}") as `21-30`,
        (select count(*) from covidcase where age between 31 and 40 and death_date is not null and infected_date between "{_from}" and "{_to}") as `31-40`,
        (select count(*) from covidcase where age between 41 and 50 and death_date is not null and infected_date between "{_from}" and "{_to}") as `41-50`,
        (select count(*) from covidcase where age between 51 and 60 and death_date is not null and infected_date between "{_from}" and "{_to}") as `51-60`,
        (select count(*) from covidcase where age between 61 and 70 and death_date is not null and infected_date between "{_from}" and "{_to}") as `61-70`,
        (select count(*) from covidcase where age between 71 and 80 and death_date is not null and infected_date between "{_from}" and "{_to}") as `71-80`,
        (select count(*) from covidcase where age >= 81 and death_date is not null and infected_date between "{_from}" and "{_to}") as `81+`;
    """

    fig, ax = plt.subplots()
    data = pd.read_sql_query(q4, sql_connector)
    y_pos = np.arange(len(labels))
    ax.barh(y_pos, data.values[0], color='grey')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    # plt.show()
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, f'{ext}mortality_by_age.png'))

    q5 = f"""select
        c.infected_date as `infected_date`,
        (select count(*) from covidcase where infected_date = c.infected_date and gender = 'm' and death_date is not null) as `muzi`,
        (select count(*) from covidcase where infected_date = c.infected_date and gender = 'f' and death_date is not null) as `zeny`,
        count(*)
        from covidcase c
        where c.infected_date between "{_from}" and "{_to}"
        group by c.infected_date
        order by c.infected_date;
        """

    fig, ax = plt.subplots()
    data = pd.read_sql_query(q5, sql_connector)
    for col, label, c, a, w in [('muzi', 'Muži', 'g', 0.5, 3), ('zeny', 'Ženy', 'r', 1, 1)]:
        ax = data.plot(ax=ax, x='infected_date', label=label, color=c, y=col, alpha=a, linewidth=w)
    plt.xticks(rotation='vertical')
    plt.legend(loc='best')
    plt.tight_layout()
    # plt.show()
    plt.savefig(os.path.join(fig_dir, f'{ext}mortality_by_sex.png'))

    q6 = f"""select
            c.infected_date,
            count(*),
            (select count(*) from covidcase c2 where c2.infected_date <= c.infected_date and death_date is not null) as cum_sum
        from covidcase c
        where c.infected_date between DATE("{_from}") and DATE("{_to}")
        group by c.infected_date
        order by c.infected_date;"""

    fig, ax = plt.subplots()
    data = pd.read_sql_query(q6, 'mysql+pymysql://root:root@127.0.0.1/upa')
    ax = data.plot(ax=ax, x='infected_date', y='cum_sum', label='Kumulativní počet', color='grey')
    plt.fill_between(data['infected_date'].values, data['cum_sum'].values, y2=0, color='grey')
    plt.xticks(rotation='vertical')
    plt.legend().remove()
    ax.set_xlabel('')
    # plt.show()
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, f'{ext}cumulative_deaths.png'))

    x = []
    y = []
    z = []

    rows = []

    custom_query = f"""
            select  (CASE
                        WHEN age < 11 THEN 0
                        WHEN age > 80 THEN 8
                        ELSE (age-1) DIV 10
                    END) as age,
                    IF(death_date is not null, DATEDIFF(death_date, infected_date), DATEDIFF(recovered_date, infected_date)) as diff, 
                   (death_date is not null) as isdead
            from covidcase 
            where infected_date between "{_from}" and "{_to}" and (death_date is not null or recovered_date is not null)
            """
    
    from sqlalchemy import create_engine

    engine = create_engine(sql_connector)
    with engine.connect() as con:
        for row in con.execute(custom_query):
            # rows.append(row)
            x.append(row[0])
            y.append(row[1] // 6)
            z.append(row[2])
if __name__ == '__main__':
    generate()
