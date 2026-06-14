import json
import math
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

# Qt 必须先于 Matplotlib 的 Qt 后端导入
try:
    from PyQt6.QtCore import QRectF, Qt, QTimer
    from PyQt6.QtGui import QColor, QBrush, QLinearGradient, QPainter, QPen
    from PyQt6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QFrame,
        QGraphicsDropShadowEffect,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPlainTextEdit,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QSplitter,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
    _QT_BIND = "PyQt6"
except ImportError:
    try:
        from PySide6.QtCore import QRectF, Qt, QTimer
        from PySide6.QtGui import QColor, QBrush, QLinearGradient, QPainter, QPen
        from PySide6.QtWidgets import (
            QApplication,
            QCheckBox,
            QComboBox,
            QFileDialog,
            QFrame,
            QGraphicsDropShadowEffect,
            QGridLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMainWindow,
            QMessageBox,
            QPlainTextEdit,
            QPushButton,
            QScrollArea,
            QSizePolicy,
            QSplitter,
            QTabWidget,
            QVBoxLayout,
            QWidget,
        )
        _QT_BIND = "PySide6"
    except ImportError:
        sys.stderr.write(
            "\n[错误] 请先安装: pip install PyQt6\n  或: pip install PySide6\n\n"
        )
        sys.exit(1)

# Qt6：QSizePolicy.Expanding 已迁至 QSizePolicy.Policy.Expanding
try:
    _QSP_EXPAND = QSizePolicy.Policy.Expanding
except AttributeError:
    _QSP_EXPAND = QSizePolicy.Expanding

import matplotlib

matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False


ENTERPRISE_QSS = """
QMainWindow, QWidget {
    background-color: #0a0e17;
    color: #e2e8f0;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}
QGroupBox {
    background-color: #111827;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 14px 14px 14px;
    font-weight: 600;
    color: #93c5fd;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #60a5fa;
}
QLabel#titleMain {
    font-size: 22px;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: 0.5px;
}
QLabel#titleSub {
    font-size: 12px;
    color: #64748b;
}
QLabel#kpiTitle {
    font-size: 11px;
    color: #94a3b8;
    font-weight: 500;
}
QLabel#kpiValue {
    font-size: 20px;
    font-weight: 700;
}
QLineEdit, QComboBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 28px;
    color: #e2e8f0;
    selection-background-color: #2563eb;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #3b82f6;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #1e293b;
    color: #e2e8f0;
    selection-background-color: #2563eb;
}
QPushButton {
    background-color: #1e40af;
    color: #f8fafc;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    min-height: 32px;
}
QPushButton:hover {
    background-color: #2563eb;
}
QPushButton:pressed {
    background-color: #1d4ed8;
}
QPushButton#btnPrimary {
    background-color: #059669;
}
QPushButton#btnPrimary:hover { background-color: #10b981; }
QPushButton#btnAccent {
    background-color: #7c3aed;
}
QPushButton#btnAccent:hover { background-color: #8b5cf6; }
QPushButton#btnTeal {
    background-color: #0d9488;
}
QPushButton#btnTeal:hover { background-color: #14b8a6; }
QPushButton:disabled {
    background-color: #334155;
    color: #64748b;
}
QFrame#kpiCard {
    background-color: #0f172a;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
}
QFrame#headerBar {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0f172a, stop:1 #111827);
    border-bottom: 1px solid #1e3a5f;
}
QFrame#glassHeader {
    background-color: rgba(15, 23, 42, 210);
    border: 1px solid rgba(148, 163, 184, 0.35);
    border-radius: 14px;
}
QTabWidget::pane {
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    top: -1px;
    background: #0f172a;
}
QTabBar::tab {
    background: #1e293b;
    color: #94a3b8;
    padding: 8px 18px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}
QTabBar::tab:selected {
    background: #1e40af;
    color: #f8fafc;
    font-weight: 600;
}
QScrollArea { border: none; background: transparent; }
QCheckBox { color: #cbd5e1; spacing: 8px; }
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #475569;
    background: #1e293b;
}
QCheckBox::indicator:checked {
    background: #2563eb;
    border-color: #3b82f6;
}
QLabel#resultText {
    color: #cbd5e1;
    font-size: 12px;
    line-height: 1.45;
}
"""

def _app_data_dir() -> Path:
    # 打包后 exe 所在目录可能不可写；统一把数据库放到用户目录下
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    d = base / "EPI-Vision"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_db_path() -> str:
    return str(_app_data_dir() / "optical_data.db")


