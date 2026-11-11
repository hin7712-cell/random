"""Polar Ranks-style ranking renderer (1080x1920 MP4).

python -I render_ranking.py STORY.json LAYOUT.json OUT_DIR

STORY.json
  source: path to source video
  title: {"line1": [[text, color_key], ...], "line2": [[text, color_key], ...]}
  ranks: in PLAY order (6 first). each {rank, label, emoji, src_in, src_out, crop_y}
  credit: optional on-screen credit text (null = none)
LAYOUT.json: measured reference layout scaled to 1080x1920 (see layout.json).

Output: preview_nosfx.mp4 (original audio only), timeline.json, overlays/*.png.
SFX are mixed afterwards with `cpb.exe myinstants_sfx mix` from the channel
sound profile, so this script never adds sounds of its own.
"""
import json, pathlib, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30


def font(path, size):
    return ImageFont.truetype(path, size)


def draw_runs(d, runs, y_center, L, fnt, stroke):
    widths = [d.textlength(t, font=fnt) for t, _ in runs]
    x = (W - sum(widths)) / 2
    for (t, ck), w in zip(runs, widths):
        d.text((x, y_center), t, font=fnt, fill=tuple(L["colors"][ck]), anchor="lm",
               stroke_width=stroke, stroke_fill=(0, 0, 0))
        x += w


def overlay(story, L, revealed, out_png, current=None):
    """current: rank shown now. With list.past_label_opacity < 1, labels of earlier ranks
    (not the numbers) are drawn at that opacity."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    past = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dp = ImageDraw.Draw(past)
    t = L["title"]
    ft = font(t["font"], t["size"])
    draw_runs(d, story["title"]["line1"], t["line1_y_center"], L, ft, t["stroke"])
    draw_runs(d, story["title"]["line2"], t["line2_y_center"], L, ft, t["stroke"])
    lst = L["list"]
    fn = font(lst["number_font"], lst["number_size"])
    fl = font(lst["label_font"], lst["label_size"])
    fe = font(lst["emoji_font"], lst["emoji_size"])
    n = len(story["ranks"])
    for k in range(1, n + 1):
        y = lst["row_y_centers"][k - 1]
        col = tuple(L["colors"][lst["number_colors"].get(str(k), "white")])
        d.text((lst["x"], y), f"{k}.", font=fn, fill=col, anchor="lm", stroke_width=lst["number_stroke"], stroke_fill=(0, 0, 0))
        r = revealed.get(k)
        if r:
            dd = dp if (current is not None and k != current and lst.get("past_label_opacity", 1) < 1) else d
            x = lst["x"] + lst["label_dx"]
            dd.text((x, y), r["label"], font=fl, fill=(255, 255, 255), anchor="lm", stroke_width=lst["label_stroke"], stroke_fill=(0, 0, 0))
            if r.get("emoji"):
                x += dd.textlength(r["label"], font=fl) + lst["emoji_gap"]
                dd.text((x, y), r["emoji"], font=fe, anchor="lm", embedded_color=True)
    op = lst.get("past_label_opacity", 1)
    if op < 1:
        a = past.getchannel("A").point(lambda v: round(v * op))
        past.putalpha(a)
        im = Image.alpha_composite(im, past)
        d = ImageDraw.Draw(im)
    if story.get("credit"):
        c = L["credit"]
        d.text((W / 2, c["y_center"]), story["credit"], font=font(c["font"], c["size"]), fill=(255, 255, 255), anchor="mm",
               stroke_width=c["stroke"], stroke_fill=(0, 0, 0))
    im.save(out_png)


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if p.returncode:
        raise SystemExit(f"ffmpeg failed: {' '.join(cmd[:6])}...\n{p.stderr[-2000:]}")


def main():
    story = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    L = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
    out = pathlib.Path(sys.argv[3]); (out / "overlays").mkdir(parents=True, exist_ok=True); (out / "segments").mkdir(exist_ok=True)
    src = story["source"]
    band = L["video_band"]  # {y0, y1}
    bw, bh = W, band["y1"] - band["y0"]
    sw, sh = L["source_size"]
    cw = sw; ch = round(sw * bh / bw)  # crop window in source px with the band's aspect
    revealed, timeline, t_out, segs = {}, [], 0.0, []
    for i, r in enumerate(story["ranks"]):
        revealed[r["rank"]] = r
        png = out / "overlays" / f"{i:02d}_rank{r['rank']}.png"
        overlay(story, L, dict(revealed), png, current=r["rank"])
        cy = r["crop_y"]
        if cy < 0 or cy + ch > sh:
            raise SystemExit(f"rank {r['rank']}: crop_y {cy} outside 0..{sh - ch}")
        dur = round(r["src_out"] - r["src_in"], 3)
        seg = out / "segments" / f"{i:02d}.mp4"
        vf = (f"[0:v]trim={r['src_in']}:{r['src_out']},setpts=PTS-STARTPTS,crop={cw}:{ch}:0:{cy},scale={bw}:{bh}:flags=lanczos,"
              f"pad={W}:{H}:0:{band['y0']}:black,fps={FPS},format=rgba[v];[v][1:v]overlay=0:0,format=yuv420p[vo];"
              f"[0:a]atrim={r['src_in']}:{r['src_out']},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={max(0, dur - 0.03)}:d=0.03,"
              f"aresample=48000,aformat=channel_layouts=stereo[ao]")
        run(["ffmpeg", "-v", "error", "-y", "-i", src, "-loop", "1", "-i", str(png), "-filter_complex", vf,
             "-map", "[vo]", "-map", "[ao]", "-t", str(dur), "-c:v", "libx264", "-crf", "17", "-preset", "medium",
             "-c:a", "aac", "-b:a", "192k", str(seg)])
        timeline.append({"rank": r["rank"], "label": r["label"], "emoji": r.get("emoji"), "output_start": round(t_out, 3),
                         "output_end": round(t_out + dur, 3), "source_in": r["src_in"], "source_out": r["src_out"],
                         "crop_source_px": [0, cy, cw, ch], "impact_source_s": r.get("impact_s"),
                         "impact_output_s": round(t_out + r["impact_s"] - r["src_in"], 3) if r.get("impact_s") is not None else None,
                         "overlay": png.name})
        t_out += dur
        segs.append(seg)
    lst = out / "segments" / "concat.txt"
    lst.write_text("".join(f"file '{s.resolve().as_posix()}'\n" for s in segs), encoding="utf-8")
    final = out / "preview_nosfx.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:v", "libx264", "-crf", "17",
         "-preset", "medium", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(final)])
    (out / "timeline.json").write_text(json.dumps({"source": src, "output": final.name, "duration": round(t_out, 3),
                                                   "segments": timeline}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"status": "ok", "output": str(final), "duration": round(t_out, 3), "segments": len(timeline)}))


if __name__ == "__main__":
    main()
