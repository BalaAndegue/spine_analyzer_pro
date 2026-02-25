"""
VolumeViewer — Visualisation 3D du maillage osseux.
Utilise Matplotlib 3D (FigureCanvasQTAgg) au lieu de PyVista/VTK.
Fonctionne sans OpenGL 3.2 — rendu logiciel complet.
"""

import numpy as np
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSlider, QLabel, QGroupBox, QComboBox, QFileDialog,
    QSplitter, QSizePolicy, QCheckBox
)
from PySide6.QtCore import Qt, Signal

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from ...core.logger import get_logger

logger = get_logger(__name__)


class VolumeViewer(QWidget):
    """
    Widget de visualisation 3D du maillage osseux.
    Rendu Matplotlib 3D embarqué dans Qt — aucun OpenGL requis.
    Supporte : rotation souris, zoom molette, export STL/PNG.
    """

    mesh_loaded   = Signal()
    volume_loaded = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.mesh_data   = None   # pv.PolyData ou None
        self.volume_data = None   # numpy array 3D ou None
        self._current_cmap   = "bone"
        self._opacity        = 0.85
        self._show_wireframe = False
        self._show_slice     = False

        self._setup_ui()

    # ──────────────────────────────────────────────────────────────
    # UI
    # ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)

        splitter = QSplitter(Qt.Horizontal)

        # ── Panneau de contrôle ──────────────────────────────────
        ctrl = QWidget()
        ctrl.setMaximumWidth(200)
        ctrl_layout = QVBoxLayout(ctrl)
        ctrl_layout.setContentsMargins(4, 4, 4, 4)

        # Affichage
        vis_group = QGroupBox("Affichage")
        vis_layout = QVBoxLayout()

        self.chk_wireframe = QCheckBox("Filaire")
        self.chk_wireframe.stateChanged.connect(self._toggle_wireframe)
        vis_layout.addWidget(self.chk_wireframe)

        self.chk_slice = QCheckBox("Plans de coupe")
        self.chk_slice.stateChanged.connect(self._toggle_slice)
        vis_layout.addWidget(self.chk_slice)

        vis_layout.addWidget(QLabel("Palette :"))
        self.cmap_combo = QComboBox()
        self.cmap_combo.addItems(["bone", "gray", "viridis", "plasma", "hot", "cool"])
        self.cmap_combo.currentTextChanged.connect(self._change_cmap)
        vis_layout.addWidget(self.cmap_combo)

        vis_layout.addWidget(QLabel("Opacité :"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(85)
        self.opacity_slider.valueChanged.connect(lambda v: self._set_opacity(v / 100))
        vis_layout.addWidget(self.opacity_slider)
        vis_group.setLayout(vis_layout)
        ctrl_layout.addWidget(vis_group)

        # Caméra
        cam_group = QGroupBox("Caméra")
        cam_layout = QVBoxLayout()

        self.btn_reset_cam = QPushButton("🔄 Réinitialiser vue")
        self.btn_reset_cam.clicked.connect(self._reset_camera)
        cam_layout.addWidget(self.btn_reset_cam)

        for label, elev, azim in [("Vue Dessus", 90, 0), ("Vue Face", 0, 0),
                                   ("Vue Côté", 0, 90), ("Vue Iso", 30, 45)]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, e=elev, a=azim: self._set_view(e, a))
            cam_layout.addWidget(btn)

        cam_group.setLayout(cam_layout)
        ctrl_layout.addWidget(cam_group)

        # Export
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout()

        self.btn_export_stl = QPushButton("💾 Exporter STL")
        self.btn_export_stl.clicked.connect(self.export_stl)
        self.btn_export_stl.setEnabled(False)
        export_layout.addWidget(self.btn_export_stl)

        self.btn_export_png = QPushButton("🖼️ Capture PNG")
        self.btn_export_png.clicked.connect(self.export_png)
        export_layout.addWidget(self.btn_export_png)

        export_group.setLayout(export_layout)
        ctrl_layout.addWidget(export_group)

        ctrl_layout.addStretch()

        # Infos
        self.info_label = QLabel("Aucun maillage")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #aaa; font-size: 10px;")
        ctrl_layout.addWidget(self.info_label)

        # ── Canvas Matplotlib ────────────────────────────────────
        self.figure = Figure(figsize=(8, 7), facecolor="#1a1a2e")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.ax = self.figure.add_subplot(111, projection="3d")
        self._style_axes()
        self._draw_placeholder()

        splitter.addWidget(ctrl)
        splitter.addWidget(self.canvas)
        splitter.setSizes([200, 800])
        main_layout.addWidget(splitter)

        # Boutons inactifs au démarrage
        self.volume_checkbox = self.chk_slice  # compat avec code existant

    def _style_axes(self):
        self.ax.set_facecolor("#0d0d1a")
        self.figure.patch.set_facecolor("#1a1a2e")
        for axis in [self.ax.xaxis, self.ax.yaxis, self.ax.zaxis]:
            axis.pane.fill = False
            axis.pane.set_edgecolor("#333355")
        self.ax.tick_params(colors="#666688", labelsize=7)
        self.ax.set_xlabel("X (mm)", color="#8888aa", fontsize=8)
        self.ax.set_ylabel("Y (mm)", color="#8888aa", fontsize=8)
        self.ax.set_zlabel("Z (mm)", color="#8888aa", fontsize=8)

    def _draw_placeholder(self):
        self.ax.text2D(
            0.5, 0.5,
            "Ouvrez un dossier DICOM\npuis cliquez Reconstruire 3D (F4)",
            transform=self.ax.transAxes,
            ha="center", va="center",
            color="#5555aa", fontsize=11,
        )
        self.canvas.draw()

    # ──────────────────────────────────────────────────────────────
    # API publique (compatibilité avec main_window.py)
    # ──────────────────────────────────────────────────────────────

    def set_mesh_data(self, mesh_data):
        """
        Afficher un maillage 3D.
        mesh_data : pv.PolyData avec .points et .faces
        """
        self.mesh_data = mesh_data
        self._render_mesh()
        self.btn_export_stl.setEnabled(True)
        self.mesh_loaded.emit()

    def set_volume_data(self, volume_data: np.ndarray):
        """
        Stocker le volume (plans de coupe affichés si case cochée).
        Pas de rendu volumétrique complet (incompatible OpenGL).
        """
        self.volume_data = volume_data
        if self._show_slice:
            self._render_slices()
        self.volume_checkbox.setEnabled(True)
        self.volume_loaded.emit()

    # ──────────────────────────────────────────────────────────────
    # Rendu
    # ──────────────────────────────────────────────────────────────

    def _render_mesh(self):
        """Dessiner le maillage PyVista avec Matplotlib 3D."""
        if self.mesh_data is None:
            return

        self.ax.cla()
        self._style_axes()

        try:
            verts  = np.array(self.mesh_data.points)
            # faces PyVista : [n, v0, v1, v2, n, v0, v1, v2, ...]
            faces_flat = np.array(self.mesh_data.faces)

            triangles = []
            i = 0
            while i < len(faces_flat):
                n = faces_flat[i]
                if n == 3:
                    tri = faces_flat[i+1:i+1+n]
                    triangles.append(verts[tri])
                i += n + 1

            triangles = np.array(triangles)

            # Couleur basée sur la hauteur Z pour un effet 3D
            zvals = triangles[:, :, 2].mean(axis=1)
            zmin, zmax = zvals.min(), zvals.max()
            norm_z = (zvals - zmin) / max(zmax - zmin, 1)

            cmap = matplotlib.colormaps.get_cmap(self._current_cmap)
            face_colors = cmap(norm_z)
            face_colors[:, 3] = self._opacity

            # Sous-sampler si trop grand (> 30 000 triangles → lag)
            max_tris = 30_000
            if len(triangles) > max_tris:
                idx = np.random.choice(len(triangles), max_tris, replace=False)
                triangles = triangles[idx]
                face_colors = face_colors[idx]

            poly = Poly3DCollection(
                triangles,
                facecolors=face_colors,
                linewidths=0.3 if self._show_wireframe else 0,
                edgecolors="#334466" if self._show_wireframe else "none",
                shade=False,   # IMPORTANT: évite le bug shape mismatch avec facecolors RGBA
            )
            self.ax.add_collection3d(poly)

            # Ajuster les limites
            for axis, dim in zip(
                [self.ax.set_xlim, self.ax.set_ylim, self.ax.set_zlim],
                [verts[:, 0], verts[:, 1], verts[:, 2]]
            ):
                axis(dim.min(), dim.max())

            self.ax.set_title(
                f"Maillage osseux — {len(triangles):,} triangles",
                color="#aaaacc", fontsize=9, pad=6
            )

            # Afficher les plans de coupe si demandé
            if self._show_slice and self.volume_data is not None:
                self._render_slices()

            self.canvas.draw()

            n_tris = self.mesh_data.n_cells
            n_pts  = self.mesh_data.n_points
            self.info_label.setText(
                f"Sommets : {n_pts:,}\nTriangles : {n_tris:,}\n"
                f"(affiché : {len(triangles):,})"
            )
            logger.info(f"Maillage rendu : {len(triangles):,} triangles")

        except Exception as e:
            logger.error(f"Erreur rendu mesh : {e}", exc_info=True)

    def _render_slices(self):
        """Superposer 3 plans de coupe orthogonaux sur le maillage."""
        if self.volume_data is None:
            return

        vol = self.volume_data.astype(np.float32)
        nz, ny, nx = vol.shape
        cmap = matplotlib.colormaps.get_cmap("bone")

        def norm(arr):
            mn, mx = arr.min(), arr.max()
            return (arr - mn) / max(mx - mn, 1)

        # Plan axial (milieu Z)
        z0 = nz // 2
        xs, ys = np.meshgrid(np.arange(nx), np.arange(ny))
        zs = np.full_like(xs, z0, dtype=float)
        colors = cmap(norm(vol[z0]))
        self.ax.plot_surface(xs, ys, zs, facecolors=colors, alpha=0.4, shade=False)

        self.canvas.draw()

    # ──────────────────────────────────────────────────────────────
    # Contrôles
    # ──────────────────────────────────────────────────────────────

    def _toggle_wireframe(self, state):
        self._show_wireframe = bool(state)
        if self.mesh_data is not None:
            self._render_mesh()

    def _toggle_slice(self, state):
        self._show_slice = bool(state)
        if self.mesh_data is not None:
            self._render_mesh()

    def _change_cmap(self, name):
        self._current_cmap = name
        if self.mesh_data is not None:
            self._render_mesh()

    def _set_opacity(self, value):
        self._opacity = value
        if self.mesh_data is not None:
            self._render_mesh()

    def _reset_camera(self):
        self.ax.view_init(elev=30, azim=45)
        self.canvas.draw()

    def _set_view(self, elev, azim):
        self.ax.view_init(elev=elev, azim=azim)
        self.canvas.draw()

    # ──────────────────────────────────────────────────────────────
    # Export
    # ──────────────────────────────────────────────────────────────

    def export_stl(self):
        """Exporter le maillage en fichier STL."""
        if self.mesh_data is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter STL", "reconstruction.stl", "STL files (*.stl)"
        )
        if path:
            try:
                self.mesh_data.save(path)
                logger.info(f"STL exporté : {path}")
            except Exception as e:
                logger.error(f"Export STL : {e}")

    def export_png(self):
        """Capturer la vue 3D actuelle en PNG."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Capturer PNG", "vue_3d.png", "PNG files (*.png)"
        )
        if path:
            self.figure.savefig(path, dpi=150, bbox_inches="tight",
                                facecolor=self.figure.get_facecolor())
            logger.info(f"PNG exporté : {path}")

    # ──────────────────────────────────────────────────────────────
    # Compat code existant (stubs)
    # ──────────────────────────────────────────────────────────────

    @property
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, v):
        self._opacity = v