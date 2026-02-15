import numpy as np
import pyvista as pv
from pyvistaqt import BackgroundPlotter
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt


# ---------------- STRUCTURAL FUNCTIONS ----------------

def compute_reactions(L, P, a, w):
    """Simply supported beam with point load P at x=a and full-span UDL w."""
    total_udl = w * L
    RB = (P * a + total_udl * (L / 2.0)) / L
    RA = (P + total_udl) - RB
    return RA, RB


def moment_along_beam(x, L, RA, P, a, w):
    """
    Bending moment M(x)
    Sagging positive
    """
    x = np.asarray(x)
    H = (x >= a).astype(float)
    M = RA * x - w * x**2 / 2.0 - P * (x - a) * H
    return M


# ---------------- MAIN APPLICATION ----------------

class BeamStressApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simply Supported Beam: Stress Viewer (PyVista)")

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QHBoxLayout(central)

        # -------- Controls Panel --------
        self.controls = QtWidgets.QFrame()
        self.controls.setFixedWidth(330)
        self.controls.setFrameShape(QtWidgets.QFrame.StyledPanel)
        layout.addWidget(self.controls)

        form = QtWidgets.QFormLayout(self.controls)
        form.setLabelAlignment(Qt.AlignLeft)

        # Inputs
        self.L = QtWidgets.QDoubleSpinBox(); self.L.setRange(0.1, 1e6); self.L.setValue(6.0); self.L.setSuffix(" m")
        self.P = QtWidgets.QDoubleSpinBox(); self.P.setRange(0.0, 1e9); self.P.setValue(20.0); self.P.setSuffix(" kN")
        self.a = QtWidgets.QDoubleSpinBox(); self.a.setRange(0.0, 1e6); self.a.setValue(3.0); self.a.setSuffix(" m")
        self.w = QtWidgets.QDoubleSpinBox(); self.w.setRange(0.0, 1e9); self.w.setValue(5.0); self.w.setSuffix(" kN/m")

        self.b = QtWidgets.QDoubleSpinBox(); self.b.setRange(0.001, 1000.0); self.b.setValue(0.25); self.b.setSuffix(" m")
        self.h = QtWidgets.QDoubleSpinBox(); self.h.setRange(0.001, 1000.0); self.h.setValue(0.45); self.h.setSuffix(" m")

        self.npts = QtWidgets.QSpinBox(); self.npts.setRange(50, 5000); self.npts.setValue(400)
        self.tube_r = QtWidgets.QDoubleSpinBox(); self.tube_r.setRange(0.001, 10.0); self.tube_r.setValue(0.06); self.tube_r.setSuffix(" m")

        self.show_deformed = QtWidgets.QCheckBox("Show exaggerated deflection (visual only)")
        self.show_deformed.setChecked(True)

        self.def_scale = QtWidgets.QDoubleSpinBox()
        self.def_scale.setRange(0.0, 1e6)
        self.def_scale.setValue(50.0)

        self.btn_update = QtWidgets.QPushButton("Update Plot")
        self.btn_update.clicked.connect(self.update_plot)

        self.lbl_results = QtWidgets.QLabel("RA: —\nRB: —\nMax σ: —")
        self.lbl_results.setStyleSheet("font-size: 12px;")

        # Layout
        form.addRow("Span L", self.L)
        form.addRow("Point Load P", self.P)
        form.addRow("Position a", self.a)
        form.addRow("UDL w", self.w)
        form.addRow(QtWidgets.QLabel("— Section (Rectangular) —"), QtWidgets.QLabel(""))
        form.addRow("Width b", self.b)
        form.addRow("Depth h", self.h)
        form.addRow(QtWidgets.QLabel("— Plot Controls —"), QtWidgets.QLabel(""))
        form.addRow("Discretization points", self.npts)
        form.addRow("Beam tube radius", self.tube_r)
        form.addRow(self.show_deformed)
        form.addRow("Deflection scale", self.def_scale)
        form.addRow(self.btn_update)
        form.addRow("Results", self.lbl_results)

        note = QtWidgets.QLabel(
            "Stress shown = elastic bending stress\n"
            "σ = |M|·c/I (beam theory)\n"
            "Not full 3D FEA."
        )
        note.setStyleSheet("color: #555;")
        form.addRow(note)

        # -------- PyVista Plotter --------
        self.plotter = BackgroundPlotter(show=False)
        layout.addWidget(self.plotter.app_window)

        self.update_plot()

    # ---------------- PLOT UPDATE ----------------

    def update_plot(self):
        self.plotter.clear()

        # Read values
        L = float(self.L.value())
        PkN = float(self.P.value())
        a = float(self.a.value())
        wkN = float(self.w.value())
        b = float(self.b.value())
        h = float(self.h.value())
        n = int(self.npts.value())
        r = float(self.tube_r.value())

        if a > L:
            a = L
            self.a.setValue(L)

        # Convert units
        P = PkN * 1e3
        w = wkN * 1e3

        # Section properties
        I = b * h**3 / 12.0
        c = h / 2.0

        # Reactions
        RA, RB = compute_reactions(L, P, a, w)

        # Discretize beam
        x = np.linspace(0, L, n)
        M = moment_along_beam(x, L, RA, P, a, w)
        sigma = np.abs(M) * c / I
        sigma_mpa = sigma / 1e6

        max_sigma = float(np.max(sigma_mpa))

        # Visual deflection (scaled moment shape)
        y = np.zeros_like(x)
        if self.show_deformed.isChecked():
            maxM = np.max(np.abs(M))
            if maxM > 0:
                y = -(M / maxM) * float(self.def_scale.value()) * 0.001

        # Create tube beam
        pts = np.c_[x, y, np.zeros_like(x)]
        line = pv.PolyData(pts)
        line.lines = np.hstack(([n], np.arange(n))).astype(np.int64)
        tube = line.tube(radius=r)

        # Safe stress interpolation
        tube_pts_x = tube.points[:, 0]
        stress_interp = np.interp(tube_pts_x, x, sigma_mpa)
        tube["Stress (MPa)"] = stress_interp

        self.plotter.add_mesh(
            tube,
            scalars="Stress (MPa)",
            cmap="turbo",
            show_scalar_bar=True,
            scalar_bar_args={"title": "Bending Stress (MPa)"},
            smooth_shading=True
        )

        # Supports
        sup_w = r * 1.8
        sup_h = r * 1.2

        blockA = pv.Cube(center=(0, -sup_h*2, 0),
                         x_length=sup_w,
                         y_length=sup_h,
                         z_length=sup_w)

        blockB = pv.Cube(center=(L, -sup_h*2, 0),
                         x_length=sup_w,
                         y_length=sup_h,
                         z_length=sup_w)

        self.plotter.add_mesh(blockA, color="gray")
        self.plotter.add_mesh(blockB, color="gray")

        # Update results text
        self.lbl_results.setText(
            f"RA: {RA/1e3:.3f} kN\n"
            f"RB: {RB/1e3:.3f} kN\n"
            f"Max σ: {max_sigma:.3f} MPa"
        )

        self.plotter.view_xy()
        self.plotter.camera.zoom(1.2)


# ---------------- RUN APP ----------------

def main():
    app = QtWidgets.QApplication([])
    win = BeamStressApp()
    win.resize(1200, 700)
    win.show()
    app.exec_()


if __name__ == "__main__":
    main()
 