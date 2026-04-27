from __future__ import annotations

from pathlib import Path

from radar_core.exceptions import StorageError
from radar_core.storage import RadarStorage as _CoreRadarStorage


class RadarStorage(_CoreRadarStorage):
    def create_daily_snapshot(self, snapshot_dir: str | None = None) -> Path | None:
        from .date_storage import snapshot_database

        snapshot_root = Path(snapshot_dir) if snapshot_dir else self.db_path.parent / "daily"
        return snapshot_database(self.db_path, snapshot_root=snapshot_root)

    def cleanup_old_snapshots(self, snapshot_dir: str | None = None, keep_days: int = 90) -> int:
        from .date_storage import cleanup_date_directories

        snapshot_root = Path(snapshot_dir) if snapshot_dir else self.db_path.parent / "daily"
        return cleanup_date_directories(snapshot_root, keep_days=keep_days)


__all__ = ["RadarStorage", "StorageError"]
