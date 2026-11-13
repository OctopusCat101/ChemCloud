from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import workspace


class WorkspaceTests(unittest.TestCase):
    def test_commit_only_changes_explicitly_selected_repository(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first, second = root / 'first', root / 'second'
            (first / '.git').mkdir(parents=True)
            (second / '.git').mkdir(parents=True)
            items = {'first': {'path': first}, 'second': {'path': second}}
            with patch.object(sys, 'argv', ['workspace.py', 'commit', 'first', '-m', 'Fix UI']), \
                 patch.object(workspace, 'projects', return_value=items), \
                 patch.object(workspace, 'git', side_effect=['main', '', ' M ui.c']), \
                 patch.object(subprocess, 'run') as run:
                workspace.main()
            self.assertEqual(len(run.call_args_list), 3)
            self.assertTrue(all(call.kwargs['cwd'] == first for call in run.call_args_list))
            self.assertEqual(run.call_args.args[0], ['git', 'commit', '-m', 'Fix UI'])

    def test_conflicts_stop_entire_batch_before_staging(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            items = {name: {'path': root / name} for name in ('first', 'second')}
            for item in items.values():
                (item['path'] / '.git').mkdir(parents=True)
            with patch.object(sys, 'argv', ['workspace.py', 'commit', 'all', '-m', 'Fix']), \
                 patch.object(workspace, 'projects', return_value=items), \
                 patch.object(workspace, 'git', side_effect=['main', '', 'main', 'conflict.c']), \
                 patch.object(subprocess, 'run') as run:
                with self.assertRaises(ValueError):
                    workspace.main()
            run.assert_not_called()

    def test_push_failure_does_not_push_remaining_projects(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            items = {name: {'path': root / name} for name in ('first', 'second')}
            for item in items.values():
                (item['path'] / '.git').mkdir(parents=True)
            with patch.object(sys, 'argv', ['workspace.py', 'push', 'all']), \
                 patch.object(workspace, 'projects', return_value=items), \
                 patch.object(workspace, 'git', side_effect=['main', '', 'main', '', 'origin', 'main']), \
                 patch.object(workspace, 'network_git', side_effect=subprocess.CalledProcessError(128, 'git')) as push:
                with self.assertRaises(subprocess.CalledProcessError):
                    workspace.main()
            self.assertEqual(push.call_count, 1)
            self.assertEqual(push.call_args.args[0], items['first']['path'])


if __name__ == '__main__':
    unittest.main()
