"""랜덤프리셋 production driver (confirmed rules 2026-11-11).

python -I produce_random_ranking.py SOURCE PROJECT SCRATCH

PROJECT/story.json  (written by the writer step; schema = story_ja.json):
  source (ignored; SOURCE argument wins), language "ja", upload_title {ja, ko}, title {line1, line2}, title_ko,
  credit|null, play_order [ranks], ranks [in PLAY order: rank, label, emoji, meaning_ko, src_in, src_out, impact_s, crop_y],
  vine_boom [{rank, impact_s}]  (0-2 lower ranks, never rank 1)

Steps (all rules fixed here, not in the story):
  1. validate story against confirmed rules
  2. render_ranking.py with layout.json (title 100px, top-left compact list, past labels 40%)
  3. vine boom via `cpb.exe myinstants_sfx mix` with the channel sound profile (impact frame, 0.5s, -3 dB)
  4. FAAAH via mix_user_sfx.py: 0.6s ending at every rank change, gain 0 dB, original ducked -6 dB
Output: PROJECT/preview.mp4 (+ manifest). Refuses to overwrite.
"""
import hashlib, json, pathlib, shutil, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent          # .../polarranks/production
ANALYSIS = HERE.parent                                 # .../polarranks
PY = sys.executable
CPB = pathlib.Path.home() / ".claude/skills/channel-preset-builder/bin/cpb.exe"
LAYOUT = HERE / "layout_ja_v2.json"
PROFILE = ANALYSIS / "sound-profile.json"
BOOM = {"profile_asset_id": "vine_boom", "asset_sha256": "c4dadbc0b9cd21b1313ec11845a00d9401bc208ae0f59f54a0282b8cb89d56c2",
        "asset_manifest": "sound-analysis/assets/vine-boom-1/4cf1452a471d358b.json", "trim_start": 0.086, "duration": 0.5, "gain_db": -3}
FAAAH = {"file": str(ANALYSIS / "sound-analysis/assets/faaah/c2d10b90385d26fa.mp3"),
         "sha256": "c8b03ff0adacaf75b504b46e505f70af70a76d234cedaeb80eef9ee7ef6d909a",
         "page_url": "https://www.myinstants.com/ko/instant/faaah-63455/", "audio_url": "https://www.myinstants.com/media/sounds/faaah.mp3",
         "rights_status": "unknown", "audition_status": "listened_by_user_2026-11-11"}
FAAAH_LEAD, FAAAH_TRIM, FAAAH_GAIN, FAAAH_DUCK = 0.6, 0.2, 0, -6


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def run(cmd, cwd=None):
    p = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, errors="replace")
    if p.returncode:
        raise SystemExit(f"step failed: {cmd[:3]}\n{p.stdout[-800:]}\n{p.stderr[-1500:]}")
    return p.stdout


def validate(st):
    errs = []
    ranks = st["ranks"]
    nums = [r["rank"] for r in ranks]
    n = len(ranks)
    if not 5 <= n <= 7 or sorted(nums) != list(range(1, n + 1)):
        errs.append("ranks must be 1..N, N 5-7")
    if st.get("play_order") and st["play_order"] != nums:
        errs.append("play_order must equal ranks order")
    if nums[-2:] != [2, 1]:
        errs.append("random order must end 2 -> 1")
    if nums == sorted(nums, reverse=True):
        errs.append("order is a plain countdown; confirmed rule is a shuffled order")
    if st.get("language") != "ja":
        errs.append("language must be ja")
    for r in ranks:
        d = r["src_out"] - r["src_in"]
        if not 2.3 <= d <= 7.8:
            errs.append(f"rank {r['rank']} clip {d:.2f}s outside 2.3-7.8s")
        if not r["src_in"] <= r.get("impact_s", r["src_in"]) <= r["src_out"]:
            errs.append(f"rank {r['rank']} impact outside clip")
        if not r.get("label") or len(r["label"]) > 10 or not r.get("emoji") or not r.get("meaning_ko"):
            errs.append(f"rank {r['rank']} needs label (<=10 chars), emoji, meaning_ko")
    for line in ("line1", "line2"):
        if len("".join(t for t, _ in st["title"][line])) > 9:
            errs.append(f"title {line} over 9 chars (100px must fit 1080px)")
    vb = st.get("vine_boom", [])
    if len(vb) > 2 or any(v["rank"] == 1 for v in vb):
        errs.append("vine_boom: 0-2 cues, never rank 1")
    if errs:
        raise SystemExit("story rejected:\n- " + "\n- ".join(errs))


