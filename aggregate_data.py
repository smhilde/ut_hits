#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 18 21:59:57 2018

@author: martin
"""

import pandas as pd
import numpy as np

df_per_position = pd.read_csv('compile_by_position.csv', index_col=0)
df_per_activity = pd.read_csv('compile_by_activity.csv', index_col=0)
df_per_time = pd.read_csv('compile_by_time.csv', index_col=0)


#games = df[df.type == 'game']
#practices = df[df.type != 'game']
#gtot = tot[tot.type == 'game']
#ptot = tot[tot.type != 'game']

# Question 1: What is the exposure to hits based on player position over all games?
games = df_per_position[df_per_position.type == 'game']
(games.groupby(['practice', 'player'], as_index=False)[['h1', 'h2', 'h3', 'h4', 'h5']]
      .sum()
      .groupby('player')
      .aggregate(np.median))

# Question 2: What is the exposure to hits based on player position over all practices?
practices = df_per_position[df_per_position.type != 'game']
(practices.groupby(['practice', 'player'], as_index=False)[['h1', 'h2', 'h3', 'h4', 'h5']]
          .sum()
          .groupby('player')
          .aggregate(np.median))
          
# Question 3: What is the exposure to hits based on player position be practice type?
practices = df_per_position[df_per_position.type != 'game']
(practices.groupby(['practice', 'type', 'player'], as_index=False)[['h1', 'h2', 'h3', 'h4', 'h5']]
          .sum()
          .groupby(['player', 'type'])
          .aggregate(np.median))         


# Question 4: What is the exposure to hits based on player position by practice activity?
practices = df_per_activity[df_per_activity.type != 'game']
(practices.groupby(['practice', 'activity'], as_index=False)[['h1', 'h2', 'h3', 'h4', 'h5']]
          .sum()
          .groupby(['activity'])
          .aggregate(np.median))

# Question 5a: What is the exposure to hits before and after break across all positions? (practices)
(ptot.groupby(['practice', 'before_break'], as_index=False)[['h1', 'h2', 'h3', 'h4', 'h5']]
     .sum()
     .groupby(['before_break'])
     .aggregate(np.median))

# Question 5b: What is the exposure to hits before and after halftime across all positions? (games)
(gtot.groupby(['practice', 'before_break'], as_index=False)[['h1', 'h2', 'h3', 'h4', 'h5']]
     .sum()
     .groupby(['before_break'])
     .aggregate(np.median))