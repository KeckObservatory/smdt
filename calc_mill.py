import numpy as np
import pandas as pd

# ============================================================
# Instrument / mask / mill constants
# ============================================================

X_CENTER   = 305.0         # mm
Y_CENTER   = 0.0           # mm
YSIDE      = 335.6         # vertical extent of mask (mm)
SCALE      = 0.7253 * 0.99857 # mm/arcsec * ADC scale
SLIT_LEN   = 5.0            # example slit length, mm
CCD_SIDE   = 2048.0
CCD_SCALE  = 0.15767
X_MILL     = 177.8
Y_MILL     = 132.3
XOFF_MILL  = 0.0
YOFF_MILL  = 0.0

# Slitmask astrometry coefficients
A_COEFF = np.array([2.0, 0.99476227, 0.00728125, 0.45412825e-6, -0.40955557e-5, 0.96690643e-6])
B_COEFF = np.array([1.0, -0.00001856, 0.99906324])

# ============================================================
# Astrometry / Mill functions
# ============================================================

def slit_astrometry_vec(xin, yin):
    """
    Vectorized astrometry touchup for arrays of x, y (mm)
    """
    xin = np.asarray(xin)
    yin = np.asarray(yin)

    xccd = CCD_SIDE / 2.0 + (X_CENTER - xin) / CCD_SCALE
    yccd = CCD_SIDE / 2.0 - (Y_CENTER - yin) / CCD_SCALE

    xccd_out = (
        A_COEFF[0] + A_COEFF[1]*xccd + A_COEFF[2]*yccd
        + A_COEFF[3]*xccd*xccd + A_COEFF[4]*yccd*yccd
        + A_COEFF[5]*xccd*yccd
    )
    yccd_out = B_COEFF[0] + B_COEFF[1]*xccd + B_COEFF[2]*yccd

    xout = X_CENTER - (xccd_out - CCD_SIDE / 2.0) * CCD_SCALE
    yout = Y_CENTER + (yccd_out - CCD_SIDE / 2.0) * CCD_SCALE

    return xout, yout

def mill_coords_vec(xin, yin):
    """
    Vectorized mill coordinates from slitmask coordinates (mm)
    """
    xout = (Y_CENTER - yin) + X_MILL + XOFF_MILL
    yout = (xin - X_CENTER) + Y_MILL + YOFF_MILL
    return xout, yout

# ============================================================
# Main function: compute slit corners + mill coordinates
# ============================================================

def mill_slit_df(df, slit_len=SLIT_LEN, print_output=True):
    """
    Compute slit corner coordinates and mill coordinates for a dataframe
    df must contain columns: obj_t_x, obj_t_y, objectId
    """

    X_center = np.array([row["obj_t_x"] for row in df])
    Y_center = np.array([row["obj_t_y"] for row in df])
    ANGLE = np.array([row["relpa"] for row in df])   # radians  This is relative to mask pa --relpa
    hwidth = np.array([0.5*row["slitWidth"]*SCALE for row in df])
    slit_len1 = np.array([row["rlength1"]*SCALE for row in df])
    slit_len2 = np.array([row["rlength2"]*SCALE for row in df])
    selected = np.array([row["selected"] for row in df])


    if True:
        # Vertical extents
        Y1 = Y_center - 0.5 * slit_len1
        Y2 = Y_center + 0.5 * slit_len2

        # Mask edge clipping (same as before)
        Y1 = np.maximum(Y1, Y_CENTER - YSIDE/2.0 + 1)
        Y2 = np.minimum(Y2, Y_CENTER + YSIDE/2.0 - 1)

        # X offsets due to tilt
        tanA = np.tan(ANGLE)

        X1c = X_center + (Y1 - Y_center) * tanA
        X2c = X_center + (Y2 - Y_center) * tanA

        # Apply slit width (HWIDTH already includes CLOCKWISE_MILL)
   
        X1 = X1c - hwidth
        X2 = X2c - hwidth
        X3 = X2c + hwidth
        X4 = X1c + hwidth

        Y3 = Y2.copy()
        Y4 = Y1.copy()

        # Stack corners (CCW, autoslit order)
        X_mask = np.vstack([X1, X2, X3, X4]).T
        Y_mask = np.vstack([Y1, Y2, Y3, Y4]).T

    if False:
        n = len(df)
        # Slit corners in mask coordinates
        #X_center = df["obj_t_x"].to_numpy()
        #Y_center = df["obj_t_y"].to_numpy()
        X_center = np.array([row["obj_t_x"] for row in df])
        Y_center = np.array([row["obj_t_y"] for row in df])

        # Vertical slits (PA=0) for now
        # TODO: update for PA != 0 later
        Y1 = Y_center - 0.5 * slit_len1
        Y2 = Y_center + 0.5 * slit_len2

        # Remove overlap with mask edges
        Y1 = np.maximum(Y1, Y_CENTER - YSIDE/2.0 + 1)
        Y2 = np.minimum(Y2, Y_CENTER + YSIDE/2.0 - 1)

        X1 = X_center.copy() - hwidth
        X2 = X_center.copy() - hwidth
        X3 = X_center.copy() + hwidth
        X4 = X_center.copy() + hwidth

        Y3 = Y2.copy()
        Y4 = Y1.copy()

        # Stack corners into arrays
        X_mask = np.vstack([X1, X2, X3, X4]).T
        Y_mask = np.vstack([Y1, Y2, Y3, Y4]).T
