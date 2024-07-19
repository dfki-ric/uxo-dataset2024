import cv2
import numpy as np
from tqdm import tqdm


def calc_overall_flow(flow):
    # XXX could try using max instead
    dx = np.mean(flow[..., 0])
    dy = np.mean(flow[..., 1])
    return np.linalg.norm((dx, dy))


def calc_optical_flow_farnerback(frame_iterator, flow_params):
    overall_flow = []
    prev_frame = next(frame_iterator)
    
    # Farnerback dense flow
    prev_flow = None        
    for frame in tqdm(frame_iterator):
        flow = cv2.calcOpticalFlowFarneback(prev_frame, frame, None, **flow_params)
        magnitude = calc_overall_flow(flow)
        overall_flow.append(magnitude)
        prev_frame = frame
        prev_flow = flow
    
    return np.array(overall_flow)

def calc_optical_flow_lk(frame_iterator, flow_params, feature_params=None):
    overall_flow = [0.]
    try:
        prev_frame = next(frame_iterator)
    except TypeError:
        frame_iterator = iter(frame_iterator)
        prev_frame = next(frame_iterator)
    
    # Lucas-Kanade sparse flow
    feature_finder_interval = 10
    prev_features = None
    for i,frame in tqdm(enumerate(frame_iterator)):
        # Find good features to match
        if prev_features is None:
            prev_features = cv2.goodFeaturesToTrack(prev_frame, mask=None, **feature_params)
        
        # Still no features? Try with the next frame
        if prev_features is None:
            overall_flow.append(0.)
            prev_frame = frame
            continue
        
        features, status, err = cv2.calcOpticalFlowPyrLK(prev_frame, frame, prev_features, None, **flow_params)
        
        # Tracking failed? We should look for new features next frame
        if not np.any(status == 1):
            overall_flow.append(0.)
            prev_features = None
            prev_frame = frame
            continue
        
        magnitude = calc_overall_flow(features[status == 1] - prev_features[status == 1])
        overall_flow.append(magnitude)
        prev_frame = frame
        if i % feature_finder_interval == 0:
            prev_features = cv2.goodFeaturesToTrack(frame, mask=None, **feature_params)
        else:
            prev_features = features[status == 1].reshape(-1, 1, 2)
        
    return np.array(overall_flow)
