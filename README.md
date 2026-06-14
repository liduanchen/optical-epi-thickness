# EPI-Vision · 光学外延层厚度智能分析平台

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-%E2%9C%93-brightgreen)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

> 基于**传输矩阵法（TMM）**的半导体外延层光学测厚桌面应用，支持光谱拟合、光路动画、3D 结构可视化和 Manim 教学视频生成。

---

## 功能概览

| 模块 | 说明 |
|:---|:---|
| **双算法引擎** | 峰值间距法（快速估算）+ TMM 传输矩阵法（s/p 偏振精确拟合） |
| **智能反演** | 固定折射率反演厚度 / 联合反演厚度 + 外延层折射率 |
| **干涉光谱** | 实验曲线 + 理论拟合 + 峰标记，支持自定义分析起点 |
| **光路动画** | 法布里-珀罗多次反射与流动激光实时动画 |
| **3D 多层膜** | 厚度与入射角联动的三维结构模型 |
| **批量分析** | 自动遍历数据库所有光谱数据，生成规律图表 |
| **教学视频** | 一键对接 Manim 渲染引擎，生成可视化教学视频 |
| **KPI 看板** | 实时显示厚度、峰数、拟合置信度等关键指标 |

---

## 快速开始

### 安装依赖

```bash
pip install PyQt6 matplotlib pandas numpy scipy openpyxl
```

可选（获得完整体验）：

```bash
pip install manim
```

### 启动

```bash
python epi_vision_qt.py
```

---

## 使用流程

1. **导入数据** — 选择 `.xlsx` / `.csv` 光谱文件，填写材料名和入射角度
2. **选择数据集** — 从下拉框选择已导入的数据
3. **运行分析** — 点击「一键自动分析」或手动调参后点击「执行分析」
4. **查看结果** — 在三个 Tab 页中切换：干涉光谱 / 光路动画 / 3D 多层膜
5. **批量分析** — 点击「批量规律学习」输出全域分析报表

### 内置材料折射率参考

| 材料 | n_film（外延层） | n_sub（衬底） |
|:---|:---:|:---:|
| SiC | 2.60 | 2.55 |
| Si | 3.40 | 3.55 |
| GaN | 2.35 | 2.30 |
| GaAs | 3.30 | 3.45 |

---

## 数据格式

光谱文件需包含两列数据：

| 列 | 内容 | 单位 |
|:---|:---|:---:|
| 第 1 列 | 波数（Wavenumber） | cm⁻¹ |
| 第 2 列 | 反射率（Reflectance） | % |

---

## 项目文件

```
EPI-Vision/
├── epi_vision_qt.py       # 主程序（PyQt6）
├── manim_engine.py         # Manim 视频渲染引擎
├── ENTERPRISE_QSS.txt      # 企业级深色样式表
├── README.md               # 本文档
└── Si* / SiC*.xlsx         # 示例光谱数据
```

---

## 技术栈

- **GUI** — PyQt6 / PySide6
- **算法** — TMM 传输矩阵法 + scipy 寻峰
- **可视化** — Matplotlib（光谱 / 3D）+ 自研 QPainter 动画组件
- **数据** — SQLite3 + pandas
- **视频** — Manim 动画引擎

---

## FAQ

**Q：启动提示缺少 PyQt6？**
A：执行 `pip install PyQt6` 或 `pip install PySide6`。

**Q：数据保存在哪里？**
A：默认在 `%LOCALAPPDATA%\EPI-Vision\optical_data.db`，删除可重置软件。

**Q：Manim 视频渲染失败？**
A：确保已安装 `manim` 及 FFmpeg，Windows 用户可能需要安装 LaTeX（推荐 MikTeX）。

**Q：拟合置信度低？**
A：尝试降低「分析起点」或调小「峰值间距」参数。

---

## License

MIT
