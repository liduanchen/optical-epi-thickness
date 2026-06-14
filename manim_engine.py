from manim import *
import json
import numpy as np


class ThicknessAnimation(Scene):
    def construct(self):
        # 工业风深色背景
        self.camera.background_color = "#060b1c"

        try:
            with open("temp_render_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {
                "title": "光学外延层厚度分析",
                "result_text": "厚度: 2.345 μm",
                "fit_confidence": 90.0,
                "x": [1000, 1100, 1200, 1300, 1400],
                "y": [0.50, 0.71, 0.62, 0.74, 0.64],
                "fit_y": [0.48, 0.69, 0.64, 0.73, 0.66],
                "peaks_x": [1100, 1300],
                "peaks_y": [0.71, 0.74],
                "thickness_trace": [1.7, 2.0, 2.2, 2.3, 2.345],
                "mse_trace": [0.09, 0.05, 0.03, 0.015, 0.01],
            }

        x = np.array(data.get("x", [1000, 1100, 1200]), dtype=float)
        y = np.array(data.get("y", [0.5, 0.7, 0.6]), dtype=float)
        fit_y = np.array(data.get("fit_y", y.tolist()), dtype=float)
        peaks_x = data.get("peaks_x", [])
        peaks_y = data.get("peaks_y", [])
        trace = data.get("thickness_trace", [])
        mse_trace = data.get("mse_trace", [])

        x_min, x_max = float(np.min(x)), float(np.max(x))
        y_min = float(min(np.min(y), np.min(fit_y)) * 0.95)
        y_max = float(max(np.max(y), np.max(fit_y)) * 1.05)
        y_step = max((y_max - y_min) / 5, 0.02)

        # 标题区域
        title = Text(data.get("title", "厚度计算演示"), font_size=40, font="SimHei", color="#93c5fd")
        subtitle = Text("实验曲线与理论曲线动态收敛", font_size=24, font="SimHei", color="#67e8f9")
        title.to_edge(UP, buff=0.45)
        subtitle.next_to(title, DOWN, buff=0.18)
        self.play(FadeIn(title, shift=DOWN * 0.2), FadeIn(subtitle, shift=DOWN * 0.2), run_time=1.2)

        # 主坐标轴
        axes = Axes(
            x_range=[x_min - 30, x_max + 30, max((x_max - x_min) / 6, 100)],
            y_range=[y_min, y_max, y_step],
            x_length=11.4,
            y_length=5.2,
            axis_config={"color": "#64748b", "stroke_width": 2},
            tips=False,
        ).shift(DOWN * 0.65)
        labels = axes.get_axis_labels(
            Text("波数 (cm⁻¹)", font_size=24, font="SimHei", color="#cbd5e1"),
            Text("反射率", font_size=24, font="SimHei", color="#cbd5e1")
        )

        exp_graph = axes.plot_line_graph(
            x_values=x.tolist(),
            y_values=y.tolist(),
            line_color="#22d3ee",
            stroke_width=4,
            add_vertex_dots=False,
        )
        fit_graph = axes.plot_line_graph(
            x_values=x.tolist(),
            y_values=fit_y.tolist(),
            line_color="#f59e0b",
            stroke_width=4,
            add_vertex_dots=False,
        )
        fit_graph.set_opacity(0.35)

        peak_group = VGroup(
            *[Dot(axes.c2p(px, py), radius=0.055, color="#ef4444") for px, py in zip(peaks_x, peaks_y)]
        )

        self.play(Create(axes), FadeIn(labels), run_time=1.1)
        self.play(Create(exp_graph), run_time=1.2)
        self.play(FadeIn(peak_group, shift=UP * 0.12), run_time=0.8)

        # 迭代拟合信息条
        if trace and mse_trace:
            iter_idx = ValueTracker(0)

            def status_text():
                idx = int(np.clip(round(iter_idx.get_value()), 0, len(trace) - 1))
                return VGroup(
                    Text(f"迭代步: {idx + 1}/{len(trace)}", font_size=24, font="SimHei", color="#a7f3d0"),
                    Text(f"厚度猜测: {trace[idx]:.3f} μm", font_size=24, font="SimHei", color="#fde68a"),
                    Text(f"MSE: {mse_trace[idx]:.5f}", font_size=24, font="Consolas", color="#c4b5fd"),
                ).arrange(RIGHT, buff=0.45).to_edge(DOWN, buff=0.55)

            status = always_redraw(status_text)
            self.add(status)

            self.play(
                Transform(fit_graph, fit_graph.copy().set_opacity(0.95)),
                iter_idx.animate.set_value(len(trace) - 1),
                run_time=3.0,
                rate_func=smooth
            )
            self.remove(status)

        # 最终结果卡片
        result_text = data.get("result_text", "厚度: ? μm")
        confidence = data.get("fit_confidence", 0.0)
        result_panel = RoundedRectangle(width=8.5, height=1.7, corner_radius=0.16, stroke_width=1.6, stroke_color="#334155")
        result_panel.set_fill(color="#0f172a", opacity=0.95)
        result_panel.to_edge(DOWN, buff=0.35)

        result_line = Text(result_text, font_size=34, font="SimHei", color="#f8fafc")
        conf_line = Text(f"拟合置信度: {confidence:.1f}%", font_size=26, font="SimHei", color="#a78bfa")
        result_group = VGroup(result_line, conf_line).arrange(DOWN, buff=0.18).move_to(result_panel.get_center())

        formula = MathTex(r"d=\frac{10000}{2n\cos\theta^{'}\Delta\nu}", color="#cbd5e1").scale(0.9)
        formula.next_to(result_panel, UP, buff=0.28)

        self.play(FadeIn(result_panel), Write(result_group), FadeIn(formula, shift=UP * 0.1), run_time=1.4)
        self.wait(1.6)