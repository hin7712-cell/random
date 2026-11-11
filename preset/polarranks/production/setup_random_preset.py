"""랜덤프리셋 setup for a new Windows PC.

.venv\\Scripts\\python.exe -I preset\\polarranks\\production\\setup_random_preset.py [--check]

1. checks prerequisites (Windows, Python 3.10+ with numpy/Pillow, ffmpeg, fonts, channel-preset-builder from vendor/채널)
2. rewrites production-binding.json for THIS PC's paths (old one kept as production-binding.prev.json)
3. creates the dedicated skill into build/ (git-ignored) and installs it to ~/.claude/skills/random-preset
It never overwrites an installed skill. The first test production + review + `finalize_skill complete`
is done afterwards by Claude following HANDOFF.md.
"""
import json, os, pathlib, platform, shutil, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
ANALYSIS = HERE.parent
REPO = next(p for p in ANALYSIS.parents if (p / "HANDOFF.md").exists())
HOME = pathlib.Path.home()
CPB = HOME / ".claude/skills/channel-preset-builder/bin/cpb.exe"
INSTALLED = HOME / ".claude/skills/random-preset"
LOCAL_PARENT = REPO / "build"


def fonts():
    need = json.loads((HERE / "layout_ja_v2.json").read_text(encoding="utf-8"))
    paths = {need["title"]["font"], need["list"]["number_font"], need["list"]["label_font"], need["list"]["emoji_font"]}
    return {p: os.path.exists(p) for p in sorted(paths)}


def check():
    res = {
        "windows": platform.system() == "Windows",
        "python_3_10_plus": sys.version_info[:2] >= (3, 10),
        "python": sys.executable,
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "fonts": fonts(),
        "channel_preset_builder": CPB.exists(),
        "random_preset_already_installed": INSTALLED.exists(),
    }
    try:
        import numpy, PIL  # noqa: F401
        res["numpy_pillow"] = True
    except ImportError:
        res["numpy_pillow"] = False
    problems = []
    if not res["windows"]: problems.append("Windows only (cpb.exe, Yu Gothic)")
    if not res["python_3_10_plus"]: problems.append("Python 3.10+ needed (HANDOFF.md step 3: py -3.12 -m venv .venv)")
    if not res["ffmpeg"] or not res["ffprobe"]: problems.append("ffmpeg/ffprobe not on PATH (winget install Gyan.FFmpeg, then open a new terminal)")
    for f, ok in res["fonts"].items():
        if not ok: problems.append(f"font missing: {f} (Pretendard: install 'for all users' so it lands in C:/Windows/Fonts)")
    if not res["channel_preset_builder"]:
        problems.append(f"channel-preset-builder not installed at {CPB.parent.parent} (install from {REPO / 'vendor' / '채널'}, HANDOFF.md step 2)")
    if not res["numpy_pillow"]: problems.append("numpy/Pillow missing: .venv\\Scripts\\python.exe -m pip install -r requirements.txt")
    if res["random_preset_already_installed"]:
        problems.append(f"{INSTALLED} already exists; not overwriting (remove it yourself first if you mean to reinstall)")
    res["problems"] = problems
    return res


def main():
    res = check()
    print(json.dumps(res, ensure_ascii=False, indent=1))
    if "--check" in sys.argv:
        return
    if res["problems"]:
        raise SystemExit("fix the problems above, then run again")
    b = ANALYSIS / "production-binding.json"
    binding = json.loads(b.read_text(encoding="utf-8"))
    shutil.copyfile(b, ANALYSIS / "production-binding.prev.json")
    drv = HERE / "produce_random_ranking.py"
    binding["command"] = [sys.executable, "-I", str(drv), "{source}", "{project}", "{scratch}"]
    binding["dependencies"] = [sys.executable, str(drv), str(HERE / "render_ranking.py"), str(HERE / "mix_user_sfx.py"),
                               str(HERE / "layout_ja_v2.json"), str(ANALYSIS / "sound-profile.json"),
                               str(ANALYSIS / "sound-analysis/assets/vine-boom-1/4cf1452a471d358b.mp3"),
                               str(ANALYSIS / "sound-analysis/assets/faaah/c2d10b90385d26fa.mp3"), str(CPB), res["ffmpeg"]]
    b.write_text(json.dumps(binding, ensure_ascii=False, indent=1), encoding="utf-8")
    LOCAL_PARENT.mkdir(parents=True, exist_ok=True)
    root = LOCAL_PARENT / "random-preset"
    if root.exists():
        raise SystemExit(f"{root} exists; remove it first (it is a local build folder)")
    for cmd in (["create", "--analysis", str(ANALYSIS), "--parent", str(LOCAL_PARENT), "--name", "random-preset", "--title", "랜덤프리셋"],
                ["install", "--skill-root", str(root), "--app", "claude"]):
        p = subprocess.run([str(CPB), "finalize_skill", *cmd], capture_output=True, text=True, errors="replace")
        print(p.stdout.strip())
        if p.returncode:
            raise SystemExit(p.stderr[-1500:])
    print(json.dumps({"status": "installed_pending_test", "skill_root": str(root), "installed": str(INSTALLED),
                      "next": "HANDOFF.md step 5 (test run, review, complete)"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
