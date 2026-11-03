#!/usr/bin/env python3
"""制作実績の画像を軽くするツール(Pillow が必要: pip3 install pillow)

  python3 tools/optimize_images.py            assets/works/ 配下の全案件を処理
  python3 tools/optimize_images.py <slug>     指定した案件だけ処理
  python3 tools/optimize_images.py --dry-run  何が変わるかだけ表示(ファイルは変えない)

案件フォルダに png / jpg を置いてこのツールを実行すると、
  1. webp に変換し、大きすぎる画像は縮小します(横長は幅1600px、縦長は高さ1400px、thumb は幅1200pxまで)
  2. 1枚あたり約150KB以下になるよう画質を自動で調整します(下限は画質60)
  3. work.json の中のファイル名(例: 01.png → 01.webp)も書き換えます
  4. 変換元の png / jpg は削除します(元画像は手元に残しておいてください)
すでに軽い webp は、何もしません(何度実行しても安全です)。
"""
import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow が必要です。  pip3 install pillow  を実行してから、もう一度実行してください。")

ROOT = Path(__file__).resolve().parent.parent
WORKS_DIR = ROOT / "assets" / "works"
MAX_W, MAX_H, THUMB_W = 1600, 1400, 1200
TARGET_KB = 150
SRC_EXT = {".png", ".jpg", ".jpeg"}
dry = "--dry-run" in sys.argv


def encode(im, dst, quality):
    im.save(dst, "WEBP", quality=quality, method=6)
    return dst.stat().st_size / 1024


def optimize_one(path, is_thumb):
    """戻り値: (出力パス, 変更の説明) / 変更不要なら (path, None)"""
    im = Image.open(path)
    im.load()
    w, h = im.size
    limit_w = THUMB_W if is_thumb else MAX_W
    scale = min(1.0, limit_w / w, (1e9 if is_thumb else MAX_H) / h)
    kb = path.stat().st_size / 1024
    needs = path.suffix.lower() in SRC_EXT or scale < 1 or kb > TARGET_KB * 1.3
    if not needs:
        return path, None
    out = path.with_suffix(".webp")
    if dry:
        return out, f"{w}x{h} {kb:.0f}KB → 変換予定"
    rgb = im.convert("RGB")
    if scale < 1:
        rgb = rgb.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    tmp = out.with_name(out.stem + ".tmp.webp")
    q = 82
    while True:
        size = encode(rgb, tmp, q)
        if size <= TARGET_KB or q <= 60:
            break
        q = max(60, q - 6)
    tmp.replace(out)
    if path != out:
        path.unlink()
    return out, f"{w}x{h} {kb:.0f}KB → {rgb.size[0]}x{rgb.size[1]} {size:.0f}KB (画質{q})"


def main():
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    # 案件フォルダ(work.json があるもの)だけが対象。preview/ など他のフォルダには触れない
    dirs = [d for d in sorted(WORKS_DIR.iterdir()) if d.is_dir() and (d / "work.json").exists() and (not only or d.name in only)]
    if only and not dirs:
        sys.exit(f"案件フォルダが見つかりません: {only}")
    total_before = total_after = 0
    for d in dirs:
        renames = {}
        for f in sorted(d.iterdir()):
            if f.suffix.lower() not in SRC_EXT | {".webp"} or f.name.endswith(".tmp.webp"):
                continue
            before = f.stat().st_size
            out, msg = optimize_one(f, f.stem == "thumb")
            if msg:
                print(f"  {d.name}/{f.name}: {msg}")
                if out != f:
                    renames[f.name] = out.name
                if not dry:
                    total_before += before
                    total_after += out.stat().st_size
        wj = d / "work.json"
        if renames and wj.exists() and not dry:
            text = wj.read_text(encoding="utf-8")
            for old, new in renames.items():
                text = text.replace(f'"{old}"', f'"{new}"')
            wj.write_text(text, encoding="utf-8")
    if total_before and not dry:
        print(f"\n合計 {total_before/1048576:.1f}MB → {total_after/1048576:.1f}MB")
    elif not total_before:
        print("変更が必要な画像はありませんでした。" if not dry else "")


if __name__ == "__main__":
    main()