def ensure_database_initialized() -> None:
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ExperimentalData (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material TEXT,
            angle REAL,
            wavenumber REAL,
            reflectance REAL
        )
        """
    )
    conn.commit()
    conn.close()


class EpitaxyRayWidget(QWidget):
    """
    空气 / 外延层 / 衬底 截面示意：斯涅尔折射 + 薄膜内多次反射（法布里-珀罗式干涉路径）。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._phase = 0.0
        self.angle_deg = 12.0
        self.thickness_um = 0.35
        self.n_film = 2.6
        self.n_sub = 2.55
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(36)
        self.setMinimumHeight(280)

    def _tick(self):
        self._phase = (self._phase + 0.05) % (2 * math.pi)
        self.update()

    def set_physics(self, angle_deg, thickness_um, n_film, n_sub=None):
        self.angle_deg = float(angle_deg)
        self.thickness_um = max(0.02, float(thickness_um))
        self.n_film = float(n_film)
        if n_sub is not None:
            self.n_sub = float(n_sub)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
        except AttributeError:
            p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        g = QLinearGradient(0, 0, 0, h)
        g.setColorAt(0.0, QColor(12, 18, 32))
        g.setColorAt(1.0, QColor(6, 8, 14))
        p.fillRect(self.rect(), g)

        margin = w * 0.06
        y_sub = h * 0.78
        film_h = max(36.0, min(140.0, self.thickness_um * 200.0))
        y_film_top = y_sub - film_h
        y_air_top = margin * 2
        x_left = margin
        x_right = w - margin

        # 衬底
        p.setPen(QPen(QColor(55, 65, 85), 1))
        p.setBrush(QColor(45, 55, 72))
        p.drawRect(int(x_left), int(y_sub), int(x_right - x_left), int(h - y_sub - margin))

        # 外延层
        p.setBrush(QColor(200, 160, 70, 210))
        p.setPen(QPen(QColor(245, 200, 90), 1))
        p.drawRect(int(x_left), int(y_film_top), int(x_right - x_left), int(film_h))

        # 空气区标签
        p.setPen(QColor(100, 116, 140))
        p.setFont(self.font())
        p.drawText(int(x_left + 6), int(y_air_top + 14), "空气 n₀≈1")
        p.drawText(int(x_left + 6), int(y_film_top + 16), f"外延层 n≈{self.n_film:.2f}  d≈{self.thickness_um:.3f} μm")
        p.drawText(int(x_left + 6), int(y_sub + 18), f"衬底 n≈{self.n_sub:.2f}")

        # 入射点
        entry_x = x_left + (x_right - x_left) * 0.28
        n0, n1 = 1.0, max(self.n_film, 1.01)
        theta0 = math.radians(self.angle_deg)
        sin_t1 = min(1.0, max(-1.0, n0 * math.sin(theta0) / n1))
        theta1 = math.asin(sin_t1)

        # 空气中入射方向（法线向下）：与竖直向下夹角 = θ0 → 方向 (sinθ0, cosθ0)
        ray_len_air = (y_film_top - y_air_top) * 1.4
        x_air0 = entry_x - ray_len_air * math.sin(theta0)
        y_air0 = y_film_top - ray_len_air * math.cos(theta0)

        def draw_seg(xa, ya, xb, yb, qc, width, alpha=255, style=Qt.PenStyle.SolidLine, dash_offset=None):
            pen = QPen(QColor(qc.red(), qc.green(), qc.blue(), alpha), width)
            pen.setStyle(style)
            if dash_offset is not None:
                try:
                    pen.setDashPattern([10.0, 7.0])
                    pen.setDashOffset(float(dash_offset))
                except Exception:
                    pass
            p.setPen(pen)
            p.drawLine(int(xa), int(ya), int(xb), int(yb))

        # 红色激光（入射+传播流动）
        laser = QColor(239, 68, 68)
        dash = -self._phase * 18.0
        draw_seg(x_air0, y_air0, entry_x, y_film_top, laser, 3, 235, Qt.PenStyle.DashLine, dash)

        # 薄膜内锯齿多次反射（外延层内上下界面来回，法布里-珀罗式干涉路径示意）
        ux = math.sin(theta1)
        uy = math.cos(theta1)
        x, y = entry_x, y_film_top + 2.0
        colors = [QColor(248, 113, 113), QColor(239, 68, 68), QColor(220, 38, 38)]
        out_count = 0
        for bounce in range(20):
            if uy > 1e-9:
                t_hit = (y_sub - y) / uy
            elif uy < -1e-9:
                t_hit = (y_film_top - y) / uy
            else:
                break
            if t_hit <= 0:
                break
            x2 = x + ux * t_hit
            y2 = y + uy * t_hit
            if x2 < x_left - 20 or x2 > x_right + 20:
                break
            qc = colors[bounce % len(colors)]
            a = max(55, 235 - bounce * 14)
            draw_seg(x, y, x2, y2, qc, 3 if bounce == 0 else 2, a, Qt.PenStyle.DashLine, dash + bounce * 2.2)

            # 每次到达上表面：画一条向空气反射出去的红色光束（多束叠加 → 干涉直觉）
            if abs(y2 - y_film_top) < 3.5 and out_count < 6:
                out_count += 1
                ray_len_out = (y_film_top - y_air_top) * 1.05
                # 向上出射，方向与入射关于法线对称
                x_out = x2 - ray_len_out * math.sin(theta0)
                y_out = y_film_top - ray_len_out * math.cos(theta0)
                # 轻微横向错开，避免完全重合看不出“多束”
                x_out += (out_count - 1) * 10.0
                x2o = x2 + (out_count - 1) * 5.0
                draw_seg(x2o, y_film_top, x_out, y_out, laser, 2, max(60, 210 - out_count * 22), Qt.PenStyle.DashLine, dash + out_count * 6.0)
            x, y = x2, y2
            uy = -uy

        p.setPen(QColor(148, 163, 184))
        cap = (
            f"入射角(相对法线) θ₀≈{self.angle_deg:.1f}°  →  薄膜内折射角 θ₁≈{math.degrees(theta1):.1f}°  |  "
            f"红色激光在薄膜内多次反射，空气侧多束反射叠加 → 薄膜干涉（示意）"
        )
        p.drawText(int(x_left + 6), int(h - margin - 6), cap)


class Structure3DWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fig = Figure(figsize=(6.2, 4.8), dpi=100, facecolor="#131b30")
        self.ax = self.fig.add_subplot(111, projection="3d")
        self.canvas = FigureCanvasQTAgg(self.fig)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.addWidget(self.canvas)
        self.update_structure(0.35, 10.0)

    def update_structure(self, thickness_um, angle_deg):
        self.ax.clear()
        self.ax.set_facecolor("#0f172a")
        d_vis = max(0.12, min(float(thickness_um), 5.0)) * 0.38
        W, D = 2.8, 1.6
        self.ax.bar3d(0, 0, -1.15, W, D, 1.15, color="#475569", alpha=0.95, shade=True, edgecolor="#334155")
        self.ax.bar3d(0, 0, 0, W, D, d_vis, color="#d4a853", alpha=0.92, shade=True, edgecolor="#b45309")
        self.ax.bar3d(0, 0, d_vis, W, D, 0.12, color="#38bdf8", alpha=0.38, shade=True, edgecolor="#0ea5e9")
        self.ax.set_xlim(0, W)
        self.ax.set_ylim(0, D)
        self.ax.set_zlim(-1.3, d_vis + 0.45)
        self.ax.set_xlabel("X", color="#94a3b8", fontsize=8)
        self.ax.set_ylabel("Y", color="#94a3b8", fontsize=8)
        self.ax.set_zlabel("Z ", color="#94a3b8", fontsize=8)
        self.ax.tick_params(colors="#64748b", labelsize=7)
        self.ax.view_init(elev=24, azim=-55 + min(12.0, angle_deg) * 0.4)
        self.ax.set_title(
            f"多层膜结构示意  d≈{thickness_um:.3f} μm  θ≈{angle_deg:.1f}°",
            color="#cbd5e1",
            fontsize=10,
            pad=8,
        )
        self.fig.tight_layout()
        self.canvas.draw_idle()


class EpiVisionQtWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EPI-Vision | 光学外延层厚度智能分析平台")
        self.resize(1480, 920)
        self.setMinimumSize(1100, 700)

        self.current_context = {}
        self.selected_import_file = None

        # 打包后的 exe 不再需要手动运行 step2/step3：启动时自动建表/初始化数据库
        ensure_database_initialized()

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 玻璃拟物顶栏 + 投影
        header_wrap = QWidget()
        header_outer = QVBoxLayout(header_wrap)
        header_outer.setContentsMargins(18, 14, 18, 8)
        glass = QFrame()
        glass.setObjectName("glassHeader")
        shadow = QGraphicsDropShadowEffect(glass)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 130))
        glass.setGraphicsEffect(shadow)
        hl = QHBoxLayout(glass)
        hl.setContentsMargins(22, 14, 22, 14)
        t1 = QLabel("EPI-Vision")
        t1.setObjectName("titleMain")
        t2 = QLabel("Enterprise Optical Metrology · TMM · 干涉拟合 · 物理示意 · 3D 结构")
        t2.setObjectName("titleSub")
        hl.addWidget(t1)
        hl.addStretch()
        hl.addWidget(t2)
        header_outer.addWidget(glass)
        root.addWidget(header_wrap)

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(16, 12, 16, 16)
        bl.setSpacing(12)

        # 参数区
        param_box = QGroupBox("分析参数与操作")
        pg = QGridLayout(param_box)
        pg.setSpacing(10)
        r = 0
        hdr0 = QLabel("数据集")
        hdr1 = QLabel("起点\ncm⁻¹")
        hdr2 = QLabel("算法")
        hdr3 = QLabel("反演")
        hdr4 = QLabel("n_film\n/ n_sub")
        hdr5 = QLabel("n范围\n~峰距")
        for h in (hdr0, hdr1, hdr2, hdr3, hdr4, hdr5):
            h.setWordWrap(True)
            h.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        pg.addWidget(hdr0, r, 0)
        pg.addWidget(hdr1, r, 1)
        pg.addWidget(hdr2, r, 2)
        pg.addWidget(hdr3, r, 3)
        pg.addWidget(hdr4, r, 4)
        pg.addWidget(hdr5, r, 5)
        r = 1
        self.combo_dataset = QComboBox()
        self.combo_dataset.setMinimumWidth(200)
        self.entry_min_wave = QLineEdit("1500")
        self.combo_method = QComboBox()
        self.combo_method.addItems(["峰值间距法（快速）", "TMM拟合法（精细）"])
        self.combo_inversion = QComboBox()
        self.combo_inversion.addItems(["固定折射率（反演厚度）", "联合反演（厚度+n_film）"])
        n_row = QWidget()
        n_l = QHBoxLayout(n_row)
        n_l.setContentsMargins(0, 0, 0, 0)
        self.entry_n_film = QLineEdit("2.60")
        self.entry_n_film.setMaximumWidth(80)
        self.entry_n_sub = QLineEdit("2.55")
        self.entry_n_sub.setMaximumWidth(80)
        n_l.addWidget(self.entry_n_film)
        n_l.addWidget(QLabel("/"))
        n_l.addWidget(self.entry_n_sub)
        sr = QWidget()
        sr_l = QHBoxLayout(sr)
        sr_l.setContentsMargins(0, 0, 0, 0)
        self.entry_n_min = QLineEdit("1.80")
        self.entry_n_min.setMaximumWidth(64)
        self.entry_n_max = QLineEdit("4.20")
        self.entry_n_max.setMaximumWidth(64)
        self.entry_peak_distance = QLineEdit("30")
        self.entry_peak_distance.setMaximumWidth(48)
        sr_l.addWidget(self.entry_n_min)
        sr_l.addWidget(QLabel("~"))
        sr_l.addWidget(self.entry_n_max)
        sr_l.addWidget(self.entry_peak_distance)
        pg.addWidget(self.combo_dataset, r, 0)
        pg.addWidget(self.entry_min_wave, r, 1)
        pg.addWidget(self.combo_method, r, 2)
        pg.addWidget(self.combo_inversion, r, 3)
        pg.addWidget(n_row, r, 4)
        pg.addWidget(sr, r, 5)

        # 左侧面板更紧凑一点，避免标题遮挡
        try:
            pg.setHorizontalSpacing(8)
        except Exception:
            pass

        btn_row = QHBoxLayout()
        self.btn_auto = QPushButton("一键自动分析")
        self.btn_auto.setObjectName("btnPrimary")
        self.btn_run = QPushButton("执行分析")
        self.btn_manim = QPushButton("生成 Manim 视频")
        self.btn_manim.setObjectName("btnAccent")
        self.btn_manim.setEnabled(False)
        self.btn_batch = QPushButton("批量规律学习")
        self.btn_batch.setObjectName("btnTeal")
        btn_row.addWidget(self.btn_auto)
        btn_row.addWidget(self.btn_run)
        btn_row.addWidget(self.btn_manim)
        btn_row.addWidget(self.btn_batch)
        btn_row.addStretch()
        pg.addLayout(btn_row, 2, 0, 1, 6)

        import_box = QGroupBox("数据库接入")
        ig = QVBoxLayout(import_box)
        ig.setContentsMargins(10, 8, 10, 10)
        self.import_file_label = QLabel("未选择文件")
        self.import_file_label.setWordWrap(True)
        self.import_file_label.setStyleSheet("color:#93c5fd;")
        ig.addWidget(self.import_file_label)
        row_imp = QHBoxLayout()
        self.entry_import_material = QLineEdit()
        self.entry_import_material.setPlaceholderText("材料名")
        self.entry_import_angle = QLineEdit()
        self.entry_import_angle.setPlaceholderText("角度")
        self.btn_pick = QPushButton("选择文件")
        self.btn_import = QPushButton("导入数据库")
        self.btn_import.setObjectName("btnPrimary")
        row_imp.addWidget(self.entry_import_material)
        row_imp.addWidget(self.entry_import_angle)
        row_imp.addWidget(self.btn_pick)
        row_imp.addWidget(self.btn_import)
        ig.addLayout(row_imp)
        self.chk_replace = QCheckBox("导入前清空同材料同角度历史数据")
        ig.addWidget(self.chk_replace)
        # 不要用固定高度截断文字/控件；让布局自适应

        result_box = QGroupBox("分析结果")
        rv = QVBoxLayout(result_box)
        rv.setContentsMargins(10, 8, 10, 10)
        self.result_label = QPlainTextEdit()
        self.result_label.setObjectName("resultText")
        self.result_label.setReadOnly(True)
        self.result_label.setPlainText("请选择数据集后执行分析。")
        try:
            self.result_label.setWordWrapMode(True)  # 某些绑定不支持该 API，下面再兜底
        except Exception:
            pass
        self.result_label.setMinimumHeight(120)
        self.result_label.setMaximumHeight(180)
        rv.addWidget(self.result_label, 1)
        result_box.setMinimumHeight(160)

        # ---- 模仿 step5_pro_gui_v2.py：顶部整行参数栏 + 中间左右(导入 / 可视化) + 底部整行结果 ----
        main = QWidget()
        grid = QGridLayout(main)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        kpi_wrap = QWidget()
        kpi_h = QHBoxLayout(kpi_wrap)
        kpi_h.setSpacing(8)
        self.kpi_thickness = self._make_kpi_card("厚度", "#34d399")
        self.kpi_peaks = self._make_kpi_card("峰值", "#60a5fa")
        self.kpi_delta = self._make_kpi_card("Δν", "#fbbf24")
        self.kpi_fit = self._make_kpi_card("拟合", "#a78bfa")
        self.kpi_method = self._make_kpi_card("算法", "#38bdf8")
        for w in (self.kpi_thickness, self.kpi_peaks, self.kpi_delta, self.kpi_fit, self.kpi_method):
            kpi_h.addWidget(w)

        plot_box = QGroupBox("可视化中心 · 光谱 / 光路动画 / 3D 结构")
        pv = QVBoxLayout(plot_box)
        self.tabs_viz = QTabWidget()
        spec_page = QWidget()
        spec_l = QVBoxLayout(spec_page)
        spec_l.setContentsMargins(0, 0, 0, 0)
        self.fig = Figure(figsize=(12, 6), dpi=100)
        self.fig.patch.set_facecolor("#131b30")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#0f172a")
        self.canvas = FigureCanvasQTAgg(self.fig)
        # 让右侧更均衡，避免左侧文字被挤压
        # 画布过高会导致页签/工具栏被挤压而“显示不全”，这里适当降低
        self.canvas.setMinimumHeight(450)
        self.canvas.setSizePolicy(_QSP_EXPAND, _QSP_EXPAND)
        self.plot_toolbar = NavigationToolbar2QT(self.canvas, spec_page)
        self.plot_toolbar.setStyleSheet(
            "background-color:#1e293b;color:#e2e8f0;border:none;border-radius:6px;padding:2px;"
        )
        spec_l.addWidget(self.plot_toolbar)
        spec_l.addWidget(self.canvas, 1)
        self.tabs_viz.addTab(spec_page, "干涉光谱")
        self.ray_widget = EpitaxyRayWidget()
        self.tabs_viz.addTab(self.ray_widget, "光路动画")
        self.struct_3d = Structure3DWidget()
        self.tabs_viz.addTab(self.struct_3d, "3D 多层膜")
        pv.addWidget(self.tabs_viz)

        # 右侧看板：KPI + 可视化中心（占主要面积）
        right_w = QWidget()
        right_v = QVBoxLayout(right_w)
        right_v.setContentsMargins(0, 0, 0, 0)
        right_v.setSpacing(10)
        right_v.addWidget(kpi_wrap)
        right_v.addWidget(plot_box, 1)

        # 左侧中部：数据库接入（类似 step5 的 import_card）
        left_mid = QWidget()
        left_mid_l = QVBoxLayout(left_mid)
        left_mid_l.setContentsMargins(0, 0, 0, 0)
        left_mid_l.setSpacing(10)
        left_mid_l.addWidget(import_box)
        left_mid_l.addStretch(1)
        left_mid.setMinimumWidth(380)

        # 网格布局（按你的要求）：
        # - row0：参数整行
        # - row1：左导入；右侧可视化看板（跨 row1+row2）
        # - row2：左下角分析结果（不再占满整行）
        grid.addWidget(param_box, 0, 0, 1, 2)
        grid.addWidget(left_mid, 1, 0, 1, 1)
        grid.addWidget(right_w, 1, 1, 2, 1)
        grid.addWidget(result_box, 2, 0, 1, 1)
        grid.setRowStretch(0, 0)
        grid.setRowStretch(1, 1)
        grid.setRowStretch(2, 0)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        bl.addWidget(main, 1)

        root.addWidget(body, 1)

        # 信号
        self.combo_dataset.currentTextChanged.connect(self.on_dataset_change)
        self.btn_auto.clicked.connect(self.auto_run_analysis)
        self.btn_run.clicked.connect(self.run_analysis)
        self.btn_manim.clicked.connect(self.render_manim_video)
        self.btn_batch.clicked.connect(self.run_batch_discovery)
        self.btn_pick.clicked.connect(self.pick_import_file)
        self.btn_import.clicked.connect(self.import_data_to_db)

        self._draw_empty_plot()
        self.load_dynamic_options()

    def _sync_physics_visuals(self, angle_deg, n_film, thickness_um, n_sub=None):
        if n_sub is None:
            try:
                n_sub = float(self.entry_n_sub.text())
            except Exception:
                n_sub = 2.55
        if hasattr(self, "ray_widget"):
            self.ray_widget.set_physics(angle_deg, thickness_um, n_film, n_sub)
        if hasattr(self, "struct_3d"):
            self.struct_3d.update_structure(thickness_um, angle_deg)

    def _make_kpi_card(self, title, color):
        f = QFrame()
        f.setObjectName("kpiCard")
        lay = QVBoxLayout(f)
        lay.setContentsMargins(12, 10, 12, 10)
        t = QLabel(title)
        t.setObjectName("kpiTitle")
        v = QLabel("—")
        v.setObjectName("kpiValue")
        v.setStyleSheet(f"color: {color};")
        v.setProperty("role", "value")
        lay.addWidget(t)
        lay.addWidget(v)
        f._value_label = v
        return f

    def _set_kpi(self, card, text):
        card._value_label.setText(text)

    def _draw_empty_plot(self):
        self.ax.clear()
        self.ax.set_title("等待数据输入", fontsize=14, color="#cbd5e1", pad=12)
        self.ax.set_xlabel("波数 (cm^-1)", color="#94a3b8")
        self.ax.set_ylabel("反射率 (%)", color="#94a3b8")
        self.ax.tick_params(colors="#94a3b8")
        for s in self.ax.spines.values():
            s.set_color("#334155")
        self.ax.grid(True, linestyle="--", linewidth=0.8, alpha=0.35, color="#475569")
        self.canvas.draw_idle()
        self._sync_physics_visuals(10.0, 2.6, 0.35)

    def show_message(self, title, text, kind="info"):
        if kind == "warning":
            QMessageBox.warning(self, title, text)
        elif kind == "error":
            QMessageBox.critical(self, title, text)
        else:
            QMessageBox.information(self, title, text)

    def load_dynamic_options(self):
        try:
            conn = sqlite3.connect(get_db_path())
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT material, angle FROM ExperimentalData")
            records = cur.fetchall()
            conn.close()
            self.combo_dataset.blockSignals(True)
            self.combo_dataset.clear()
            if not records:
                self.combo_dataset.addItem("(无数据)")
                self.combo_dataset.blockSignals(False)
                return
            for mat, ang in records:
                self.combo_dataset.addItem(f"{mat} - {ang}度")
            self.combo_dataset.blockSignals(False)
            self.on_dataset_change(self.combo_dataset.currentText())
        except Exception as e:
            self.show_message("数据库错误", str(e), "error")

    def on_dataset_change(self, selection):
        if not selection or "(无数据)" in selection:
            return
        try:
            material = selection.split(" - ")[0]
        except Exception:
            return
        preset = {
            "SiC": (2.60, 2.55),
            "Si": (3.40, 3.55),
            "GaN": (2.35, 2.30),
            "GaAs": (3.30, 3.45),
        }
        n_film, n_sub = preset.get(material, (2.60, 3.00))
        self.entry_n_film.setText(f"{n_film:.2f}")
        self.entry_n_sub.setText(f"{n_sub:.2f}")

    def auto_select_min_cutoff(self, df):
        if df.empty:
            return 1500.0
        x = df["wavenumber"].values
        y = df["reflectance"].values
        min_w = x.min()
        candidates = np.arange(max(min_w, 600), min(x.max(), 2200) + 1, 40)
        best_cutoff = None
        best_score = -np.inf
        for cutoff in candidates:
            mask = x >= cutoff
            if np.sum(mask) < 80:
                continue
            x_sub = x[mask]
            y_sub = y[mask]
            peaks, _ = find_peaks(y_sub, distance=20, height=np.mean(y_sub) * 0.7)
            if len(peaks) < 3:
                continue
            deltas = np.diff(x_sub[peaks])
            std_delta = np.std(deltas) if len(deltas) > 1 else 999
            score = len(peaks) * 12 - std_delta * 6
            if score > best_score:
                best_score = score
                best_cutoff = cutoff
        return float(best_cutoff) if best_cutoff is not None else max(min_w + 350, 1300.0)

    def run_analysis(self):
        try:
            min_cutoff = float(self.entry_min_wave.text().strip())
        except ValueError:
            self.show_message("输入错误", "分析起点请输入有效数字。", "warning")
            return
        self._perform_analysis(min_cutoff)

    def auto_run_analysis(self):
        selection = self.combo_dataset.currentText()
        if not selection or "无数据" in selection:
            self.show_message("提示", "请先选择数据集。", "warning")
            return
        material, angle_str = selection.split(" - ")
        angle_deg = float(angle_str.replace("度", ""))
        conn = sqlite3.connect(get_db_path())
        df = pd.read_sql(
            "SELECT wavenumber, reflectance FROM ExperimentalData WHERE material=? AND angle=?",
            conn,
            params=(material, angle_deg),
        )
        conn.close()
        best = self.auto_select_min_cutoff(df)
        self.entry_min_wave.setText(str(int(best)))
        self._perform_analysis(best)

    def _perform_analysis(self, min_cutoff):
        selection = self.combo_dataset.currentText()
        if not selection or "无数据" in selection:
            self.show_message("提示", "请先选择数据集。", "warning")
            return
        material, angle_str = selection.split(" - ")
        angle_deg = float(angle_str.replace("度", ""))
        conn = sqlite3.connect(get_db_path())
        df = pd.read_sql(
            "SELECT wavenumber, reflectance FROM ExperimentalData WHERE material=? AND angle=?",
            conn,
            params=(material, angle_deg),
        )
        conn.close()
        df_filtered = df[df["wavenumber"] >= min_cutoff].copy()
        if df_filtered.empty:
            self.show_message("警告", f"在 {min_cutoff} cm^-1 之后没有数据点。", "warning")
            return
        x = df_filtered["wavenumber"].values
        y = df_filtered["reflectance"].values
        method = self.combo_method.currentText().strip()
        try:
            n = float(self.entry_n_film.text().strip())
            n_sub = float(self.entry_n_sub.text().strip())
            peak_distance = max(5, int(float(self.entry_peak_distance.text().strip())))
            n_min = float(self.entry_n_min.text().strip())
            n_max = float(self.entry_n_max.text().strip())
        except ValueError:
            self.show_message("输入错误", "折射率与峰值间距请输入有效数字。", "warning")
            return
        if n_min >= n_max:
            self.show_message("输入错误", "联合反演的 n_film 范围需要满足 n_min < n_max。", "warning")
            return
        peaks, _ = find_peaks(y, distance=peak_distance, height=np.mean(y))
        if len(peaks) < 2:
            self.result_label.setPlainText("未检测到足够的干涉条纹，请降低峰值间距或调整分析起点。")
            return
        theta_prime = np.arcsin(np.sin(np.radians(angle_deg)) / n)
        avg_delta_nu = np.abs(np.mean(np.diff(x[peaks])))
        thickness_fast = 10000 / (2 * n * np.cos(theta_prime) * avg_delta_nu)
        constant_k = 10000 / (2 * n * np.cos(theta_prime))
        peak_x = x[peaks]
        phase_anchor = peak_x[0] if len(peak_x) > 0 else x[0]
        y_mean = float(np.mean(y))
        amp = max(float(np.ptp(y) / 2), 1e-6)

        def build_cosine_curve(thickness_guess):
            delta_guess = constant_k / max(thickness_guess, 1e-6)
            return y_mean + amp * np.cos(2 * np.pi * (x - phase_anchor) / delta_guess)

        def tmm_reflectance(thickness_um, n_film):
            wl_um = 10000.0 / np.maximum(x, 1e-9)
            n0 = 1.0
            n1 = n_film
            n2 = n_sub
            theta0 = np.radians(angle_deg)
            theta1 = np.arcsin(np.clip(n0 * np.sin(theta0) / n1, -1, 1))
            theta2 = np.arcsin(np.clip(n0 * np.sin(theta0) / n2, -1, 1))
            beta = 2 * np.pi * n1 * np.cos(theta1) * thickness_um / np.maximum(wl_um, 1e-9)
            exp_term = np.exp(2j * beta)
            r01_s = (n0 * np.cos(theta0) - n1 * np.cos(theta1)) / (n0 * np.cos(theta0) + n1 * np.cos(theta1))
            r12_s = (n1 * np.cos(theta1) - n2 * np.cos(theta2)) / (n1 * np.cos(theta1) + n2 * np.cos(theta2))
            rs = (r01_s + r12_s * exp_term) / (1 + r01_s * r12_s * exp_term)
            r01_p = (n1 * np.cos(theta0) - n0 * np.cos(theta1)) / (n1 * np.cos(theta0) + n0 * np.cos(theta1))
            r12_p = (n2 * np.cos(theta1) - n1 * np.cos(theta2)) / (n2 * np.cos(theta1) + n1 * np.cos(theta2))
            rp = (r01_p + r12_p * exp_term) / (1 + r01_p * r12_p * exp_term)
            raw = np.abs(0.5 * (rs + rp)) ** 2
            raw_norm = (raw - np.min(raw)) / (np.ptp(raw) + 1e-9)
            y_norm = (y - np.min(y)) / (np.ptp(y) + 1e-9)
            aligned = raw_norm * np.ptp(y) + np.min(y)
            mse = float(np.mean((raw_norm - y_norm) ** 2))
            return aligned, mse

        inversion_mode = self.combo_inversion.currentText().strip()
        if "TMM" in method:
            if "联合反演" in inversion_mode:
                best_mse = float("inf")
                best_fit = build_cosine_curve(thickness_fast)
                best_n = n
                best_trace = np.array([thickness_fast], dtype=float)
                for n_guess in np.linspace(n_min, n_max, 38):
                    theta_tmp = np.arcsin(np.clip(np.sin(np.radians(angle_deg)) / n_guess, -1, 1))
                    t0 = 10000 / (2 * n_guess * np.cos(theta_tmp) * max(avg_delta_nu, 1e-9))
                    search_min = max(0.1, t0 * 0.55)
                    search_max = max(search_min + 0.2, t0 * 1.8)
                    local_trace = np.linspace(search_min, search_max, 36)
                    for t_guess in local_trace:
                        y_guess, mse_guess = tmm_reflectance(float(t_guess), float(n_guess))
                        if mse_guess < best_mse:
                            best_mse = mse_guess
                            best_fit = y_guess
                            best_n = float(n_guess)
                            thickness_um = float(t_guess)
                            best_trace = local_trace
                n = best_n
                thickness_trace = np.append(best_trace, thickness_um)
                mse_trace = [tmm_reflectance(float(t), n)[1] for t in thickness_trace]
                y_fit = best_fit
                mse_final = float(best_mse)
            else:
                search_min = max(0.2, thickness_fast * 0.5)
                search_max = max(search_min + 0.2, thickness_fast * 1.8)
                thickness_trace = np.linspace(search_min, search_max, 52)
                mse_trace = []
                best_idx = 0
                best_mse = float("inf")
                best_fit = build_cosine_curve(thickness_fast)
                for i, t_guess in enumerate(thickness_trace):
                    y_guess, mse_guess = tmm_reflectance(float(t_guess), n)
                    mse_trace.append(mse_guess)
                    if mse_guess < best_mse:
                        best_mse = mse_guess
                        best_idx = i
                        best_fit = y_guess
                thickness_um = float(thickness_trace[best_idx])
                y_fit = best_fit
                mse_final = float(best_mse)
        else:
            thickness_um = float(thickness_fast)
            thickness_trace = np.linspace(max(thickness_um * 0.65, 0.1), thickness_um * 1.35, 36)
            thickness_trace = np.append(thickness_trace, thickness_um)
            mse_trace = [
                float(np.mean((build_cosine_curve(float(t)) - y) ** 2)) for t in thickness_trace
            ]
            y_fit = build_cosine_curve(thickness_um)
            mse_final = float(np.mean((y_fit - y) ** 2))

        fit_confidence = max(0.0, min(100.0, (1.0 - mse_final / (np.var(y) + 1e-9)) * 100.0))
        method_label = "TMM拟合法" if "TMM" in method else "峰值间距法"
        if "联合反演" in inversion_mode and "TMM" in method:
            method_label = "TMM联合反演"
        eps_r = n ** 2
        optical_level = "高折射率" if n >= 3.0 else ("中等折射率" if n >= 2.0 else "低折射率")

        self.result_label.setPlainText(
            f"分析完成：{selection}\n\n"
            f"算法模式：{method_label}\n"
            f"分析起点：{min_cutoff:.0f} cm^-1\n"
            f"n_film={n:.3f}, n_sub={n_sub:.3f}, 峰值间距={peak_distance}\n"
            f"检测峰值：{len(peaks)} 个\n"
            f"平均波数差 Δν：{avg_delta_nu:.2f} cm^-1\n"
            f"推算外延层厚度：{thickness_um:.3f} μm\n"
            f"拟合置信度：{fit_confidence:.1f}%\n"
            f"反演光学性质：n_film={n:.3f}, εr≈{eps_r:.3f}（{optical_level}）"
        )
        self._set_kpi(self.kpi_thickness, f"{thickness_um:.3f} μm")
        self._set_kpi(self.kpi_peaks, str(len(peaks)))
        self._set_kpi(self.kpi_delta, f"{avg_delta_nu:.2f} cm^-1")
        self._set_kpi(self.kpi_fit, f"{fit_confidence:.1f}%")
        self._set_kpi(self.kpi_method, method_label)

        self.ax.clear()
        self.ax.set_facecolor("#0f172a")
        self.ax.plot(x, y, color="#22d3ee", linewidth=2.0, alpha=0.95, label="实验光谱")
        self.ax.fill_between(x, y, np.min(y), color="#0ea5e9", alpha=0.12)
        self.ax.plot(x, y_fit, color="#f59e0b", linewidth=2.1, linestyle="--", alpha=0.92, label="理论拟合")
        self.ax.scatter(
            x[peaks],
            y[peaks],
            color="#ef4444",
            s=70,
            edgecolors="#f8fafc",
            linewidth=1.2,
            zorder=5,
            label="干涉峰",
        )
        self.ax.set_title(f"{selection} | 起点 {min_cutoff:.0f} cm^-1", fontsize=14, color="#e2e8f0", pad=12)
        self.ax.set_xlabel("波数 (cm^-1)", color="#cbd5e1")
        self.ax.set_ylabel("反射率 (%)", color="#cbd5e1")
        self.ax.tick_params(colors="#94a3b8")
        for spine in self.ax.spines.values():
            spine.set_color("#334155")
        self.ax.grid(True, linestyle="--", linewidth=0.8, alpha=0.35, color="#475569")
        leg = self.ax.legend(loc="upper right", fontsize=10, frameon=True)
        leg.get_frame().set_facecolor("#111827")
        leg.get_frame().set_edgecolor("#334155")
        for t in leg.get_texts():
            t.set_color("#f8fafc")
        self.fig.tight_layout()
        self.canvas.draw_idle()

        self.current_context = {
            "title": f"光学测厚推演: {selection}",
            "x": x.tolist(),
            "y": y.tolist(),
            "fit_y": y_fit.tolist(),
            "peaks_x": x[peaks].tolist(),
            "peaks_y": y[peaks].tolist(),
            "result_text": f"厚度: {thickness_um:.3f} μm",
            "fit_confidence": fit_confidence,
            "method": method_label,
            "thickness_trace": thickness_trace.tolist(),
            "mse_trace": mse_trace,
        }
        self._sync_physics_visuals(angle_deg, n, thickness_um, n_sub)
        self.btn_manim.setEnabled(True)

    def render_manim_video(self):
        if not self.current_context:
            self.show_message("提示", "请先完成一次分析。", "warning")
            return
        self.btn_manim.setEnabled(False)
        self.btn_manim.setText("渲染中…")
        QApplication.processEvents()
        try:
            if os.path.exists("media"):
                import shutil
                shutil.rmtree("media", ignore_errors=True)
            with open("temp_render_data.json", "w", encoding="utf-8") as f:
                json.dump(self.current_context, f, ensure_ascii=False)
            subprocess.run(
                [sys.executable, "-m", "manim", "-pql", "--disable_caching", "manim_engine.py", "ThicknessAnimation"],
                check=True,
            )
            self.show_message("渲染完成", "视频已生成，请查看 media/videos 目录。", "info")
        except Exception as e:
            self.show_message("渲染错误", str(e), "error")
        finally:
            self.btn_manim.setText("生成 Manim 视频")
            self.btn_manim.setEnabled(True)

    def run_batch_discovery(self):
        self.btn_batch.setEnabled(False)
        self.btn_batch.setText("分析中…")
        QApplication.processEvents()
        try:
            conn = sqlite3.connect(get_db_path())
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT material, angle FROM ExperimentalData ORDER BY material, angle")
            datasets = cur.fetchall()
            if not datasets:
                conn.close()
                self.show_message("提示", "数据库中没有可用数据集。", "warning")
                return
            rows = []
            for material, angle_deg in datasets:
                df = pd.read_sql(
                    "SELECT wavenumber, reflectance FROM ExperimentalData WHERE material=? AND angle=?",
                    conn,
                    params=(material, float(angle_deg)),
                )
                if df.empty:
                    continue
                min_cutoff = self.auto_select_min_cutoff(df)
                df = df[df["wavenumber"] >= min_cutoff].copy()
                if len(df) < 120:
                    continue
                x = df["wavenumber"].values
                y = df["reflectance"].values
                peaks, _ = find_peaks(y, distance=30, height=np.mean(y))
                if len(peaks) < 2:
                    continue
                avg_delta_nu = float(np.abs(np.mean(np.diff(x[peaks]))))
                n_sub = 2.55 if material == "SiC" else (3.55 if material == "Si" else 3.00)
                n_candidates = np.linspace(1.8, 4.2, 42)
                best_mse = float("inf")
                best_n = 2.6
                best_t = 1.0
                y_norm = (y - np.min(y)) / (np.ptp(y) + 1e-9)
                for n_guess in n_candidates:
                    theta_tmp = np.arcsin(np.clip(np.sin(np.radians(angle_deg)) / n_guess, -1, 1))
                    t0 = 10000 / (2 * n_guess * np.cos(theta_tmp) * max(avg_delta_nu, 1e-9))
                    t_min = max(0.08, t0 * 0.55)
                    t_max = max(t_min + 0.2, t0 * 1.8)
                    for t_guess in np.linspace(t_min, t_max, 36):
                        wl_um = 10000.0 / np.maximum(x, 1e-9)
                        n0, n1, n2 = 1.0, n_guess, n_sub
                        theta0 = np.radians(angle_deg)
                        theta1 = np.arcsin(np.clip(n0 * np.sin(theta0) / n1, -1, 1))
                        theta2 = np.arcsin(np.clip(n0 * np.sin(theta0) / n2, -1, 1))
                        beta = 2 * np.pi * n1 * np.cos(theta1) * t_guess / np.maximum(wl_um, 1e-9)
                        exp_term = np.exp(2j * beta)
                        r01_s = (n0 * np.cos(theta0) - n1 * np.cos(theta1)) / (n0 * np.cos(theta0) + n1 * np.cos(theta1))
                        r12_s = (n1 * np.cos(theta1) - n2 * np.cos(theta2)) / (n1 * np.cos(theta1) + n2 * np.cos(theta2))
                        rs = (r01_s + r12_s * exp_term) / (1 + r01_s * r12_s * exp_term)
                        r01_p = (n1 * np.cos(theta0) - n0 * np.cos(theta1)) / (n1 * np.cos(theta0) + n0 * np.cos(theta1))
                        r12_p = (n2 * np.cos(theta1) - n1 * np.cos(theta2)) / (n2 * np.cos(theta1) + n1 * np.cos(theta2))
                        rp = (r01_p + r12_p * exp_term) / (1 + r01_p * r12_p * exp_term)
                        raw = np.abs(0.5 * (rs + rp)) ** 2
                        raw_norm = (raw - np.min(raw)) / (np.ptp(raw) + 1e-9)
                        mse = float(np.mean((raw_norm - y_norm) ** 2))
                        if mse < best_mse:
                            best_mse = mse
                            best_n = float(n_guess)
                            best_t = float(t_guess)
                fit_confidence = max(0.0, min(100.0, (1.0 - best_mse / (np.var(y_norm) + 1e-9)) * 100.0))
                rows.append(
                    {
                        "material": material,
                        "angle_deg": float(angle_deg),
                        "cutoff_cm^-1": float(min_cutoff),
                        "peak_count": int(len(peaks)),
                        "avg_delta_nu_cm^-1": avg_delta_nu,
                        "thickness_um": best_t,
                        "n_film": best_n,
                        "epsilon_r": best_n ** 2,
                        "fit_confidence_percent": fit_confidence,
                    }
                )
            conn.close()
            if not rows:
                self.show_message("提示", "批量分析未得到有效结果。", "warning")
                return
            out_df = pd.DataFrame(rows).sort_values(by=["material", "angle_deg"])
            out_csv = Path("batch_optical_patterns.csv")
            out_png = Path("batch_optical_patterns.png")
            out_df.to_csv(out_csv, index=False, encoding="utf-8-sig")
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.4), dpi=120)
            fig.patch.set_facecolor("#0f172a")
            for ax in axes:
                ax.set_facecolor("#111827")
                ax.grid(True, linestyle="--", alpha=0.35, color="#475569")
                ax.tick_params(colors="#cbd5e1")
                for sp in ax.spines.values():
                    sp.set_color("#334155")
            for mat in out_df["material"].unique():
                g = out_df[out_df["material"] == mat]
                axes[0].plot(g["angle_deg"], g["thickness_um"], marker="o", linewidth=2.0, label=mat)
                axes[1].plot(g["angle_deg"], g["n_film"], marker="o", linewidth=2.0, label=mat)
            axes[0].set_title("角度-厚度规律", color="#e2e8f0")
            axes[0].set_xlabel("入射角 (deg)", color="#cbd5e1")
            axes[0].set_ylabel("厚度 (um)", color="#cbd5e1")
            axes[1].set_title("角度-有效折射率规律", color="#e2e8f0")
            axes[1].set_xlabel("入射角 (deg)", color="#cbd5e1")
            axes[1].set_ylabel("n_film", color="#cbd5e1")
            for ax in axes:
                leg = ax.legend()
                leg.get_frame().set_facecolor("#0b1220")
                leg.get_frame().set_edgecolor("#334155")
                for txt in leg.get_texts():
                    txt.set_color("#f8fafc")
            fig.tight_layout()
            fig.savefig(out_png, dpi=160)
            plt.close(fig)
            self.show_message("导出完成", f"已生成:\n{out_csv}\n{out_png}", "info")
        except Exception as e:
            self.show_message("批量分析失败", str(e), "error")
        finally:
            self.btn_batch.setText("批量规律学习")
            self.btn_batch.setEnabled(True)

    def pick_import_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择光谱数据",
            str(Path.cwd()),
            "数据 (*.xlsx *.xls *.csv);;所有文件 (*.*)",
        )
        if path:
            self.selected_import_file = path
            self.import_file_label.setText(f"已选择: {os.path.basename(path)}")

    def import_data_to_db(self):
        if not self.selected_import_file:
            self.show_message("提示", "请先选择文件。", "warning")
            return
        material = self.entry_import_material.text().strip()
        try:
            angle = float(self.entry_import_angle.text().strip())
        except ValueError:
            self.show_message("输入错误", "角度请输入数字。", "warning")
            return
        if not material:
            self.show_message("输入错误", "请输入材料名称。", "warning")
            return
        self.btn_import.setEnabled(False)
        self.btn_import.setText("导入中…")
        QApplication.processEvents()
        try:
            path = self.selected_import_file
            if path.lower().endswith(".csv"):
                raw = pd.read_csv(path)
            else:
                raw = pd.read_excel(path)
            if raw.shape[1] < 2:
                raise ValueError("至少需要两列：波数、反射率")
            x = pd.to_numeric(raw.iloc[:, 0], errors="coerce")
            y = pd.to_numeric(raw.iloc[:, 1], errors="coerce")
            clean = pd.DataFrame({"wavenumber": x, "reflectance": y}).dropna().sort_values("wavenumber")
            if clean.empty:
                raise ValueError("无有效数值行")
            conn = sqlite3.connect(get_db_path())
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS ExperimentalData (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    material TEXT,
                    angle REAL,
                    wavenumber REAL,
                    reflectance REAL
                )
                """
            )
            if self.chk_replace.isChecked():
                cur.execute("DELETE FROM ExperimentalData WHERE material=? AND angle=?", (material, angle))
            conn.commit()
            payload = pd.DataFrame(
                {
                    "material": material,
                    "angle": angle,
                    "wavenumber": clean["wavenumber"].values,
                    "reflectance": clean["reflectance"].values,
                }
            )
            payload.to_sql("ExperimentalData", conn, if_exists="append", index=False)
            conn.close()
            self.load_dynamic_options()
            target = f"{material} - {angle}度"
            idx = self.combo_dataset.findText(target)
            if idx >= 0:
                self.combo_dataset.setCurrentIndex(idx)
            self.show_message("导入成功", f"已导入 {len(payload)} 条记录。", "info")
        except Exception as e:
            self.show_message("导入失败", str(e), "error")
        finally:
            self.btn_import.setText("导入数据库")
            self.btn_import.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(ENTERPRISE_QSS)
    w = EpiVisionQtWindow()
    w.setWindowTitle(f"EPI-Vision | Qt ({_QT_BIND}) · 光学外延层厚度智能分析平台")
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
