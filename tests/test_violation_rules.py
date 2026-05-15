from src.violations.pedestrian_violation import detect_pedestrian_violation
from src.violations.wrong_way import detect_wrong_way


def test_wrong_way_true_for_opposite_movement() -> None:
    points = [(100, 300), (100, 250), (100, 200)]
    result = detect_wrong_way(points, expected_direction="down", min_movement=40)
    assert result["is_violation"] is True


def test_wrong_way_false_for_correct_movement() -> None:
    points = [(100, 200), (100, 250), (100, 300)]
    result = detect_wrong_way(points, expected_direction="down", min_movement=40)
    assert result["is_violation"] is False


def test_pedestrian_violation_outside_crosswalk() -> None:
    road_zone = [[0, 0], [200, 0], [200, 200], [0, 200]]
    crosswalk_zone = [[50, 50], [150, 50], [150, 100], [50, 100]]
    result = detect_pedestrian_violation((20, 20), road_zone, crosswalk_zone)
    assert result["is_violation"] is True


def test_pedestrian_no_violation_inside_crosswalk() -> None:
    road_zone = [[0, 0], [200, 0], [200, 200], [0, 200]]
    crosswalk_zone = [[50, 50], [150, 50], [150, 100], [50, 100]]
    result = detect_pedestrian_violation((75, 75), road_zone, crosswalk_zone)
    assert result["is_violation"] is False

