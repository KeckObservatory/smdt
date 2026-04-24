import numpy as np
import pandas as pd
from dataclasses import dataclass

# ============================================================
# Math constants
# ============================================================

PI     = 3.14159265358979324
TWOPI  = 2.0 * PI
HALFPI = PI / 2.0

RPD  = PI / 180.0          # radians per degree
DPR  = 1.0 / RPD
RPH  = RPD * 15.0
RPS  = RPH / 3600.0
RPAS = RPD / 3600.0        # radians per arcsecond


# ============================================================
# Instrument / slitmask configuration
# ============================================================

@dataclass
class InstrumentConfig:
    x_center: float          # mm
    scale: float             # mm / arcsec
    mask_angle_deg: float    # degrees
    mask_bend_deg: float     # degrees


# ============================================================
# Vectorized coordinate transform
# ============================================================

def ad_to_xy_vec(ra0, dec0, ra, dec, theta, inst):
    """
    Vectorized transform from (RA, DEC) to (X, Y) mask coordinates.

    Parameters
    ----------
    ra0, dec0 : float
        Field center [radians]
    ra, dec : array-like
        Object coordinates [radians]
    theta : array-like
        Rotator angle [radians]
    inst : InstrumentConfig

    Returns
    -------
    x, y : ndarray
        Mask coordinates [mm]
    status : ndarray (int)
        Status flag (all zeros, Fortran-compatible)
    """


    #ra    = np.array([row["raR"]    for row in df])
    #dec   = np.array([row["decR"]   for row in df])
    #theta = np.array([row["theta"]  for row in df])

#    ra  = np.asarray(ra)
#    dec = np.asarray(dec)
#    theta = np.asarray(theta)

    # Status array (Fortran never really sets this)
    status = np.zeros_like(ra, dtype=int)

    # Fixed angles
    m_angle = inst.mask_angle_deg * RPD
    bend    = inst.mask_bend_deg * RPD
    angle   = theta * RPD

    xo = inst.x_center / inst.scale

    # ---- Field center offset (J. Cohen fix) ----
    ra1  = xo * np.cos(angle) * RPAS / np.cos(dec0)
    dec1 = xo * np.sin(angle) * RPAS

    rac  = ra0  - ra1
    decc = dec0 - dec1

    # ---- Gnomonic projection ----
    dr = ra - rac

    sdr = np.sin(dr)
    cdr = np.cos(dr)

    sd  = np.sin(dec)
    cd  = np.cos(dec)

    sd0 = np.sin(decc)
    cd0 = np.cos(decc)

    denom = sd * sd0 + cd * cd0 * cdr

    eta = cd * sdr / (denom * RPAS)
    nu  = (sd * cd0 - cd * sd0 * cdr) / (denom * RPAS)

    # ---- Rotate and scale ----
    cos_a = np.cos(angle)
    sin_a = np.sin(angle)

    x = ( cos_a * eta + sin_a * nu) * inst.scale
    y = (-sin_a * eta + cos_a * nu) * inst.scale

    # ---- Final mask corrections ----
    x /= np.cos(m_angle)
    y /= np.cos(bend)

    return x, y, status


# ============================================================
# DataFrame driver (fully vectorized)
# ============================================================
def xypos_df(df, inst):
    """
    Vectorized replacement for Fortran XYPOS.

    Required DataFrame columns
    --------------------------
    raRad      : object RA (radians)
    decRad     : object DEC (radians)
    ra_fldR    : field center RA (radians)
    dec_fldR   : field center DEC (radians)
    objectId   : object name

    Output columns added
    --------------------
    obj_t_x    : mask X (mm)
    obj_t_y    : mask Y (mm)
    """

    print("\n Computing mask coordinates...")

    # Field center (same for all rows — grab first)
#    ra0  = df["ra0_fldU"].iloc[0]
#    dec0 = df["dec0_fldU"].iloc[0]

    row0 = df[0]
    ra0  = row0["ra0_fldU"]
    dec0 = row0["dec0_fldU"]

    ra    = np.array([row["raRadU"]   for row in df])
    dec   = np.array([row["decRadU"]  for row in df])
    theta = np.array([row["pa0_fld"] for row in df])   #change from relpa

    x, y, status = ad_to_xy_vec(
        ra0,
        dec0,
        ra,
        dec,
        theta,
        inst,
    )


   # df["obj_t_x"] = x
   # df["obj_t_y"] = y
    for row, xi, yi in zip(df, x, y):
        row["obj_t_x"] = xi
        row["obj_t_y"] = yi

    # Fortran-style error reporting
    bad = status < 0
    if np.any(bad):
        for name in df.loc[bad, "objectId"]:
            print(f"Transformation error too large: {name}")

    print(f" Proceeding with {len(df):4d} positions...")

    return df


# ============================================================
# Example usage
# ============================================================

if __name__ == "__main__":

    inst = InstrumentConfig(
        x_center=305.0,
        scale=0.7253 * 0.99857,
        mask_angle_deg=8.06,
        mask_bend_deg=1.94,
    )


    df = pd.DataFrame([{'objectId': 'GUI310', 'raHour': 0.6767944444444444, 'decDeg': 40.87046388888889, 'eqx': 2000.0, 'mag': 17.576499938964844, 'pBand': 'F814W', 'pcode': 2, 'sampleNr': 0, 'selected': 1, 'slitLPA': 0.0, 'length1': 5.0, 'length2': 5.0, 'rlength1': 24.3413338666615, 'rlength2': 7.036940753079875, 'slitWidth': 1.0, 'orgIndex': 0, 'inMask': 0, 'raRad': 0.17718437122142097, 'decRad': 0.7133241616785571, 'localselected': 1, 'xarcsS': 411.3483711801043, 'yarcsS': 0.0, 'xarcs': 420.00056773689516, 'yarcs': 0.0, 'length1S': 15.689137309870688, 'length2S': 15.689137309870688, 'slitX1': 312.1810732858256, 'slitX2': 289.1385773622902, 'slitX3': 289.13746568961017, 'slitX4': 312.17987195707576, 'slitY1': -127.47076878992034, 'slitY2': -127.81265007781677, 'slitY3': -127.08012336475899, 'slitY4': -126.73835583136422, 'arcslitX1': 427.03750848997504, 'arcslitX2': 395.6592338702336, 'arcslitX3': 395.6592338702336, 'arcslitX4': 427.03750848997504, 'newcenterRADeg': 10.151916666666665, 'newcenterDECDeg': 40.87046388888889, 'arcslitY1': -0.5, 'arcslitY2': -0.5, 'arcslitY3': 0.5, 'arcslitY4': 0.5, 'ra_fldR': 0.17718437122142097, 'dec_fldR': 0.7132562705156081, 'lst': 0.17718437122142097}])

    df = xypos_df(df, inst)
#    print(df)

    from calc_mill import mill_slit_df
    df = mill_slit_df(df)
#    print(df[["objectId", "millX1", "millY1", "millX2", "millY2", "millX3", "millY3", "millX4", "millY4"]])


def get_mill(df):

    inst = InstrumentConfig(
        x_center=305.0,
        scale=0.7253 * 0.99857,
        mask_angle_deg=8.06,
        mask_bend_deg=1.94,
    )


   

    df = xypos_df(df, inst)

    from calc_mill import mill_slit_df
    df = mill_slit_df(df)
    return df