def main():
    source, project, scratch = (pathlib.Path(a).resolve() for a in sys.argv[1:4])
    final = project / "preview.mp4"
    if final.exists():
        raise SystemExit(f"refusing to overwrite {final}")
    st = json.loads((project / "story.json").read_text(encoding="utf-8"))
    validate(st)
    st["source"] = str(source)
    scratch.mkdir(parents=True, exist_ok=True)
    work = scratch / "render"
    if work.exists():
        shutil.rmtree(work)
    (scratch / "story.resolved.json").write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    run([PY, "-I", HERE / "render_ranking.py", scratch / "story.resolved.json", LAYOUT, work])
    tl = json.loads((work / "timeline.json").read_text(encoding="utf-8"))
    seg = {s["rank"]: s for s in tl["segments"]}

    boom_events = []
    for v in st.get("vine_boom", []):
        s = seg[v["rank"]]
        boom_events.append(dict(BOOM, start=round(s["output_start"] + v["impact_s"] - s["source_in"], 3),
                                reason=f"rank {v['rank']} impact frame (source {v['impact_s']}s)"))
    nosfx, boomed = work / "preview_nosfx.mp4", work / "preview_boom.mp4"
    if boom_events:
        # the channel mixer requires the profile inside the cue-sheet directory: write it there, then move it to scratch
        plan = ANALYSIS / f".cue-{hashlib.sha256(str(project).encode()).hexdigest()[:12]}.json"
        plan.write_text(json.dumps({"channel_url": "https://www.youtube.com/@polarranks", "sound_profile": PROFILE.name,
                                    "events": boom_events}, ensure_ascii=False, indent=1), encoding="utf-8")
        try:
            run([CPB, "myinstants_sfx", "mix", "--video", nosfx, "--plan", plan, "--output", boomed], cwd=ANALYSIS)
        finally:
            shutil.move(str(plan), str(scratch / "sfx-plan.json"))
    else:
        boomed = nosfx

    changes = [s["output_start"] for s in tl["segments"][1:]]
    fa_events = [{"start": round(c - FAAAH_LEAD, 3), "trim_start": FAAAH_TRIM, "duration": FAAAH_LEAD, "gain_db": FAAAH_GAIN,
                  "duck_db": FAAAH_DUCK, "reason": f"before rank change at {c}s"} for c in changes]
    uplan = scratch / "user-sfx-plan.json"
    uplan.write_text(json.dumps({"requested_by": "user-confirmed preset rule 2026-11-11 (not a channel sound)",
                                 "request": "순위 바뀌기 전에 FAAAH 효과음", "asset": FAAAH, "events": fa_events},
                                ensure_ascii=False, indent=1), encoding="utf-8")
    project.mkdir(parents=True, exist_ok=True)
    run([PY, "-I", HERE / "mix_user_sfx.py", uplan, boomed, final])

    manifest = {"preset": "랜덤프리셋 (polarranks random ranking, ja)", "source": str(source), "source_sha256": sha(source),
                "output": final.name, "output_sha256": sha(final), "duration": tl["duration"],
                "play_order": [s["rank"] for s in tl["segments"]], "timeline": tl["segments"],
                "vine_boom": boom_events, "faaah": fa_events,
                "dependencies": {p.name: sha(p) for p in [HERE / "render_ranking.py", HERE / "mix_user_sfx.py", LAYOUT, PROFILE,
                                                          pathlib.Path(__file__)]},
                "audition": "pipeline checks waveform only; preset sounds listened by user 2026-11-11"}
    (project / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"status": "ok", "output": str(final), "duration": tl["duration"]}))


if __name__ == "__main__":
    main()
