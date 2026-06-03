"""Icône pour la barre système."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QIcon, QPainter, QPen, QPixmap


def make_app_icon(size: int = 64) -> QIcon:
    """Génère une icône simple (cercle vert + point central)."""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    margin = size // 8
    p.setPen(QPen(Qt.NoPen))
    p.setBrush(QBrush(Qt.GlobalColor.darkGray))
    p.drawEllipse(margin, margin, size - 2 * margin, size - 2 * margin)
    p.setBrush(QBrush(Qt.GlobalColor.green))
    p.drawEllipse(margin + 4, margin + 4, size - 2 * margin - 8, size - 2 * margin - 8)
    p.setBrush(QBrush(Qt.GlobalColor.white))
    c = size // 2
    p.drawEllipse(c - size // 10, c - size // 10, size // 5, size // 5)
    p.end()
    return QIcon(pix)
