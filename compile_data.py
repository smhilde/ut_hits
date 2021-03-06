# -*- coding: utf-8 -*-
"""
Code to compile Tulsa football hit data into a DataFrame
"""
from __future__ import print_function, division
import pandas as pd
import numpy as np
import toolz
import copy

#------------#
# FUNCTIONS  #
#------------#
@toolz.curry
def during_practice(practice, hit_date):
    """ 
    during_practice takes a hit_date that is a datetime object and a pandas
    dataframe called practices. practices should have a start and end time for
    the practice session that occurs on a given day.
    """
    # Find day of hit and format as a string
    hit_day = hit_date.date().strftime('%Y-%m-%d')
    # Find the start and end time of the practice of the hit day
    start_time = practice[hit_day].loc[practice.period == 'start'].date
    end_time = practice[hit_day].loc[practice.period == 'end'].date
    if start_time.empty or end_time.empty:
        return False
    # determine if the hit occurred during practice
    return np.logical_and(start_time <= hit_date, hit_date <= end_time).values[0]

@toolz.curry
def during_event(practices, hit):
    return during_practice(practices[hit.ptype], hit.date)

@toolz.curry
def before_break(practice, hit_date):
    # Find day of hit and format as a string
    hit_day = hit_date.date().strftime('%Y-%m-%d')
    # Find the start time of the break period
    break_time = practice[hit_day].loc[practice.period == 'break'].date
    if break_time.empty:
        # If the practice session didn't have a break, by definition all events
        # for that session occurred before the break.
        return True
    # determine if the hit occurred during practice
    return (hit_date <= break_time).values[0]
    
def read_hit_data(filename, skiprows=0, sheet='FINAL- bad hits and 1 out',
                  date_column={'date': [1,2]}): 
    df = pd.read_excel(filename, skiprows=skiprows, sheetname=sheet,
                       parse_dates=date_column)
    df.columns = [col.strip() for col in df.columns]
    df.set_index('date', inplace=True)
    return df

def read_attendance_data(filename, date_column='date'):
    df = pd.read_excel(filename)
    df.columns = [str(col).strip() for col in df.columns]
    df.set_index(date_column, inplace=True)
    return df

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

def read_participation_data(filename, skiprows=None, date_column='date'):
    df = pd.read_excel(filename, skiprows=skiprows, sheetname=None)
    df['offensive']['day'] = df['offensive']['day'].ffill()
    df['offensive']['name'] = df['offensive']['name'].ffill()
    df['offensive'].set_index(date_column, inplace=True)
    df['defensive']['day'] = df['defensive']['day'].ffill()
    df['defensive']['name'] = df['defensive']['name'].ffill()
    df['defensive'].set_index(date_column, inplace=True)
    return df
    
def read_serial_num_to_position(filename, index_col='number'):
    return pd.read_excel(filename).set_index(index_col)

def read_player_types(filename, index_col='type'):
    return pd.read_excel(filename).set_index(index_col)

def read_event_types(filename, index_col='date'):
    return pd.read_excel(filename).set_index(index_col)

def read_game_durations(filename, index_col=0):
    return pd.read_excel(filename, index_col=index_col, header=[0,1])

@toolz.curry
def get_player_type(position_type_df, player_code):
    if not player_code in position_type_df.columns:
        print('Player code not in position type table. Call Seth.')
        raise KeyError
    try: 
        return position_type_df[position_type_df[player_code]==True].index[0]
    except:
        print('Something went wrong while determining player type (offensive or defensive). Call Seth.')
        raise RuntimeError

@toolz.curry    
def get_player_position(positions, player_number):
    return positions.loc[player_number].position

@toolz.curry
def get_player_position_code(positions, player_number):
    return positions.loc[player_number]['code']

@toolz.curry
def get_practice(practices, ptype):
    return practices[ptype]

def get_closest_activity_idx(practice, hit_date):
    # Find the index of the practice activity during which the hit occurred
    return practice.index.get_loc(hit_date, method='pad')

def get_activity_idx(practice, hit_date):
    # Return the activity during which the hit occurred
    activity_idx = get_closest_activity_idx(practice, hit_date)
    act_row = practice.iloc[activity_idx]
    ## Hits shouldn't occur during breaks or the all up activities. Assign hits
    ## during these activities to the activity immediately prior.
    if act_row.period == 'break' or act_row.period == 'all up':
        activity_idx -= 1
        ## NOTE: I could do the above recursively, which may be more robust but
        ##       not strictly necessary since I'm basically looking for the 
        ##       above result.
        #return get_activity(practice, player_code, hit_date-1)
    return activity_idx

