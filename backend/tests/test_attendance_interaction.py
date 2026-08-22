from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_attendance_interaction_contract():
    learning = (ROOT / "app" / "routers" / "learning.py").read_text(encoding="utf-8")
    dashboard = (ROOT / "app" / "routers" / "dashboard.py").read_text(encoding="utf-8")
    mobile = (ROOT.parent / "weapp" / "src" / "pages" / "student" / "attendance.vue").read_text(encoding="utf-8")
    assert '@router.post("/attendance/{attendance_id}/status"' in learning
    assert '"subject_id": r.subject_id' in dashboard
    assert '"subject_name": subject_map.get' in dashboard
    assert "['正常', '迟到', '请假', '缺勤', '早退']" in mobile
    assert 'attendance/${record.id}/cancel' in mobile
