#!/usr/bin/env python
import sys
import os
from random import randint
import yaml
import numpy as np
import cv2


def usage():
    print(f'{sys.argv[0]} <extracted-aris-folder>')


def save_marks(aris_dir, onset, marks):
    basename = os.path.split(aris_dir)[-1]
    with open(os.path.join(aris_dir, basename + '_marks.yaml'), 'w') as f:
        yaml.safe_dump(dict(onset=onset, marks=list(marks)), f)
        
        
def get_marks(aris_dir):
    basename = os.path.split(aris_dir)[-1]
    try:
        with open(os.path.join(aris_dir, basename + '_marks.yaml'), 'r') as f:
            data = yaml.safe_load(f)
            return data.get('onset', -1), data.get('marks', [])
    except FileNotFoundError:
        pass
            
    return -1, []


def view_images(aris_dir):
    basename = os.path.split(aris_dir)[-1]
    color = np.random.randint(0, 256, 3, dtype=np.uint8)
    if np.all(color < 128):
        color += 64
    color = color.tolist()
    images = sorted([os.path.join(aris_dir, f) for f in os.listdir(aris_dir) if f.endswith('.pgm')])
    num_images = len(images)
    idx = 0
    reload = True
    
    onset, marks = get_marks(aris_dir)
    marks = set(marks)
    
    # Read first image, all frames of a recording have the same size
    img = cv2.imread(images[idx])
    h = img.shape[0]
    w = img.shape[1]
    
    cv2.namedWindow('preview', cv2.WINDOW_NORMAL)
    cv2.setWindowTitle('preview', basename)
    
    while True:
        if reload:
            img = cv2.imread(images[idx])
            
            cv2.putText(img, basename,                 (5, 10), cv2.FONT_HERSHEY_SIMPLEX, .3,  color, 1)
            cv2.putText(img, f'Motion onset: {onset}', (5, 20), cv2.FONT_HERSHEY_SIMPLEX, .3, color, 1)
            
            if idx == onset:
                cv2.putText(img, f'{idx} / {num_images} *', (5, 30), cv2.FONT_HERSHEY_SIMPLEX, .3,  color, 1)
            elif idx in marks:
                cv2.putText(img, f'{idx} / {num_images} M', (5, 30), cv2.FONT_HERSHEY_SIMPLEX, .3,  color, 1)
            else:
                cv2.putText(img, f'{idx} / {num_images}', (5, 30), cv2.FONT_HERSHEY_SIMPLEX, .3,  color, 1)
            
            cv2.putText(img, f'arrows: navigate', (5, h-60), cv2.FONT_HERSHEY_SIMPLEX, .3,  color, 1)
            cv2.putText(img, f'enter: save',      (5, h-50), cv2.FONT_HERSHEY_SIMPLEX, .3,  color, 1)
            cv2.putText(img, f'0: set onset',     (5, h-40), cv2.FONT_HERSHEY_SIMPLEX, .3,  color, 1)
            cv2.putText(img, f'm: mark frame',    (5, h-30), cv2.FONT_HERSHEY_SIMPLEX, .3,  color, 1)
            cv2.putText(img, f's: skip',          (5, h-20), cv2.FONT_HERSHEY_SIMPLEX, .3,  color, 1)
            cv2.putText(img, f'q: skip',          (5, h-10), cv2.FONT_HERSHEY_SIMPLEX, .3,  color, 1)
            
        cv2.imshow('preview', img)
        key = cv2.waitKey(1) & 0xFF
        reload = True
        
        # There's a bug in opencv that prevents arrow keys being handled once the user interacted with the window,
        # so we also allow using the numpad. See https://github.com/opencv/opencv/issues/20215
        if key in [81, ord('4')]:
            # left
            idx = (idx - 1) % num_images
        elif key in [83, ord('6')]:
            # right
            idx = (idx + 1) % num_images
        elif key in [82, ord('8')]:
            # up
            idx = (idx + 10) % num_images
        elif key in [84, ord('2')]:
            # down
            idx = (idx - 10) % num_images
        elif key == ord('0'):
            # 0: set onset
            onset = idx
        elif key == ord('m'):
            # m: toggle mark
            if idx == onset:
                continue
            if idx in marks:
                marks.remove(idx)
            else:
                marks.add(idx)
        elif key == 13:
            # enter: save and next folder
            save_marks(aris_dir, onset, marks)
            break
        elif key == ord('s'):
            # s: next folder
            break
        elif key == ord('q'):
            # q: quit
            sys.exit(0)
        else:
            # Reload if any of the buttons we handle is pressed, otherwise don't
            reload = False
        
    print(f'{basename}: onset={onset}, marks={marks}, key={key}')
    

if __name__ == '__main__':
    in_dir_path = sys.argv[1]
    
    for aris_dir in sorted(os.listdir(in_dir_path)):
        view_images(os.path.join(in_dir_path, aris_dir))