@toolz.curry    
def get_activity(practice, pcode, hit_date):
    # Return the activity during which the hit occurred
    activity_idx = get_activity_idx(practice, hit_date)
    return practice.loc[practice.index[activity_idx], pcode]

def get_parti(practice, pcode, hit_date):
    # Return the pcodes of the players that were participating in the event
    # in which the hit occurred
    activity_idx = get_activity_idx(practice, hit_date)
    activity = get_activity(practice, pcode, hit_date)
    return list(practice.columns[practice.iloc[activity_idx] == activity])

@toolz.curry
def get_practice_name(practice, hit_date):
    activity_idx = get_activity_idx(practice, hit_date)
    return practice.loc[practice.index[activity_idx], 'name']

@toolz.curry
def get_event_type(event_df, hit_date):
    return event_df.loc[hit_date.date()].type

def get_num_players(method='by_position', data={}):
    att_df = data['attendance_df']
    pcode = data['pcode']
    hit_date = data['hit_date']
    # Look up number of players
    if method == 'by_position':
        # How many people were playing this position on the hit date?
        return att_df.loc[hit_date.date()][pcode]
    elif method == 'total':
        # How many total people were participating on the hit date?
        att_df = data['df']
        return att_df.loc[hit_date.date()]['total']
    elif method == 'by_activity':
        # How many people were participating in the activity on the hit date?
        # What player codes participated in the activity?
        parti_codes = get_parti(data['practice_df'], pcode, hit_date)
        return att_df.loc[hit_date.date()][parti_codes].sum()
    else:
        raise NotImplementedError

def get_duration(data={}):
    if data['event_type'] == 'game':
        hit_date = data['hit_date']
        game_dur_df = data['game_dur_df']
        ptype = data['ptype']
        activity = data['activity']
        date_mask = [dd.date() == hit_date.date() for dd in game_dur_df.index]
        return game_dur_df.loc[date_mask, (ptype, activity)].iloc[0]
    else:
        durs = data['durations']
        event = data['event']
        prebrk = data['prebreak']
        return durs[np.logical_and(durs.prebreak == prebrk,
                                   durs.name == event)].length.values[0]

def normalize_hits(hit, player_method=None, time_method=None, data={}):
    hit = copy.deepcopy(hit).astype(np.float64)
    if player_method:
        hit = norm_by_players(hit, method=player_method, data=data)
    if time_method:
        hit = norm_by_time(hit, data=data)
    return hit

def norm_by_players(hit, **kwargs):
    num_players = get_num_players(**kwargs)
    if num_players == 0:
        #hit['sum 1'] = np.NAN
        hit['sum 2'] = np.NAN
        hit['sum 3'] = np.NAN
        hit['sum 4'] = np.NAN
        hit['sum 5'] = np.NAN
    else:
        #hit['sum 1'] /= num_players
        hit['sum 2'] /= num_players
        hit['sum 3'] /= num_players
        hit['sum 4'] /= num_players
        hit['sum 5'] /= num_players
    return hit

def norm_by_time(hit, **kwargs):
    duration = get_duration(**kwargs)
    if duration == 0:
        #hit['sum 1'] = np.NAN
        hit['sum 2'] = np.NAN
        hit['sum 3'] = np.NAN
        hit['sum 4'] = np.NAN
        hit['sum 5'] = np.NAN
    else:
        #hit['sum 1'] /= duration
        hit['sum 2'] /= duration
        hit['sum 3'] /= duration
        hit['sum 4'] /= duration
        hit['sum 5'] /= duration
    return hit

def get_hits_out_of_event(input_files):    
    practices = read_practice_data(input_files['practices'])
    psn_to_pcode = read_serial_num_to_position(input_files['psn_to_pcode'])
    pcode_to_ptype = read_player_types(input_files['pcode_to_ptype'])
    
    de = during_event(practices)
    psn_to_ptype = toolz.compose(get_player_type(pcode_to_ptype),
                                 get_player_position_code(psn_to_pcode))
    
    hits = (read_hit_data(input_files['hits'])
             .reset_index()
             .assign(ptype=lambda x: x.Number.apply(psn_to_ptype))
             .assign(in_event=lambda x: x.apply(de, axis=1)))
    hits = hits.drop(hits.columns[range(2, 22)], axis=1)
    hits[hits.in_event == False].to_csv('hits_not_during_events.csv')
    
