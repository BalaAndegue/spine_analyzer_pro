#!/usr/bin/env python3
"""
generate_test_dicom.py  (v2 — anatomie réaliste)
-------------------------------------------------
Génère un scanner CT synthétique haute qualité de la colonne lombaire.

Résolution  : 256×256 px, 120 coupes axiales
Spacing     : 0.9×0.9 mm XY, 2.5 mm Z
Anatomie    : corps vertébraux, pédicules, apophyses épineuses et transverses,
              disques intervertébraux, canal rachidien, muscles paravertébraux,
              graisse sous-cutanée, peau.
HU réalistes avec bruit gaussien.

Usage : python3 scripts/generate_test_dicom.py
"""

import sys, os, numpy as np, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)

OUTPUT_DIR   = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "test_dicom")
N_SLICES     = 120
ROWS = COLS  = 256
SPACING_XY   = 0.9   # mm
SPACING_Z    = 2.5   # mm
N_VERTEBRAE  = 5     # L1‑L5 lombaires

rng = np.random.default_rng(42)


def sigmoid(x): return 1 / (1 + np.exp(-x))


def soft_circle(Y, X, cy, cx, r, steepness=0.5):
    """Masque circulaire soft-edge."""
    d = np.sqrt((X - cx)**2 + (Y - cy)**2)
    return sigmoid((r - d) * steepness)


