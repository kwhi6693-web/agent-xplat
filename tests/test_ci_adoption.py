"""Exercise the emitted workflow against an unrelated, uninstalled repository."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap

import pytest
from agent_xplat.init import write_ci


def _block(workflow, step_name):
    step = workflow.split('      - name: ' + step_name + '\n', 1)[1].split('\n      - ', 1)[0]
    return textwrap.dedent(step.split('        run: |\n', 1)[1])


@pytest.mark.skipif(os.name == 'nt' or not shutil.which('bash'), reason='emitted consumer job runs on Ubuntu/bash')
def test_generated_scan_gate_and_summary_on_external_repository(tmp_path):
    target = tmp_path / 'target'
    target.mkdir()
    (target / 'SKILL.md').write_text('chmod +x run.sh\n')
    # A target import or installation would create the sentinel and fail.
    trap = "from pathlib import Path\nPath('TARGET_EXECUTED').touch()\nraise RuntimeError('target executed')\n"
    (target / 'sitecustomize.py').write_text(trap)
    (target / 'agent_xplat.py').write_text(trap)
    env = os.environ.copy()
    env.update(PATH=str(Path(sys.executable).parent) + os.pathsep + env['PATH'],
               GIT_AUTHOR_NAME='test', GIT_AUTHOR_EMAIL='test@example.invalid',
               GIT_COMMITTER_NAME='test', GIT_COMMITTER_EMAIL='test@example.invalid',
               GITHUB_OUTPUT=str(tmp_path / 'outputs'), GITHUB_STEP_SUMMARY=str(tmp_path / 'summary'))
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=target, env=env, text=True).strip()
    git('init'); git('add', '.'); git('commit', '-m', 'base')
    env['BASE_SHA'] = git('rev-parse', 'HEAD')
    workflow = write_ci(tmp_path).read_text()
    def run_step(name, **extra):
        return subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', _block(workflow, name)],
                              cwd=tmp_path, env={**env, **extra}, capture_output=True, text=True)
    assert run_step('Scan and preserve gate outcome').returncode == 0
    assert 'exit_code=0' in (tmp_path / 'outputs').read_text()
    assert run_step('Publish readable summary').returncode == 0
    assert 'New Findings' in (tmp_path / 'summary').read_text()
    assert run_step('Enforce portability gate', SCAN_EXIT='0').returncode == 0
    assert run_step('Enforce portability gate', SCAN_EXIT='').returncode == 3
    (target / 'SKILL.md').write_text('chmod +x run.sh\nexport EXTRA=yes\n')
    assert run_step('Scan and preserve gate outcome').returncode == 0
    assert (tmp_path / 'outputs').read_text().splitlines()[-1] == 'exit_code=1'
    assert run_step('Enforce portability gate', SCAN_EXIT='1').returncode == 1
    assert {p.suffix for p in (tmp_path / 'reports').iterdir()} == {'.json', '.markdown', '.sarif'}
    assert not list(tmp_path.rglob('TARGET_EXECUTED'))


def test_init_ci_accepts_only_immutable_tool_refs(tmp_path):
    with pytest.raises(ValueError):
        write_ci(tmp_path, tool_ref='master')
    sha = 'a' * 40
    assert '@' + sha in write_ci(tmp_path, tool_ref=sha).read_text()