def get_practice_times_pre_post(practices):
    # Just select the offensive practices - they should be the same
    for p in practices:
        practice = practices[p]
        practice['day'] = [pd.to_datetime(x).date() for x in practice['date']]
        practice['prebreak'] = ['pre' if before_break(practice, x['date'])
                                else 'post'
                                for idx, x in practice.iterrows()]
        (practice.groupby(['name', 'prebreak', 'day'], as_index=False)
            .sum()
            .sort_values(by=['day', 'name', 'prebreak'])
            .to_csv('{}_practice_lengths.csv'.format(p), index=False))
            
def compile_data(input_files, norm_methods=(None, None)):
    hits = read_hit_data(input_files['hits'])
    practices = read_practice_data(input_files['practices'])
    att = read_attendance_data(input_files['attendance'])
    #game_dur = read_game_durations(input_files['game_duration'])
    #duration_data = pd.read_csv('practice_lengths.csv')
    #parti = read_participation_data(input_files['participation'])
    event_df = read_event_types(input_files['event_types'])
    psn_to_pcode = read_serial_num_to_position(input_files['psn_to_pcode'])
    pcode_to_ptype = read_player_types(input_files['pcode_to_ptype'])
    
    results = []
    for hit_date, hit in hits.iterrows():
        # Look up the hit player's position code
        pcode = get_player_position_code(psn_to_pcode, hit.Number)
        # Determine the player type
        player_type = get_player_type(pcode_to_ptype, pcode)
        # Load the correct set of practices
        practice = practices[player_type]
        # Filter the hit out if it doesn't occur during a practice period
        if not during_practice(practice, hit_date):
            continue
        # Look up the hit player's position
        player_position = get_player_position(psn_to_pcode, hit.Number)
        # Look up the event
        event = get_practice_name(practice, hit_date)
        # Look up the event type
        event_type = get_event_type(event_df, hit_date)
        # Look up the activity
        activity = get_activity(practice, pcode, hit_date)
        # Determine pre/post break
        prebreak = 'pre' if before_break(practice, hit_date) else 'post'
        # Normalize the hit data
        data = {'attendance_df': att,
                'practice_df': practice,
                #'game_dur_df': game_dur,
                'pcode': pcode,
                'ptype': player_type,
                'event': event,
                'event_type': event_type,
                'activity': activity,
                'hit': hit,
                'hit_date': hit_date,
                #'durations': duration_data,
                'prebreak': prebreak}
        hit = normalize_hits(hit, *norm_methods, data)
            
        print('Processing hit...\n'+
              '\tHit Date: {}\n'.format(hit_date))
        
        # Add results to list
        results.append({'event': event,
                        'type': event_type,
                        'date': hit_date,
                        'activity': activity,
                        'before_break': prebreak,
                        'player': player_position,
                        'pcode': pcode,
                        'ptype': player_type,
                        #'h1': hit['sum 1'], 
                        'h2': hit['sum 2'], 
                        'h3': hit['sum 3'], 
                        'h4': hit['sum 4'],
                        'h5': hit['sum 5']})        
    return (pd.DataFrame(results)
              .assign(day=lambda x: [pd.to_datetime(y).date() for y in x.date])
              .sort_values(by=['date']))
    
#--------------#
# MAIN PROGRAM #
#--------------#
if __name__ == '__main__':     
    input_files = {'hits': 'Tulsa_HIE_5 minute increments final- corrected 7-10.xlsx',
                   'practices': 'practices.xlsx',
                   'attendance': 'attendance.xlsx',
                   'event_types': 'event_type.xlsx',
                    #'game_duration': 'minutes_per_game.xlsx',
                   'pcode_to_ptype': 'player_code_to_type.xlsx',
                   'psn_to_pcode': 'serial_number_to_position.xlsx'}
    
    compile_data(input_files, norm_methods=(None, None)).to_csv('compiled_raw.csv') 
    #compile_data(input_files, norm_methods=('by_position', None)).to_csv('compiled_by_position.csv')  
    #compile_data(input_files, norm_methods=('by_activity', None)).to_csv('compiled_by_activity.csv')
    #compile_data(input_files, norm_methods=('by_activity', 'by_time')).to_csv('compiled_by_time_activity_test.csv')
