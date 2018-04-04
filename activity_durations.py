import pandas as pd

def read_practice_data(filename, skiprows=None, date_column='date'):
    df = pd.read_excel(filename, skiprows=skiprows, sheetname=None)
    df['offensive']['day'] = df['offensive']['day'].ffill()
    df['offensive']['name'] = df['offensive']['name'].ffill()
    df['offensive']['type'] = df['offensive']['type'].ffill()
    df['offensive'].index = df['offensive'][date_column]
    df['defensive']['day'] = df['defensive']['day'].ffill()
    df['defensive']['name'] = df['defensive']['name'].ffill()
    df['defensive']['type'] = df['defensive']['type'].ffill()
    df['defensive'].index = df['defensive'][date_column]
    return df


practices = read_practice_data('practices.xlsx')

### Offensive Practices
po = practices['offensive']
rb = pd.pivot_table(po, values='length', index='name', columns=['qbrb'], aggfunc=np.sum)
ol = pd.pivot_table(po, values='length', index='name', columns=['ot'], aggfunc=np.sum)
wr = pd.pivot_table(po, values='length', index='name', columns=['wr'], aggfunc=np.sum)

# Find the activities that the ols and the wrs have in common
common = set(wr.columns) & set(ol.columns)
for activity in common:
    # Find those instances where the wrs were doing the activity but the ols weren't
    mask = np.logical_and(np.isnan(ol[activity]), ~np.isnan(wr[activity]))
    # Set the ol duration equal to the wr duration for these instances
    ol.loc[mask, activity] = wr.loc[mask, activity]

common = set(ol.columns) & set(rb.columns)
for activity in common:
    # Find those instances where the wrs were doing the activity but the ols weren't
    mask = np.logical_and(np.isnan(rb[activity]), ~np.isnan(ol[activity]))
    # Set the ol duration equal to the wr duration for these instances
    rb.loc[mask, activity] = ol.loc[mask, activity]


# add the columns in ol that aren't in ol to rb
for column in ol.columns:
    if column not in rb.columns:
        rb[column] = ol[column]

# output offensive activity durations
#rb.to_csv('offensive_activity_durations.csv')
offense = rb.copy()

### Defensive Practices
d = practices['defensive']
dt = pd.pivot_table(d, values='length', index='name', columns=['dt'], aggfunc=np.sum)
cb = pd.pivot_table(d, values='length', index='name', columns=['cb'], aggfunc=np.sum)

# Find the activities that the dts and the cbs have in common
common = set(dt.columns) & set(cb.columns)
for activity in common:
    # Find those instances where the cbs were doing the activity but the dts weren't
    mask = np.logical_and(np.isnan(dt[activity]), ~np.isnan(cb[activity]))
    # Set the dt duration equal to the cb duration for these instances
    dt.loc[mask, activity] = cb.loc[mask, activity]

# add the activities in cb that aren't in dt to dt
for column in cb.columns:
    if column not in dt.columns:
        dt[column] = cb[column]

# output offensive activity durations
#dt.to_csv('defensive_activity_durations.csv')
defense = dt.copy()


# create a multiindex for a combined data frame
tuples = list(zip(itertools.cycle(['offensive']), offense.columns)) + list(zip(itertools.cycle(['defensive']), defense.columns))
idx = pd.MultiIndex.from_tuples(tuples)

ref = dict(offensive=offense, defensive=defense)
out = pd.DataFrame(index=offense.index, columns=idx)
for col in out.columns:
    out[col] = ref[col[0]][col[1]]
out.to_csv('activity_durations.csv')
