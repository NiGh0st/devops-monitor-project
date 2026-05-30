"""Tests for api/metrics.py."""

from api.metrics import get_system_metrics


def test_metrics_keys_present():
    """get_system_metrics() must return all expected keys."""
    data = get_system_metrics()
    required_keys = {
        "cpu_percent",
        "memory_percent",
        "memory_total_gb",
        "memory_used_gb",
        "disk_percent",
        "disk_total_gb",
        "disk_used_gb",
    }
    assert required_keys.issubset(data.keys()), f"Missing keys: {required_keys - data.keys()}"


def test_cpu_range():
    """cpu_percent must be between 0 and 100."""
    data = get_system_metrics()
    assert 0 <= data["cpu_percent"] <= 100, f"cpu_percent out of range: {data['cpu_percent']}"


def test_memory_range():
    """memory_percent must be between 0 and 100."""
    data = get_system_metrics()
    assert 0 <= data["memory_percent"] <= 100


def test_disk_range():
    """disk_percent must be between 0 and 100."""
    data = get_system_metrics()
    assert 0 <= data["disk_percent"] <= 100


def test_memory_gb_positive():
    """Memory totals must be positive numbers."""
    data = get_system_metrics()
    assert data["memory_total_gb"] > 0
    assert data["memory_used_gb"] >= 0
    assert data["memory_used_gb"] <= data["memory_total_gb"]


def test_disk_gb_positive():
    """Disk totals must be positive numbers."""
    data = get_system_metrics()
    assert data["disk_total_gb"] > 0
    assert data["disk_used_gb"] >= 0
    assert data["disk_used_gb"] <= data["disk_total_gb"]


def test_metrics_returns_dict():
    """get_system_metrics() must return a dict."""
    data = get_system_metrics()
    assert isinstance(data, dict)
