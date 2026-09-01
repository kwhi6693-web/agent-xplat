import * as cp from "node:child_process";

if (process.platform === "win32") {
  cp.spawnSync("powershell.exe");
} else {
  cp.spawnSync("bash", ["-lc", "echo ok"]);
}
