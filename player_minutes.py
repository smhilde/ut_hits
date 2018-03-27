#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 26 22:24:13 2018

@author: martin
"""
import pandas as pd

def get_num_players_by_date(att_df, date, option):
    return att_df.loc[date, option]

def get_prepost_duration_by_date(durs, date, pp, option):
    return durs[durs['prebreak']==pp].loc[date, option]

def get_post_duration_by_date(durs, date, option):
    return durs[durs['prebreak']=='post'].loc[date, option]

att_df = read_attendance_data('attendance.xlsx')
durs = pd.read_csv('durations.csv', index_col='day', parse_dates=True)
raw = pd.read_csv('compiled_raw.csv', index_col=0)
raw['day'] = [pd.to_datetime(x).date() for x in raw['date']]
(raw.groupby(['event', 'before_break', 'day'], as_index=False)[['h2', 'h3', 'h4', 'h5']]
    .sum()
    .sort_values(by=['day', 'event', 'before_break'])
    .assign(total_players=lambda x: [get_num_players_by_date(att_df, y.day, 'total') for idx, y in x.iterrows()])
    .assign(def_players=lambda x: [get_num_players_by_date(att_df, y.day, 'defensive') for idx, y in x.iterrows()])
    .assign(off_players=lambda x: [get_num_players_by_date(att_df, y.day, 'offensive') for idx, y in x.iterrows()])
    .assign(def_min=lambda x: [get_prepost_duration_by_date(durs, y.day, y.before_break, 'defensive') for idx, y in x.iterrows()])
    .assign(off_min=lambda x: [get_prepost_duration_by_date(durs, y.day, y.before_break, 'offensive') for idx, y in x.iterrows()])
    .assign(player_min=lambda x: x.def_players*x.def_min + x.off_players*x.off_min)
    .assign(sum24=lambda x: x.h2+x.h3+x.h4)
    .assign(sum34=lambda x: x.h3+x.h4)
    .assign(n2=lambda x: x.h2/x.player_min)
    .assign(n3=lambda x: x.h3/x.player_min)
    .assign(n4=lambda x: x.h4/x.player_min)
    .assign(n5=lambda x: x.h5/x.player_min)
    .assign(n24=lambda x: x.sum24/x.player_min)
    .assign(n34=lambda x: x.sum34/x.player_min)).to_csv('compiled_by_event_time.csv')