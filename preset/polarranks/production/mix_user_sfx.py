"""Mix user-requested (non-channel) SFX cues onto a finished MP4.

python -I mix_user_sfx.py PLAN.json IN.mp4 OUT.mp4

The channel mixer (cpb myinstants_sfx mix) only accepts sounds observed in the
reference channel. Sounds the user explicitly asked for, which the channel
does not use, are mixed here instead and recorded as user requests.

PLAN.json: {"requested_by": "...", "request": "...", "asset": {"file", "sha256", "page_url"},
            "events": [{"start", "trim_start", "duration", "gain_db", "reason"}]}
Video is stream-copied; only audio is re-encoded. Refuses to overwrite OUT.
"""
import hashlib, json, pathlib, subprocess, sys


def main():
    plan = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    src, out = sys.argv[2], pathlib.Path(sys.argv[3])
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    a = plan["asset"]
    if hashlib.sha256(open(a["file"], "rb").read()).hexdigest() != a["sha256"]:
        raise SystemExit("asset hash mismatch")
    ev = plan["events"]
    if not 1 <= len(ev) <= 12:
        raise SystemExit("1-12 events")
    args = ["ffmpeg", "-v", "error", "-i", src]
    # optional ducking of the existing mix under each cue (event["duck_db"] < 0)
    duck = [f"volume={e['duck_db']}dB:enable='between(t,{e['start']},{e['start'] + e['duration']})'"
            for e in ev if e.get("duck_db", 0) < 0]
    parts, labels = [f"[0:a]{','.join(duck) if duck else 'anull'}[base]"], ["[base]"]
    for i, e in enumerate(ev):
        if e["duration"] <= 0 or e["duration"] > 10 or e["start"] < 0 or e["gain_db"] > 0:
            raise SystemExit(f"bad event {i}")
        args += ["-i", a["file"]]
        d = int(round(e["start"] * 1000))
        parts.append(f"[{i + 1}:a]atrim={e['trim_start']}:{e['trim_start'] + e['duration']},asetpts=PTS-STARTPTS,"
                     f"afade=t=out:st={max(0, e['duration'] - 0.08)}:d=0.08,aresample=48000,aformat=channel_layouts=stereo,"
                     f"volume={e['gain_db']}dB,adelay={d}|{d}[s{i}]")
        labels.append(f"[s{i}]")
    fc = ";".join(parts) + f";{''.join(labels)}amix=inputs={len(labels)}:duration=first:normalize=0,volume=-2dB,alimiter=limit=0.89:level=false[a]"
    args += ["-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-movflags", "+faststart", str(out)]
    p = subprocess.run(args, capture_output=True, text=True, errors="replace")
    if p.returncode:
        raise SystemExit(p.stderr[-1500:])
    log = dict(plan, input=src, output=str(out), output_sha256=hashlib.sha256(out.read_bytes()).hexdigest())
    out.with_suffix(".usersfx.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"status": "ok", "output": str(out), "events": len(ev)}))


if __name__ == "__main__":
    main()
