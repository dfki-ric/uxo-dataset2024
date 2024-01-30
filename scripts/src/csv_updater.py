#!/usr/bin/env python
import os
import csv


# I used this script to make some edits in the matching csv files here and there 
# when I noticed I forgot to add some details. It might be useful to you as well!


def basename(s):
    if s.endswith('/'):
        s = s[:-1]
    return os.path.split(s)[-1]

def gopro_sorting_key(filename):
    base = os.path.splitext(basename(filename))[0]
    #prefix = base[:2]   # GX
    chapter = base[2:4]  # 01
    vid = base[4:8]      # 0010
    clip = base[9:11]    # _01
    return f'{vid}{chapter}{clip}'


def update(csv_file, aris_dirs, gopro_files, gantry_files):
    out_file = csv_file + '_new.csv'
    
    with open(csv_file, 'r') as inp:
        reader = csv.DictReader(inp)
        header = list(reader.fieldnames)
        
        with open(out_file, 'w') as out:
            writer = csv.DictWriter(out, header)
            writer.writeheader()
            
            for row in reader:
                if int(row['aris_idx']) < 0:
                    row['aris_file'] = ''
                if int(row['gopro_idx']) < 0:
                    row['gopro_file'] = ''
                if int(row['gantry_idx']) < 0:
                    row['gantry_file'] = ''

                writer.writerow(row)
            

if __name__ == '__main__':
    # XXX
    day = 2
    csv_file = 'matches_day2.csv'
    
    aris_base_dir = f'data/aris/day{day}/'
    gopro_base_dir = f'data/gopro/day{day}/clips_sd/'
    gantry_base_dir = f'data/gantry/day{day}/'
    
    aris_dirs = sorted(os.path.join(aris_base_dir, f) for f in os.listdir(aris_base_dir))
    gopro_files = sorted([os.path.join(gopro_base_dir, f) for f in os.listdir(gopro_base_dir) if f.lower().endswith('.mp4')], key=gopro_sorting_key)
    gantry_files = sorted(os.path.join(gantry_base_dir, f) for f in os.listdir(gantry_base_dir) if f.lower().endswith('.csv') and not 'metadata' in f.lower())
    
    update(csv_file, aris_dirs, gopro_files, gantry_files)
