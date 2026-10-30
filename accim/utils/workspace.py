# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Cleaning of the files that the simulations write in a folder."""

import fnmatch
import os
import warnings
from os import PathLike
from pathlib import Path
from typing import List, Optional, Union

__all__ = [
    'WorkspaceArtifactCleaner',
]


class WorkspaceArtifactCleaner:
    """Track generated files from a baseline snapshot and safely clean them."""

    def __init__(
            self,
            workspace_root: Union[str, PathLike],
            exclude_dirs: Optional[List[str]] = None,
            include_hidden: bool = False,
    ):
        self.workspace_root = Path(workspace_root).resolve()
        if not self.workspace_root.exists():
            raise FileNotFoundError(f"workspace_root does not exist: {self.workspace_root}")

        self.include_hidden = include_hidden
        self.exclude_dirs = set(exclude_dirs or [
            '.git', '__pycache__', '.ipynb_checkpoints', '.idea', '.pytest_cache',
            '.mypy_cache', '.venv', 'venv'
        ])
        self._baseline_files: set[str] = set()
        self.generated_files: List[str] = []
        self.files_planned_for_deletion: List[str] = []
        self.files_deleted: List[str] = []
        self.generated_files_not_selected_for_deletion: List[str] = []

    def _iter_relative_files(self):
        for root, dirs, files in os.walk(self.workspace_root):
            root_path = Path(root)
            dirs[:] = [
                d for d in dirs
                if d not in self.exclude_dirs and (self.include_hidden or not d.startswith('.'))
            ]
            for name in files:
                if not self.include_hidden and name.startswith('.'):
                    continue
                rel_path = (root_path / name).relative_to(self.workspace_root).as_posix()
                yield rel_path

    def capture_initial_state(self) -> List[str]:
        self._baseline_files = set(self._iter_relative_files())
        return sorted(self._baseline_files)

    def get_current_files(self) -> List[str]:
        return sorted(set(self._iter_relative_files()))

    def get_generated_files(self) -> List[str]:
        if not self._baseline_files:
            raise RuntimeError("Initial state not captured. Call capture_initial_state() first.")
        current = set(self._iter_relative_files())
        self.generated_files = sorted(current - self._baseline_files)
        return self.generated_files

    def print_generated_files(self, max_items: Optional[int] = None) -> List[str]:
        generated = self.get_generated_files()
        print(f"Generated files detected: {len(generated)}")
        shown = generated if max_items is None else generated[:max_items]
        for rel_path in shown:
            print(f" - {rel_path}")
        if max_items is not None and len(generated) > max_items:
            print(f"... and {len(generated) - max_items} more")
        return generated

    def build_deletion_plan(
            self,
            allow_patterns: Optional[List[str]] = None,
            deny_patterns: Optional[List[str]] = None,
    ) -> List[Path]:
        allow_patterns = allow_patterns or []
        deny_patterns = deny_patterns or []
        plan: List[Path] = []

        generated = self.get_generated_files()
        for rel_path in generated:
            if allow_patterns and not any(fnmatch.fnmatch(rel_path, p) for p in allow_patterns):
                continue
            if deny_patterns and any(fnmatch.fnmatch(rel_path, p) for p in deny_patterns):
                continue
            plan.append(self.workspace_root / rel_path)

        self.files_planned_for_deletion = [p.relative_to(self.workspace_root).as_posix() for p in plan]
        planned_set = set(self.files_planned_for_deletion)
        self.generated_files_not_selected_for_deletion = [
            rel for rel in generated if rel not in planned_set
        ]

        if self.generated_files_not_selected_for_deletion:
            warnings.warn(
                "Some generated files are not selected for deletion. "
                f"Count: {len(self.generated_files_not_selected_for_deletion)}",
                UserWarning,
            )

        return plan

    def delete_generated_files(
            self,
            allow_patterns: Optional[List[str]] = None,
            deny_patterns: Optional[List[str]] = None,
            dry_run: bool = True,
            remove_empty_dirs: bool = False,
    ) -> List[str]:
        plan = self.build_deletion_plan(allow_patterns=allow_patterns, deny_patterns=deny_patterns)
        rel_plan = self.files_planned_for_deletion
        print(f"Files {'planned for deletion' if dry_run else 'to delete'}: {len(rel_plan)}")
        for rel_path in rel_plan:
            print(f" - {rel_path}")

        if dry_run:
            print("Dry run enabled. No files were deleted.")
            return rel_plan

        deleted: List[str] = []
        for abs_path in plan:
            if abs_path.exists() and abs_path.is_file():
                abs_path.unlink()
                deleted.append(abs_path.relative_to(self.workspace_root).as_posix())

        self.files_deleted = deleted

        if remove_empty_dirs:
            for root, dirs, _ in os.walk(self.workspace_root, topdown=False):
                root_path = Path(root)
                for d in dirs:
                    if d in self.exclude_dirs:
                        continue
                    try:
                        (root_path / d).rmdir()
                    except OSError:
                        pass

        print(f"Deleted files: {len(deleted)}")
        return deleted
