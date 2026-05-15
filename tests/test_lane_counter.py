from src.analytics.lane_counter import LaneCounter


def test_same_vehicle_not_counted_twice_in_same_lane() -> None:
    lanes = {"lane_1": {"points": [[0, 0], [100, 0], [100, 100], [0, 100]]}}
    counter = LaneCounter(lanes)

    counter.update(track_id=1, class_name="car", center=(40, 40))
    counter.update(track_id=1, class_name="car", center=(45, 45))

    assert counter.get_counts()["lane_1"] == 1
    assert counter.get_summary()["total_vehicles"] == 1


def test_different_vehicles_counted_correctly() -> None:
    lanes = {"lane_1": {"points": [[0, 0], [100, 0], [100, 100], [0, 100]]}}
    counter = LaneCounter(lanes)

    counter.update(track_id=1, class_name="car", center=(40, 40))
    counter.update(track_id=2, class_name="truck", center=(50, 50))

    assert counter.get_counts()["lane_1"] == 2
    assert counter.get_summary()["busiest_lane"] == "lane_1"

