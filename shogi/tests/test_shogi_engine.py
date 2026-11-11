"""USI boundary tests with no engine binary, third-party package or robot."""
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import shogi_engine


class RecordedInput(io.StringIO):
    def close(self):
        self.commands = self.getvalue().splitlines()
        super().close()


class EngineTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.engine-test-', dir=Path(__file__).resolve().parents[2])
        self.addCleanup(self.temp.cleanup)
        self.engine = Path(self.temp.name) / 'engine with spaces' / 'yaneuraou'
        self.engine.parent.mkdir()
        self.engine.touch()
        self.environment = patch.dict(os.environ, {'SHOGI_ENGINE_PATH': str(self.engine)})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.old_eval = os.environ.pop('SHOGI_EVAL_DIR', None)
        self.addCleanup(self.restore_eval)

    def restore_eval(self):
        if self.old_eval is not None:
            os.environ['SHOGI_EVAL_DIR'] = self.old_eval
        else:
            os.environ.pop('SHOGI_EVAL_DIR', None)

    def process(self, response='bestmove 7g7f ponder 3c3d'):
        proc = Mock()
        proc.stdin = RecordedInput()
        proc.stdout = io.StringIO('id name YaneuraOu\nusiok\nreadyok\n' + response + '\n')
        proc.poll.return_value = None
        return proc

    def test_default_path_is_yaneuraou_without_fairy_stockfish_fallback(self):
        with patch.dict(os.environ, {'SHOGI_ENGINE_PATH': ''}):
            location = shogi_engine.engine_path()
        self.assertIn('YaneuraOu', location.parts)
        self.assertEqual(location.name, 'yaneuraou.exe' if os.name == 'nt' else 'yaneuraou')

    def test_configured_binary_working_directory_and_usi_sequence(self):
        evaluation = self.engine.parent / 'evaluation with spaces'
        evaluation.mkdir()
        proc = self.process()
        with patch.dict(os.environ, {'SHOGI_EVAL_DIR': str(evaluation)}), \
                patch.object(shogi_engine.subprocess, 'Popen', return_value=proc) as popen:
            self.assertEqual(shogi_engine.bestmove('start sfen', {'7g7f', '2g2f'}), '7g7f')
        self.assertEqual(popen.call_args.args[0], [str(self.engine.resolve())])
        self.assertEqual(popen.call_args.kwargs['cwd'], str(self.engine.parent.resolve()))
        self.assertFalse(popen.call_args.kwargs.get('shell', False))
        self.assertEqual(proc.stdin.commands, [
            'usi', 'setoption name EvalDir value ' + str(evaluation.resolve()),
            'isready', 'usinewgame', 'position sfen start sfen', 'go movetime 500'])
        self.assertTrue(proc.stdin.closed)
        self.assertTrue(proc.stdout.closed)
        proc.kill.assert_called_once()

    def test_default_evaluation_does_not_override_engine_setting(self):
        proc = self.process()
        with patch.object(shogi_engine.subprocess, 'Popen', return_value=proc):
            shogi_engine.bestmove('sfen', {'7g7f'})
        self.assertFalse(any(line.startswith('setoption') for line in proc.stdin.commands))

    def test_missing_engine_fails_without_launching_any_fallback(self):
        self.engine.unlink()
        with patch.object(shogi_engine.subprocess, 'Popen') as popen:
            with self.assertRaisesRegex(ValueError, 'SHOGI_ENGINE_PATH'):
                shogi_engine.bestmove('sfen', {'7g7f'})
        popen.assert_not_called()

    def test_missing_evaluation_directory_fails_before_starting_engine(self):
        with patch.dict(os.environ, {'SHOGI_EVAL_DIR': str(self.engine.parent / 'missing')}), \
                patch.object(shogi_engine.subprocess, 'Popen') as popen:
            with self.assertRaisesRegex(ValueError, 'SHOGI_EVAL_DIR'):
                shogi_engine.bestmove('sfen', {'7g7f'})
        popen.assert_not_called()

    def test_illegal_move_is_rejected_and_process_is_closed(self):
        proc = self.process('bestmove 9a9b')
        with patch.object(shogi_engine.subprocess, 'Popen', return_value=proc):
            with self.assertRaisesRegex(ValueError, '合法手'):
                shogi_engine.bestmove('sfen', {'7g7f'})
        proc.kill.assert_called_once()
        self.assertTrue(proc.stdout.closed)

    def test_resignation_and_no_move(self):
        for value in ('resign', '(none)', '0000'):
            with self.subTest(value=value):
                with patch.object(shogi_engine.subprocess, 'Popen', return_value=self.process('bestmove ' + value)):
                    self.assertIsNone(shogi_engine.bestmove('sfen', {'7g7f'}))

    def test_early_exit_reports_configuration_error_without_waiting_for_timeout(self):
        proc = self.process('info string evaluation missing')
        with patch.object(shogi_engine.subprocess, 'Popen', return_value=proc):
            with self.assertRaisesRegex(ValueError, '応答前に終了'):
                shogi_engine.bestmove('sfen', {'7g7f'})
        self.assertTrue(proc.stdout.closed)


if __name__ == '__main__':
    unittest.main()
