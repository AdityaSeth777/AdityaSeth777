import base64
import glob
import io
import os
from xml.sax.saxutils import escape

from PIL import Image, ExifTags, ImageOps

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()  # iPhones default to HEIC — decode those too
except ImportError:
    pass

from glass import THEMES, background_defs, tile_css, FONT_STACK, MONO_STACK

PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "..", "photos", "travel")
WIDTH, HEIGHT = 460, 340
MAX_PHOTOS = 6
MAX_DIM = 640
JPEG_QUALITY = 72


def _exif_caption(img):
    try:
        exif = img._getexif()
        if not exif:
            return None
        tags = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
        parts = []
        if "FocalLength" in tags:
            parts.append(f"{float(tags['FocalLength']):.0f}mm")
        if "FNumber" in tags:
            parts.append(f"f/{float(tags['FNumber']):.1f}")
        if "ExposureTime" in tags:
            et = tags["ExposureTime"]
            parts.append(f"1/{round(1/float(et))}s" if float(et) < 1 else f"{et}s")
        if "ISOSpeedRatings" in tags:
            parts.append(f"ISO{tags['ISOSpeedRatings']}")
        return " · ".join(parts) if parts else None
    except Exception:
        return None


def load_photos():
    extensions = ("*.jpg", "*.jpeg", "*.png", "*.heic", "*.heif", "*.HEIC", "*.JPG")
    paths = sorted(set(
        p for ext in extensions for p in glob.glob(os.path.join(PHOTOS_DIR, ext))
    ))[:MAX_PHOTOS]

    photos = []
    for path in paths:
        try:
            img = Image.open(path)
            caption = _exif_caption(img)
            # Phone photos rely on the EXIF orientation flag rather than
            # rotating the actual pixels — without this, sideways/upside
            # down shots render wrong.
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            img.thumbnail((MAX_DIM, MAX_DIM))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=JPEG_QUALITY)
            data_uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
            photos.append({"src": data_uri, "caption": caption or os.path.basename(path)})
        except Exception as e:
            print(f"skipping {path}: {e}")
    return photos


def build_svg(theme_name, photos):
    t = THEMES[theme_name]

    if not photos:
        body = f"""
        <div class="tile placeholder">
          <div class="label">travel log</div>
          <div class="value">Photos coming soon</div>
          <div class="sub">Drop JPEGs into photos/travel/ to fill this in.</div>
        </div>
        """
        frames_css = ""
    else:
        # Each frame is independently keyframed (opacity + a horizontal
        # slide-in/slide-out) rather than sharing one continuously-translated
        # flex container — a shared giant transform turned out to glitch
        # intermittently under foreignObject + SVG filters, whereas simple
        # per-element opacity/transform keyframes render reliably.
        n = len(photos)

        layers = "".join(
            f"""
            <div class="frame" style="{'' if n == 1 else f'animation-delay: {i * 4}s;'}">
              <img src="{p['src']}" />
              <div class="caption">{escape(p['caption'])}</div>
            </div>
            """
            for i, p in enumerate(photos)
        )
        body = f'<div class="tile photo-tile">{layers}</div>'

        if n == 1:
            # A single photo needs no animation at all.
            frames_css = """
            .frame { position: absolute; inset: 0; opacity: 1; }
            """
        else:
            seconds_per_photo = 4
            total = seconds_per_photo * n
            slot_pct = 100 / n
            ease_pct = (0.4 / total) * 100  # fixed 0.4s fade regardless of slot count

            # Deliberately overlapping windows: this frame stays fully visible
            # until just after the *next* frame has finished fading in, so
            # there's always at least one frame at opacity 1 — no blank gap.
            fade_out_start_pct = slot_pct + ease_pct
            fade_out_end_pct = slot_pct + 2 * ease_pct
            frames_css = f"""
            @keyframes slide-cycle {{
              0% {{ opacity: 0; transform: translateX(28px); }}
              {round(ease_pct, 3)}% {{ opacity: 1; transform: translateX(0); }}
              {round(fade_out_start_pct, 3)}% {{ opacity: 1; transform: translateX(0); }}
              {round(fade_out_end_pct, 3)}% {{ opacity: 0; transform: translateX(-28px); }}
              100% {{ opacity: 0; transform: translateX(-28px); }}
            }}
            .frame {{
              position: absolute; inset: 0;
              opacity: 0;
              animation: slide-cycle {total}s linear infinite;
            }}
            """

        # object-fit: contain (not cover) so mixed portrait/landscape photos
        # never get cropped — any leftover space is transparent, revealing
        # the tile's own glass background instead of a solid letterbox bar.
        frames_css += """
        .frame { background: transparent; }
        .frame img {
          width: 100%; height: 100%;
          object-fit: contain; object-position: center;
          background: transparent;
          display: block;
        }
        """

    html = f"""
    <div xmlns="http://www.w3.org/1999/xhtml" class="wrap">
      <style>
        {tile_css(theme_name)}
        .wrap {{ width: {WIDTH}px; height: {HEIGHT}px; padding: 18px; font-family: {FONT_STACK}; }}
        .tile {{ width: 100%; height: 100%; position: relative; padding: 0; }}
        .photo-tile {{ overflow: hidden; }}
        .caption {{
          position: absolute; left: 0; right: 0; bottom: 0;
          padding: 8px 14px;
          font-family: {MONO_STACK};
          font-size: 11px;
          color: #fff;
          background: linear-gradient(transparent, rgba(0,0,0,0.55));
        }}
        .placeholder {{ align-items: flex-start; justify-content: center; padding: 18px; }}
        .placeholder .value {{ font-size: 18px; font-weight: 600; margin-top: 6px; }}
        .placeholder .sub {{ font-size: 12px; color: {t['muted']}; margin-top: 6px; }}
        {frames_css}
      </style>
      {body}
    </div>
    """

    bg = background_defs(theme_name, WIDTH, HEIGHT, seed=2)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  {bg}
  <foreignObject x="0" y="0" width="{WIDTH}" height="{HEIGHT}">
    {html}
  </foreignObject>
</svg>
"""


def main():
    photos = load_photos()
    for theme_name in ("dark", "light"):
        svg = build_svg(theme_name, photos)
        out = f"photos-{theme_name}.svg"
        with open(out, "w") as f:
            f.write(svg)
        print(f"Wrote {out} ({len(photos)} photos)")


if __name__ == "__main__":
    main()