#        print(X_mask)

    # Apply astrometry correction
    X_mask, Y_mask = slit_astrometry_vec(X_mask, Y_mask)

    # Convert to mill coordinates
    X_mill, Y_mill = mill_coords_vec(X_mask, Y_mask)

    # Store in DataFrame
    #df["millX1"] = X_mill[:,0]
    #df["millY1"] = Y_mill[:,0]
    #df["millX2"] = X_mill[:,1]
    #df["millY2"] = Y_mill[:,1]
    #df["millX3"] = X_mill[:,2]
    #df["millY3"] = Y_mill[:,2]
    #df["millX4"] = X_mill[:,3]
    #df["millY4"] = Y_mill[:,3]

    for row, Xm, Ym in zip(df, X_mill, Y_mill):
        row["millX1"] = Xm[0]
        row["millY1"] = Ym[0]
        row["millX2"] = Xm[1]
        row["millY2"] = Ym[1]
        row["millX3"] = Xm[2]
        row["millY3"] = Ym[2]
        row["millX4"] = Xm[3]
        row["millY4"] = Ym[3]


    # Print output in CNC-style format
#    if print_output:
#        for row, Xm, Ym in zip(df, X_mill, Y_mill):
#            print(f"# Object: {row['objectId']}")
#            for i in range(4):
#                print(f"{Xm[i]:12.6f}{Ym[i]:12.6f}{0.0:12.6f}")
#            print()

# --- CNC STYLE CONSOLE OUTPUT ---
    if print_output:
        print("\n# ===== SELECTED OBJECTS =====")
        for row, Xm, Ym, sel in zip(df, X_mill, Y_mill, selected):
            if sel == 1:
                print(f"# Object: {row['objectId']}")
                for i in range(4):
                    print(f"{Xm[i]:12.6f}{Ym[i]:12.6f}{0.0:12.6f}")
                print()

        print("\n# ===== NOT SELECTED OBJECTS =====")
        for row, Xm, Ym, sel in zip(df, X_mill, Y_mill, selected):
            if sel != 1:
                print(f"# Object: {row['objectId']}")
                for i in range(4):
                    print(f"{Xm[i]:12.6f}{Ym[i]:12.6f}{0.0:12.6f}")
                print()


    with open("a.file3", "w") as fout:
        for row, Xm, Ym, sel in zip(df, X_mill, Y_mill, selected):
            if sel == 1:
                print("newrow")
                fout.write("newrow\n")
                for i in range(4):
                    line = f"{Xm[i]:.6f} {Ym[i]:.6f} 0.000000"
                    print(line)
                    fout.write(line + "\n")
                fout.write(f"{Xm[0]:.6f} {Ym[0]:.6f} 0.000000" + "\n") #return to first corner

#    with open("a.file3", "w") as fout:
#        for row, Xm, Ym in zip(df, X_mill, Y_mill):
#            print("newrow")
#            fout.write("newrow\n")
#            for i in range(4):
#                line = f"{Xm[i]:.6f} {Ym[i]:.6f} 0.000000"
#                print(line)              # to terminal
#                fout.write(line + "\n")  # to file


    for row in df:
        print((row["millX1"]+row["millX3"])/2/(0.7253 * 0.99857),(row["millY1"]+row["millY3"])/2/(0.7253 * 0.99857))

    return df

# ============================================================
# Example usage
# ============================================================

if __name__ == "__main__":

    # Example dataframe
    df = pd.DataFrame([{
        "objectId": "GUI310",
        "obj_t_x": 308.04,
        "obj_t_y": 0.27,
        "relpa":0,"slitWidth":1.0,"rlength1":5.0,"rlength2":5.0
    }, {
        "objectId": "GUI3132",
        "obj_t_x": 326.03,
        "obj_t_y": 94.32,
        "relpa":0,"slitWidth":1.0,"rlength1":5.0,"rlength2":5.0
    }])

    df = mill_slit_df([df])
#    print(df)
    #print(df[["objectId", "millX1", "millY1", "millX2", "millY2", "millX3", "millY3", "millX4", "millY4"]])

