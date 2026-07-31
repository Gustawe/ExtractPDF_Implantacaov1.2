"""Gera o ícone corporativo do aplicativo em formato ICO."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


NAVY = (1, 0, 66, 255)
WHITE = (255, 255, 255, 255)
LIGHT_BLUE = (205, 218, 244, 255)


def create_icon(output_path: Path) -> None:
    canvas_size = 256
    image = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    drawing = ImageDraw.Draw(image)

    drawing.rounded_rectangle((8, 8, 248, 248), radius=48, fill=NAVY)

    # Folha com dobra discreta.
    drawing.rounded_rectangle((62, 40, 194, 216), radius=12, fill=WHITE)
    drawing.polygon(((156, 40), (194, 78), (156, 78)), fill=LIGHT_BLUE)

    # Grade de planilha, simples o suficiente para permanecer legível em 16 px.
    drawing.rounded_rectangle((80, 102, 176, 184), radius=5, outline=NAVY, width=8)
    drawing.line((80, 130, 176, 130), fill=NAVY, width=6)
    drawing.line((80, 157, 176, 157), fill=NAVY, width=6)
    drawing.line((112, 102, 112, 184), fill=NAVY, width=6)
    drawing.line((144, 102, 144, 184), fill=NAVY, width=6)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(
        output_path,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    create_icon(project_root / "src" / "conversor_folhas" / "resources" / "app.ico")