def make_spine_slice(z: int) -> np.ndarray:
    """Génère une coupe axiale CT réaliste."""
    img = np.full((ROWS, COLS), -950.0)   # air
    Y, X = np.ogrid[:ROWS, :COLS]
    cy, cx = ROWS // 2, COLS // 2

    # ── Corps du patient ─────────────────────────────────────────
    #  Ellipse de graisse sous-cutanée
    fat_mask = ((X - cx) / 95)**2 + ((Y - cy) / 85)**2 <= 1
    img[fat_mask] = -80 + rng.normal(0, 10, ROWS * COLS).reshape(ROWS, COLS)[fat_mask]

    # Peau (anneau fin)
    skin = (((X - cx) / 95)**2 + ((Y - cy) / 85)**2 <= 1) & \
           (((X - cx) / 88)**2 + ((Y - cy) / 78)**2 >= 1)
    img[skin] = 40

    # ── Muscles paravertébraux (deux lobes latéraux) ─────────────
    for side in [-1, 1]:
        mx = int(cx + side * 30)
        my = int(cy + 8)
        m = soft_circle(Y, X, my, mx, 22, steepness=0.4)
        img = np.where(m > 0.3, 55 + rng.normal(0, 8, img.shape), img)

    # ── Positionnement dans le cycle vertèbre / disque ───────────
    vertebra_h = N_SLICES // N_VERTEBRAE
    local_z    = z % vertebra_h
    disc_h     = max(3, vertebra_h // 6)
    in_disc    = local_z < disc_h

    # Légère rotation progressive (scoliose synthétique douce)
    angle = np.sin(z / N_SLICES * np.pi * 2) * 4   # ±4°
    rad   = np.deg2rad(angle)
    cos_a, sin_a = np.cos(rad), np.sin(rad)

    def rot(y, x):
        dy, dx = y - cy, x - cx
        return cy + dy * cos_a - dx * sin_a, cx + dy * sin_a + dx * cos_a

    # ── Corps vertébral ──────────────────────────────────────────
    r_body = 32
    r_core = 24

    body_mask = ((X - cx) / r_body)**2 + ((Y - cy) / r_body)**2 <= 1
    if not in_disc:
        # Os spongieux (travée)
        img[body_mask] = 250 + rng.normal(0, 20, img.shape)[body_mask]
        # Os cortical (anneau)
        cortical = body_mask & ~(((X - cx) / (r_body - 4))**2 + ((Y - cy) / (r_body - 4))**2 <= 1)
        img[cortical] = 900 + rng.normal(0, 30, img.shape)[cortical]
    else:
        # Disque intervertébral (nucléus pulposus + annulus)
        nucleus = ((X - cx) / 16)**2 + ((Y - cy) / 16)**2 <= 1
        img[body_mask] = 120 + rng.normal(0, 10, img.shape)[body_mask]   # annulus
        img[nucleus]   = 70  + rng.normal(0, 5,  img.shape)[nucleus]     # nucleus

    # ── Canal rachidien ──────────────────────────────────────────
    canal_cy = int(cy - r_body * 0.75)
    canal_mask = ((X - cx) / 9)**2 + ((Y - canal_cy) / 10)**2 <= 1
    img[canal_mask] = 15   # LCR

    # Moelle épinière (disque interne)
    cord_mask = ((X - cx) / 5)**2 + ((Y - canal_cy) / 6)**2 <= 1
    img[cord_mask] = 80

    if not in_disc:
        # ── Pédicules ─────────────────────────────────────────────
        for side in [-1, 1]:
            px = int(cx + side * (r_body + 4))
            py = int(canal_cy + 2)
            ped = ((X - px) / 8)**2 + ((Y - py) / 6)**2 <= 1
            img[ped] = 800 + rng.normal(0, 25, img.shape)[ped]

        # ── Lame vertébrale ───────────────────────────────────────
        for side in [-1, 1]:
            for t in np.linspace(0, 1, 12):
                lx = int(cx + side * (5 + t * 12))
                ly = int(canal_cy - int(2 + t * 6))
                lm = ((X - lx) / 4)**2 + ((Y - ly) / 3)**2 <= 1
                img[lm] = 850

        # ── Apophyse épineuse (postérieure) ──────────────────────
        for dy in range(0, 28, 3):
            sy = canal_cy - dy
            sm = ((X - cx) / 4)**2 + ((Y - sy) / 3)**2 <= 1
            img[sm] = 850 + rng.normal(0, 15, img.shape)[sm]

        # ── Apophyses transverses ─────────────────────────────────
        for side in [-1, 1]:
            for t in np.linspace(0, 1, 10):
                tx = int(cx + side * (r_body + 5 + t * 22))
                ty = int(cy - 2)
                tm = ((X - tx) / 5)**2 + ((Y - ty) / 4)**2 <= 1
                img[tm] = 820

    # ── Clip et bruit global ─────────────────────────────────────
    img += rng.normal(0, 8, img.shape)   # bruit quantum CT
    return np.clip(img, -1024, 3000).astype(np.int16)


def write_slice(pixel_array, z_idx, output_dir):
    import pydicom
    from pydicom.dataset import Dataset, FileDataset, FileMetaDataset
    from pydicom.uid import generate_uid, ExplicitVRLittleEndian

    px = (pixel_array + 1024).astype(np.uint16)

    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID    = "1.2.840.10008.5.1.4.1.1.2"
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID          = ExplicitVRLittleEndian

    ds = FileDataset(None, {}, file_meta=meta, preamble=b"\0" * 128)
    ds.PatientName, ds.PatientID = "Synthétique^Lombaire", "LUMBARSYN"
    ds.PatientAge, ds.PatientSex = "045Y", "M"
    ds.StudyInstanceUID    = "1.2.3.4.99.100"
    ds.SeriesInstanceUID   = "1.2.3.4.99.200"
    ds.SOPInstanceUID      = meta.MediaStorageSOPInstanceUID
    ds.SOPClassUID         = meta.MediaStorageSOPClassUID
    ds.StudyDate           = "20260225"
    ds.Modality            = "CT"
    ds.StudyDescription    = "Colonne lombaire synthétique"
    ds.SeriesDescription   = "Coupes axiales L1-L5"
    ds.Rows, ds.Columns    = ROWS, COLS
    ds.PixelSpacing        = [SPACING_XY, SPACING_XY]
    ds.SliceThickness      = SPACING_Z
    ds.SpacingBetweenSlices = SPACING_Z
    ds.ImagePositionPatient = [0.0, 0.0, z_idx * SPACING_Z]
    ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
    ds.InstanceNumber       = z_idx + 1
    ds.SamplesPerPixel      = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated, ds.BitsStored, ds.HighBit = 16, 16, 15
    ds.PixelRepresentation  = 0
    ds.RescaleIntercept     = -1024
    ds.RescaleSlope         = 1
    ds.RescaleType          = "HU"
    ds.PixelData            = px.tobytes()

    path = os.path.join(output_dir, f"CT_{z_idx:04d}.dcm")
    ds.save_as(path, enforce_file_format=True)
    return path


def main():
    import shutil
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    log.info(f"Génération {N_SLICES} coupes {ROWS}×{COLS} → {OUTPUT_DIR}")
    total = 0
    for z in range(N_SLICES):
        slc = make_spine_slice(z)
        f   = write_slice(slc, z, OUTPUT_DIR)
        total += os.path.getsize(f)
        if (z + 1) % 20 == 0:
            log.info(f"  {z+1}/{N_SLICES}...")

    size_mb  = total / 1e6
    vol_mb   = N_SLICES * ROWS * COLS * 4 / 1e6
    log.info(f"\n✅ {N_SLICES} fichiers DICOM | {size_mb:.1f} MB disque")
    log.info(f"💡 RAM reconstruction : ~{vol_mb + 30:.0f} MB")
    log.info(f"🚀 Dossier : {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
