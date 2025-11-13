import csv
import os
from collections import deque
import re

def parse_description(desc):
    indicators = {
        'three_points': 0,
        'free_throws': 0,
        'twos': 0,
        'd_reb': 0,
        'o_reb': 0,
        'assist': 0,
        'steal': 0,
        'block': 0,
        'foul': 0,
        'shot_distance': 0,
        'field_goals': 0,
        'efficient_shot': 0,
    }
    desc_lower = desc.lower()
    if 'makes' in desc_lower:
        if 'three point' in desc_lower:
            indicators['three_points'] = 3
            indicators['field_goals'] = 3
            match = re.search(r'(\d+)-foot', desc)
            indicators['shot_distance'] = int(match.group(1)) if match else 23
            if any(word in desc_lower for word in ['layup', 'hook', 'dunk', 'tip', 'put back']):
                indicators['efficient_shot'] = 1
        elif 'free throw' in desc_lower:
            indicators['free_throws'] = 1
        else:
            indicators['twos'] = 2
            indicators['field_goals'] = 2
            match = re.search(r'(\d+)-foot', desc)
            indicators['shot_distance'] = int(match.group(1)) if match else 1
            if any(word in desc_lower for word in ['layup', 'hook', 'dunk', 'tip', 'put back']):
                indicators['efficient_shot'] = 1
    elif 'misses' in desc_lower:
        if 'three point' in desc_lower:
            indicators['three_points'] = 0
            indicators['field_goals'] = 0
            match = re.search(r'(\d+)-foot', desc)
            indicators['shot_distance'] = int(match.group(1)) if match else 23
            indicators['efficient_shot'] = 0
        elif 'free throw' in desc_lower:
            indicators['free_throws'] = 0
        else:
            indicators['twos'] = 0
            indicators['field_goals'] = 0
            match = re.search(r'(\d+)-foot', desc)
            indicators['shot_distance'] = int(match.group(1)) if match else 1
            indicators['efficient_shot'] = 0
    if 'defensive rebound' in desc_lower:
        indicators['d_reb'] = 1
    if 'offensive rebound' in desc_lower:
        indicators['o_reb'] = 1
    if 'assists' in desc_lower:
        indicators['assist'] = 1
    if 'steals' in desc_lower:
        indicators['steal'] = 1
    if 'block' in desc_lower:
        indicators['block'] = 1
    if 'foul' in desc_lower:
        indicators['foul'] = 1
    return indicators

def process_game(file_path):
    filename = os.path.basename(file_path)
    parts = filename.split('_')
    home_team = parts[1].title()
    away_team = parts[2].title()
    home_stats = {
        'events': [],
        'last_fg_points': deque(maxlen=10),
        'totals': {k: 0 for k in ['three_points', 'free_throws', 'twos', 'd_reb', 'o_reb', 'assist', 'steal', 'block', 'foul', 'shot_distance', 'field_goals', 'efficient_shot']}
    }
    away_stats = {
        'events': [],
        'last_fg_points': deque(maxlen=10),
        'totals': {k: 0 for k in ['three_points', 'free_throws', 'twos', 'd_reb', 'o_reb', 'assist', 'steal', 'block', 'foul', 'shot_distance', 'field_goals', 'efficient_shot']}
    }
    with open(file_path, 'r') as f:
        lines = f.readlines()
        header = [h.strip() for h in lines[0].strip().split(',')]
        for line in lines[1:]:
            values = line.strip().split(',')
            row = {k.strip(): v for k, v in zip(header, values)}
            time_str = row['time']
            if not time_str:
                continue
            desc = row['description']
            team = row['team']
            desc_lower = desc.lower()
            if ':' in time_str:
                minutes, seconds = map(int, time_str.split(':'))
                total_seconds = minutes * 60 + seconds
            else:
                total_seconds = float(time_str)
            indicators = parse_description(desc)
            event = {'time': total_seconds, 'indicators': indicators}
            if team == home_team:
                current_stats = home_stats
            else:
                current_stats = away_stats
            current_stats['events'].append(event)
            for k, v in indicators.items():
                current_stats['totals'][k] += v
            if indicators['field_goals'] > 0 or (indicators['field_goals'] == 0 and 'misses' in desc_lower and ('three point' in desc_lower or 'two point' in desc_lower)):
                current_stats['last_fg_points'].append(indicators['field_goals'])
    # Compute level 0 additional
    for stats in [home_stats, away_stats]:
        fg_list = list(stats['last_fg_points'])
        stats['points_last_3_fg'] = sum(fg_list[-3:]) if len(fg_list) >= 3 else sum(fg_list)
        stats['points_last_5_fg'] = sum(fg_list[-5:]) if len(fg_list) >= 5 else sum(fg_list)
        stats['points_last_10_fg'] = sum(fg_list[-10:])
    # Compute level 1
    def compute_rolling(stats, time_window):
        events = stats['events']
        if not events:
            return 0
        cutoff = events[-1]['time'] - time_window * 60
        return sum(e['indicators']['field_goals'] for e in events if e['time'] >= cutoff)
    for stats in [home_stats, away_stats]:
        stats['point_1m'] = compute_rolling(stats, 1)
        stats['point_3m'] = compute_rolling(stats, 3)
        stats['point_5m'] = compute_rolling(stats, 5)
        stats['point_10m'] = compute_rolling(stats, 10)
        # Similarly for others, but for simplicity, only points for now
    return home_team, away_team, home_stats, away_stats

def main():
    directory = '/Users/pranavpenmatcha/ESX/NBAgameDataScraping/NBA 2025 FirstWeek'
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            file_path = os.path.join(directory, filename)
            home_team, away_team, home_stats, away_stats = process_game(file_path)
            print(f"Game: {home_team} vs {away_team}")
            print(f"Home totals: {home_stats['totals']}")
            print(f"Away totals: {away_stats['totals']}")
            print(f"Home points_last_3_fg: {home_stats['points_last_3_fg']}")
            print(f"Away points_last_3_fg: {away_stats['points_last_3_fg']}")
            print(f"Home point_3m: {home_stats['point_3m']}")
            print(f"Away point_3m: {away_stats['point_3m']}")
            print("---")

if __name__ == "__main__":
    main()