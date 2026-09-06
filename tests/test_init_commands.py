import json
from pathlib import Path

from agent_xplat.cli import main


def test_init_init_ci_and_badge_are_non_destructive(tmp_path: Path, capsys):
    assert main(["init", str(tmp_path)]) == 0
    assert (tmp_path / ".agent-xplat.yml").exists()
    original = (tmp_path / ".agent-xplat.yml").read_text(encoding="utf-8")
    assert main(["init", str(tmp_path)]) == 2
    assert (tmp_path / ".agent-xplat.yml").read_text(encoding="utf-8") == original
    assert main(["init-ci", str(tmp_path)]) == 0
    workflow = tmp_path / ".github" / "workflows" / "agent-xplat.yml"
    assert workflow.exists()
    text = workflow.read_text(encoding="utf-8")
    assert "ubuntu-latest" in text
    assert "pip install 'agent-xplat==" in text
    assert 'python -I -m agent_xplat' in text
    assert 'security-events: write' not in text
    assert 'pytest' not in text and 'pip install -e' not in text
    assert 'GITHUB_STEP_SUMMARY' in text and '--baseline-only' in text
    assert main(["badge", str(tmp_path)]) == 0
    assert (tmp_path / "agent-xplat-badge.svg").exists()
    assert "Static Checked" in capsys.readouterr().out


def test_runtime_verified_badge_requires_three_os_evidence(tmp_path: Path):
    assert main(["badge", str(tmp_path), "--runtime-verified"]) == 2
    (tmp_path / "agent-xplat-verification.json").write_text(
        '{"status":"VERIFIED","verified_os":["windows","macos","linux"]}\n', encoding="utf-8"
    )
    assert main(["badge", str(tmp_path), "--runtime-verified"]) == 2


def test_badge_scans_and_records_source_evidence(tmp_path):
    (tmp_path / 'SKILL.md').write_text('chmod +x run.sh\n')
    assert main(['badge', str(tmp_path)]) == 0
    data = json.loads((tmp_path / 'agent-xplat-badge.json').read_text())
    assert data['summary']['findings'] > 0
    assert data['summary']['source_identity']['method'] == 'static-inference'
    assert data['verification']['status'] == 'INFERRED'
    assert 'Inference only' in (tmp_path / 'agent-xplat-badge.svg').read_text()


def test_runtime_badge_rejects_stale_and_accepts_bound_evidence(tmp_path):
    import os
    import subprocess
    from agent_xplat import __version__
    env = {**os.environ, 'GIT_AUTHOR_NAME': 'test', 'GIT_AUTHOR_EMAIL': 'test@example.invalid',
           'GIT_COMMITTER_NAME': 'test', 'GIT_COMMITTER_EMAIL': 'test@example.invalid'}
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=tmp_path, env=env, text=True).strip()
    (tmp_path / '.gitignore').write_text('agent-xplat-*.json\nagent-xplat-*.svg\n')
    (tmp_path / 'SKILL.md').write_text('echo ok\n')
    git('init'); git('add', '.'); git('commit', '-m', 'base')
    sha = git('rev-parse', 'HEAD')
    evidence = {'status': 'VERIFIED', 'verified_os': ['windows', 'macos', 'linux'],
                'source_commit': sha, 'tool_version': __version__,
                'runs': [{'os': os_name, 'status': 'VERIFIED', 'exit_code': 0,
                          'source_commit': sha, 'tool_version': __version__,
                          'command': ['python', '-m', 'pytest'], 'evidence_url': 'https://example.invalid/run'}
                         for os_name in ['windows', 'macos', 'linux']]}
    path = tmp_path / 'agent-xplat-verification.json'
    path.write_text(json.dumps(evidence))
    assert main(['badge', str(tmp_path), '--runtime-verified']) == 0
    evidence['source_commit'] = '0' * 40
    path.write_text(json.dumps(evidence))
    assert main(['badge', str(tmp_path), '--runtime-verified']) == 2
