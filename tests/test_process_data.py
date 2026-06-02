import cv2
import numpy as np

from app.process_data import is_same_droplet, process_frame


def test_is_same_droplet_true():
    prev = (100.0, 10, 10, 30, 40)
    new = (102.0, 10, 10, 35, 40)
    assert is_same_droplet(new, prev, area_ratio=0.05, dim_ratio=0.05, position_threshold=10)


def test_is_same_droplet_false_position():
    prev = (100.0, 10, 10, 30, 40)
    new = (101.0, 10, 10, 50, 40)
    assert not is_same_droplet(new, prev, area_ratio=0.05, dim_ratio=0.05, position_threshold=10)


def test_process_frame_finds_droplet():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(img, (50, 50), 10, (255, 255, 255), -1)
    processed, sizes, positions = process_frame(img)
    assert len(sizes) == 1
    area, w, h = sizes[0]
    assert area > 300
    assert positions[0] == (50, 50)
