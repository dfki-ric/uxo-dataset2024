#!/usr/bin/env python3

import numpy as np
from os import path
import yaml

import matplotlib.pyplot as plt
from pytransform3d import rotations as pr
from pytransform3d import transformations as pt
from pytransform3d.transform_manager import TransformManager

def _read_yaml_file(filename):
    file = open(filename, 'r')
    return yaml.safe_load(file)


def _generate_tf_manager(tf_statics, object='setup', tm=None):
    if not tm:
        tm = TransformManager()

    for tf in tf_statics[object]:
        transform = pt.transform_from_pq(
                        np.hstack((
                            np.array([tf['translation']['x'], tf['translation']['y'], tf['translation']['z']]), 
                            np.array([tf['rotation']['w'], tf['rotation']['x'], tf['rotation']['y'], tf['rotation']['z']]))))
        
        tm.add_transform(tf['frame_id'], tf['parent_frame_id'], transform)

    return tm 


def _generate_tf_manager_for_all(tf_statics):
    tm = TransformManager()
    _generate_tf_manager(tf_statics, object='setup', tm=tm)
    _generate_tf_manager(tf_statics, object='targets', tm=tm)
    return tm


def get_tf_manager():
    filename = path.join(path.dirname(path.realpath(__file__)), 'tf_statics.yaml')
    if path.isfile(filename):
        tf_statics = _read_yaml_file(filename)
        tf_manager = _generate_tf_manager_for_all(tf_statics)
        return tf_manager
    else:
        print(f"Tf file '{filename}' not found, returning an empty tf manager")
        return TransformManager()

