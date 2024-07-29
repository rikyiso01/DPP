from scripts.kmeans import Point, distance, kmeans, mean
import statistics


def test_kmeans():
    assert {*kmeans([Point(0, 0), Point(1, 1), Point(2, 2)], k=3)} == {0, 1, 2}
    assert {*kmeans([0.0, 1, 2, 3, 4], k=3)} == {0, 1, 2}


def test_mean():
    x: list[float] = [*range(1000)]
    assert mean(x) == statistics.mean(range(1000))


def test_distance():
    assert distance(3.0, 5.0) == 2
    assert distance(Point(0, 0), Point(0, 1)) == 1
