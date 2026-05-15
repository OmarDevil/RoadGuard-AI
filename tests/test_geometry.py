from src.utils.geometry import get_box_center, point_inside_polygon


def test_point_inside_polygon() -> None:
    polygon = [[0, 0], [10, 0], [10, 10], [0, 10]]
    assert point_inside_polygon((5, 5), polygon) is True


def test_point_outside_polygon() -> None:
    polygon = [[0, 0], [10, 0], [10, 10], [0, 10]]
    assert point_inside_polygon((15, 5), polygon) is False


def test_box_center_calculation() -> None:
    assert get_box_center(10, 20, 30, 60) == (20, 40)

