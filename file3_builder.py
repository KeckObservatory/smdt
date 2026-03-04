from datetime import datetime

def normalize_params(p):
    numeric_keys = [
        "Temperature",
        "Pressure",
        "CenterWaveLength",
        "MaskPA",
        "HourAngle",
        "SlitWidth",
        "MinSlitLength",
        "MinSlitSeparation",
    ]

    for k in numeric_keys:
        if k in p:
            try:
                p[k] = float(p[k])
            except (ValueError, TypeError):
                p[k] = 0.0

    return p



def build_header(selected,p):
    """
    Build AUTOSLIT file3 header with strict legacy formatting.

    All numeric values come from dict `p`.
    """
    p=normalize_params(p)
    now = p.get("timestamp", datetime.utcnow())
    ra_h,ra_m,ra_s=p['InputRA'].split(':')
    ra_h = int(ra_h)
    ra_m = int(ra_m)
    ra_s = float(ra_s)
    dec_d,dec_m,dec_s=p['InputDEC'].split(':')
    dec_d = int(dec_d)
    dec_m = int(dec_m)
    dec_s = float(dec_s)
    content = ""

    # --- Banner ---
    content += "(                                               )\n"
    content += "(  ****       AUTOSLIT  3.0 OUTPUT        ****  )\n"
    content += f"(  ****     {now:%a %b %d %H:%M:%S %Y}      ****  )\n"
    content += "(  ****                                   ****  )\n"
    content += f"(  ****  {p['Author']:<33}****  )\n"
    content += f"(  ****     {p['Author'].split('@', 1)[1]:<28}****  )\n"
    content += "(                                               )\n"
    content += "(                                               )\n"

    # --- Files ---
    content += "(  ===========================================  )\n"
    content += "(              Autoslit Parameters              )\n"
    content += "(  -------------------------------------------  )\n"
    content += "(                                               )\n"
    content += "(  Files:                                       )\n"
    content += "(  -------------------------------------------  )\n"
    content += f"(  Input object file:              {(p['OutputFits'][:-5] if p['OutputFits'].endswith('.fits') else p['OutputFits']) + '.out':<12} )\n"
    content += f"(  Output listing file:            {'file1':<12} )\n"
    content += f"(  Output stage coordinate file:   {'file2':<12} )\n"
    content += f"(  Output file for the punch/mill: {'file3':<12} )\n"
    content += "(  -------------------------------------------  )\n"
    content += "(                                               )\n"

    # --- Physical parameters ---
    content += "(  Physical parameters:     [default]  [input]  )\n"
    content += "(  -------------------------------------------  )\n"
    content += f"(  Temperature [C]:          {0:8.1f}{p['Temperature']:10.1f}  )\n"
    content += f"(  Air pressure [mm of Hg]:  {486:8.1f}{p['Pressure']:10.1f}  )\n"
    content += f"(  Latitude:                 {19.83:8.2f}{19.83:10.2f}  )\n"
    content += f"(  Wavelength [A]:           {6000:8.1f}{p['CenterWaveLength']:10.1f}  )\n"
    content += f"(  Position angle:           {0:8.2f}{p['MaskPA']:10.2f}  )\n"
    content += f"(  Hour angle:               {0:8.2f}{p['HourAngle']:10.2f}  )\n"
    content += f"(  Epoch:                   [today]{2000:9.2f}  )\n"
    content += f"(  Slit width [arc-sec]:     {1.0:8.2f}{p['SlitWidth']:10.2f}  )\n"
    content += f"(  Slit length [arc-sec]:    {5:8.2f}{p['MinSlitLength']:10.2f}  )\n"
    content += f"(  Slit separation [arc-sec]:{0.5:8.2f}{p['MinSlitSeparation']:10.2f}  )\n"
    content += "(  -------------------------------------------  )\n"
    content += "(                                               )\n"

    # --- Slit layout ---
    content += "(  Slit layout parameters:                      )\n"
    content += "(  -------------------------------------------  )\n"
    content += f"(  Top half of mask:    {'*single* rank of slits':<23} )\n"
    content += f"(  Bottom half of mask: {'*single* rank of slits':<23} )\n"
    content += f"(  Special plot symbols have priority  > {750:6d}  )\n"
    content += f"(  Slit selection:                 {'interactive':<11} )\n"
    content += f"(  Pickoff mirror in use:          {'FALSE':<5}  )\n"
    content += f"(  Engineering run:                {'FALSE':<5}  )\n"
    content += "(  -------------------------------------------  )\n"
    content += "(                                               )\n"

    # --- Inventory ---
    content += "(  Slit inventory:           assigned/declared  )\n"
    content += "(  -------------------------------------------  )\n"
    content += f"(  Number of standard slits:        {(selected.pcode > 0).sum():10d}  )\n"
    content += f"(  Number of boxes:            {(selected.pcode == -2).sum():3d}/{(selected.pcode == -2).sum():<3d}  )\n"
    content += f"(  Number of tilted slits:     {((selected.pcode > 0) & (selected.relpa != 0)).sum():3d}/{((selected.pcode >0) & (selected.relpa != 0)).sum():<3d}  )\n"
    content += f"(  Number of arc slits:        {0:3d}/{0:<3d}  )\n"
    content += f"(  Number of line segment slits:{0:3d}/{0:<3d}  )\n"
    content += "(  ===========================================  )\n"
    content += "(                                               )\n"

    # --- Center of field ---
    content += "(  ===========================================  )\n"
    content += "(                Center of Field                )\n"
    content += "(  -------------------------------------------  )\n"
    content += "(  Center of Field is:                          )\n"
    content += f"(  RA  =   {ra_h:2d}h   {ra_m:2d}m  {ra_s:7.3f}s    [{2000:7.2f}]      )\n"
    content += f"(  DEC =   {dec_d:3d}d   {dec_m:2d}m  {dec_s:7.3f}s                   )\n"
    content += "(  ===========================================  )\n\n"

    return content

