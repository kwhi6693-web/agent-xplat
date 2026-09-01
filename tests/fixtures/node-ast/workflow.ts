import * as cp from "node:child_process";
const output = process.env.OUTPUT;
cp.exec("rm -rf dist");
cp.spawnSync("cmd.exe", ["/c", "echo", "ok"]);
if (process.platform === "win32") {
  cp.spawnSync("powershell.exe");
}
