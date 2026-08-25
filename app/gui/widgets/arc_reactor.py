"""Futuristic Animated Arc Reactor / Holographic AI Visualizer for JARVIS HUD."""

import math
from PySide6.QtCore import QPointF, QRectF, QTimer, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget


class ArcReactorWidget(QWidget):
    """Futuristic Iron Man / JARVIS Arc Reactor HUD visualizer."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(240, 240)
        self.angle1 = 0.0
        self.angle2 = 0.0
        self.angle3 = 0.0
        self.pulse = 0.0
        self.pulse_dir = 1
        self.status = "ONLINE"  # ONLINE, LISTENING, THINKING, SPEAKING
        self.status_detail = "JARVIS AI CORE"

        # Smooth 30 FPS Animation Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_step)
        self.timer.start(33)

    def set_state(self, status: str, detail: str = "") -> None:
        """Update reactor status: ONLINE, LISTENING, THINKING, SPEAKING."""
        self.status = status.upper()
        if detail:
            self.status_detail = detail
        self.update()

    def _animate_step(self) -> None:
        speed_mult = 2.5 if self.status in ("THINKING", "LISTENING") else 1.0
        self.angle1 = (self.angle1 + 1.2 * speed_mult) % 360
        self.angle2 = (self.angle2 - 0.8 * speed_mult) % 360
        self.angle3 = (self.angle3 + 2.0 * speed_mult) % 360

        # Pulse effect
        self.pulse += 0.04 * self.pulse_dir * speed_mult
        if self.pulse > 1.0:
            self.pulse = 1.0
            self.pulse_dir = -1
        elif self.pulse < 0.0:
            self.pulse = 0.0
            self.pulse_dir = 1

        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        radius = min(w, h) / 2.0 - 12

        # Base Glow Colors based on state
        if self.status == "LISTENING":
            neon_cyan = QColor(0, 255, 200, 240)
            glow_color = QColor(0, 255, 170, 80)
            status_text_color = QColor(0, 255, 200)
        elif self.status == "THINKING":
            neon_cyan = QColor(0, 210, 255, 240)
            glow_color = QColor(112, 0, 255, 90)
            status_text_color = QColor(56, 189, 248)
        elif self.status == "SPEAKING":
            neon_cyan = QColor(0, 180, 255, 255)
            glow_color = QColor(0, 150, 255, 110)
            status_text_color = QColor(96, 165, 250)
        else:
            neon_cyan = QColor(0, 230, 255, 220)
            glow_color = QColor(0, 160, 255, 50)
            status_text_color = QColor(56, 189, 248)

        # 1. Background radial energy field
        bg_grad = QRadialGradient(cx, cy, radius * 1.1)
        bg_grad.setColorAt(0.0, QColor(0, 150, 255, 30 + int(self.pulse * 25)))
        bg_grad.setColorAt(0.7, QColor(0, 40, 80, 20))
        bg_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(bg_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), radius * 1.05, radius * 1.05)

        # 2. Outer Static HUD Ring
        pen_outer = QPen(QColor(0, 180, 255, 70), 1.5, Qt.DashLine)
        painter.setPen(pen_outer)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # 3. Outer Segmented Rotating Ring (Angle 1)
        pen_arc1 = QPen(neon_cyan, 2.5)
        painter.setPen(pen_arc1)
        arc_rect1 = QRectF(cx - radius * 0.92, cy - radius * 0.92, radius * 1.84, radius * 1.84)
        for i in range(4):
            start_ang = int((self.angle1 + i * 90) * 16)
            span_ang = int(55 * 16)
            painter.drawArc(arc_rect1, start_ang, span_ang)

        # 4. Tick Marks Circle
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle2)
        painter.setPen(QPen(QColor(0, 200, 255, 120), 1.5))
        num_ticks = 24
        tick_r_out = radius * 0.84
        tick_r_in = radius * 0.77
        for i in range(num_ticks):
            if i % 3 == 0:
                painter.drawLine(0, -int(tick_r_out), 0, -int(tick_r_in - 3))
            else:
                painter.drawLine(0, -int(tick_r_out), 0, -int(tick_r_in))
            painter.rotate(360 / num_ticks)
        painter.restore()

        # 5. Inner Counter-Rotating Hex / Segmented Ring (Angle 2)
        pen_arc2 = QPen(QColor(0, 150, 255, 180), 2.0)
        painter.setPen(pen_arc2)
        arc_rect2 = QRectF(cx - radius * 0.68, cy - radius * 0.68, radius * 1.36, radius * 1.36)
        for i in range(6):
            start_ang = int((self.angle2 + i * 60) * 16)
            span_ang = int(35 * 16)
            painter.drawArc(arc_rect2, start_ang, span_ang)

        # 6. Central Reactor Core Glow
        core_r = radius * (0.42 + self.pulse * 0.05)
        core_grad = QRadialGradient(cx, cy, core_r)
        core_grad.setColorAt(0.0, QColor(255, 255, 255, 240))
        core_grad.setColorAt(0.3, neon_cyan)
        core_grad.setColorAt(0.7, glow_color)
        core_grad.setColorAt(1.0, QColor(0, 20, 50, 10))

        painter.setBrush(QBrush(core_grad))
        painter.setPen(QPen(neon_cyan, 2.0))
        painter.drawEllipse(QPointF(cx, cy), core_r, core_r)

        # 7. High-Tech Core Brackets
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle3)
        painter.setPen(QPen(QColor(255, 255, 255, 200), 2.0))
        for _ in range(3):
            painter.drawArc(QRectF(-core_r * 0.75, -core_r * 0.75, core_r * 1.5, core_r * 1.5), int(0), int(60 * 16))
            painter.rotate(120)
        painter.restore()

        # 8. Center Hologram Text Overlay
        painter.setPen(status_text_color)
        font_title = QFont("Consolas", 10, QFont.Bold)
        painter.setFont(font_title)
        painter.drawText(QRectF(cx - 80, cy - 26, 160, 20), Qt.AlignCenter, "JARVIS")

        font_status = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(font_status)
        painter.setPen(QColor(255, 255, 255, 220))
        painter.drawText(QRectF(cx - 90, cy - 6, 180, 20), Qt.AlignCenter, f"● {self.status}")

        font_sub = QFont("Segoe UI", 7)
        painter.setFont(font_sub)
        painter.setPen(QColor(148, 163, 184, 180))
        painter.drawText(QRectF(cx - 100, cy + 12, 200, 16), Qt.AlignCenter, "MARK-85 HUD")
