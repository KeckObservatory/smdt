from astropy.io import fits
import maskLayouts
import drawUtils
import utils
import matplotlib
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import logging
logger = logging.getLogger('smdt')
matplotlib.use('agg')
import os

def pf(filename):
    segments = []
    current_segment = []

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()

            # Skip blank lines
            if not line:
                continue

            # Skip comment / header lines
            if line.startswith('('):
                continue

            # Start a new segment
            if line.lower().startswith('newrow'):
                if current_segment:          # save previous segment
                    segments.append(current_segment)
                    current_segment = []
                continue

            # Otherwise it should be coordinates
            parts = line.split()
            if len(parts) >= 2:
                x = float(parts[0])
                y = float(parts[1])
                current_segment.append((x, y))

    # Add the last segment if file didn’t end with newrow
    if current_segment:
        segments.append(current_segment)

    # ---- Plotting ----
    plt.figure()

    for seg in segments:
        xs = [p[0] for p in seg]
        ys = [p[1] for p in seg]
        plt.plot(xs, ys, alpha=0.4)   # draws line from (x,y) to next (x,y)

    plt.gca().set_aspect('equal', adjustable='box')
#    plt.xlabel("X")
#    plt.ylabel("Y")
#    plt.title("Segments from m31.file3")
#    plt.show()






def makeplot(slitdata, typedata, plotname,inst):
    sx1,sx2,sx3,sx4=[],[],[],[]
    sy1,sy2,sy3,sy4=[],[],[],[]
    col=[]


    for i in range(len(slitdata)):
        logger.debug(f'slitdata: {slitdata[i]}')
        print(slitdata[i][4])
        x,y=(slitdata[i][3],slitdata[i][4])
        print(y)
        sx1.append(x)
        sy1.append(y)
        x,y=(slitdata[i][5],slitdata[i][6])
        sx2.append(x)
        sy2.append(y)
        x,y=(slitdata[i][7],slitdata[i][8])
        sx3.append(x)
        sy3.append(y)
        x,y=(slitdata[i][9],slitdata[i][10])
        sx4.append(x)
        sy4.append(y)
        if typedata[i][5]=='P':      #color blue for slits
            col.append('royalblue')
#        elif typedata[i][5]=='G':    #color gold for guidestars - but will never appear in slitdata commenting out
#            col.append('gold')
        elif typedata[i][5]=='A':    #color purple for alignment boxes
            col.append('violet')
        else:
            #can't identify slit type?
            col.append('crimson')    #color red if something else

    fig, sps = plt.subplots(1, figsize=(16, 5))
    plt.subplot(111)
    plt.title (os.path.splitext(os.path.basename(plotname))[0])

    ax=plt.gca()
    ZPT_YM=128.803
    layout = maskLayouts.MaskLayouts[inst]
    if inst=='deimos':
        layoutMM = maskLayouts.scaleLayout(layout, utils.AS2MM, 0, -ZPT_YM) ###
    if inst=='lris':
        layoutMM = maskLayouts.scaleLayout(layout, utils.AS2MM, 177.8-305, 132.3) ###

    drawUtils.drawPatch(ax, layoutMM, fc="None", ec="g")
  
    for i in range(len(sx1)):
        if col[i]=='gold':
            plt.scatter((sx1[i]+sx2[i]+sx3[i]+sx4[i])/4,(sy1[i]+sy2[i]+sy3[i]+sy4[i])/4,s=30,facecolors='none',edgecolors=col[i],alpha=0.9,label='Guide Star')
            pass
        elif col[i]=='violet':
            plt.plot([sx1[i],sx2[i],sx3[i],sx4[i],sx1[i]],[sy1[i],sy2[i],sy3[i],sy4[i],sy1[i]],color=col[i],alpha=0.8,label='Alignment Box')
        elif col[i]=='royalblue':
            plt.plot([sx1[i],sx2[i],sx3[i],sx4[i],sx1[i]],[sy1[i],sy2[i],sy3[i],sy4[i],sy1[i]],color=col[i],alpha=0.8,label='Target slit')
        else:
            plt.plot([sx1[i],sx2[i],sx3[i],sx4[i],sx1[i]],[sy1[i],sy2[i],sy3[i],sy4[i],sy1[i]],color=col[i],alpha=0.8,label='Unknown')

    if inst=='deimos':
        plt.gca().invert_xaxis()
    plt.grid()
    plt.legend([Line2D([], [], color='violet'),Line2D([], [], color='royalblue')],['Alignment Box','Target slit'],loc="upper left")




    return plt
