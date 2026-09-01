from agent_xplat.env import classify_assignment, find_variable_syntax
from agent_xplat.executables import executable_kind
from agent_xplat.line_endings import line_ending_style


def test_support_modules_expose_structured_portability_facts():
    assert classify_assignment("FOO=bar node app.js") == "posix-inline"
    assert classify_assignment("$env:FOO=bar") == "powershell"
    assert classify_assignment("set FOO=bar") == "cmd"
    assert "HOME" in find_variable_syntax("echo $HOME and %USERPROFILE%")
    assert line_ending_style(b"a\r\nb\r\n") == "CRLF"
    assert line_ending_style(b"a\nb\n") == "LF"
    assert executable_kind("python3") == "python"
    assert executable_kind("venv\\Scripts\\python.exe") == "python"
