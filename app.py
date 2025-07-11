from flask import Flask, render_template, request, jsonify, send_file, make_response, session
from flask.logging import default_handler
from flask_session import Session
from flask_cors import CORS
import webbrowser
import numpy as np
import maskLayouts as ml
import os
import json
import numpy as np
import targs
import calcmask
import json
import plot
import logging
from logging import FileHandler, StreamHandler
import tarfile
import logging
from functools import wraps
from utils import schema, validate_params, stripquote
from io import BytesIO
import utils as util
import pdb

logger = logging.getLogger('smdt')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger.setLevel(logging.INFO)
logger.addHandler(default_handler)
st = StreamHandler()
st.setLevel(logging.INFO)
st.setFormatter(formatter)
fh = FileHandler('smdt.log')
fh.setFormatter(formatter)
logger.addHandler(fh)


# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def log_function_call(func):
    """Decorator to log function calls"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(
            f"Function '{func.__name__}' called with args: {args} kwargs: {kwargs}")
        result = func(*args, **kwargs)
        logging.info(f"Function '{func.__name__}' returned: {result}")
        return result
    return wrapper


def launchBrowser(host, portnr, path):
    webbrowser.open(f"http://{host}:{portnr}/{path}", new=1)


app = Flask(__name__)
app.config.from_pyfile('config.py')
Session(app)
CORS(app, supports_credentials=True)


@app.before_request
def log_request():
    logging.info(
        f"Request made to: {request.path} with method {request.method}")


# @app.route('/readparams')
def readparams():
    dict = {}
    with open('params.cfg') as f:
        for line in f:
            try:
                if len(line.split(',')) == 4:
                    sep = line.strip().split(',')
                    (k, v) = sep[0].split(' = ')
                    dict[k] = (stripquote(v), stripquote(sep[1]),
                               stripquote(sep[2]), stripquote(sep[3]))
                else:
                    continue
            except Exception as e:
                pass
                print('Failed to load parameters', e)
    return dict


@app.route('/setColumnValue', methods=["GET", "POST"])
def setColumnValue():
    values = request.json['value']
    column = request.json['column']
    logger.info(f"Setting column {column} to value {values}")
    logger.info(f"session keys: {session.keys()}")
    logger.info(f"session targetList: {session.get('targetList')}")
    session['targetList'] = targs.update_column(
        session['targetList'], column, values)
    session.modified = True
    return {'status': 'OK', 'targets': session['targetList']}


@app.route('/updateTarget', methods=["GET", "POST"])
def updateTarget():
    values = request.json['values']
    session['targetList'], idx = targs.update_target(
        session['targetList'], values)
    session.modified = True
    outp = targs.to_json_with_info(session['params'], session['targetList'])
    return {**outp, 'idx': idx, "info": targs.getROIInfo(session['params'])}


@app.route('/updateSelection', methods=["GET", "POST"])
def updateSelection():
    values = request.json['values']
    session['targetList'], idx = targs.update_target(
        session['targetList'], values)
    session.modified = True
    outp = targs.to_json_with_info(session['params'], session['targetList'])
    return {**outp, 'idx': idx, "info": targs.getROIInfo(session['params'])}


@app.route('/deleteTarget', methods=["GET", "POST"])
def deleteTarget():
    idx = request.json['idx']
    if idx < len(session['targetList']):
        session['targetList'].pop(idx)
        session.modified = True
    else:
        logger.debug('Invalid idx. Not deleting')
    outp = targs.to_json_with_info(session['params'], session['targetList'])
    outp = {**outp, 'idx': idx, "info": targs.getROIInfo(session['params'])}
    return outp


@app.route('/resetSelection', methods=["GET", "POST"])
def resetSelection():
    session['targetList'] = [{**target, 'selected': target['localselected']}
                             for target in session['targetList']]
    session.modified = True
    outp = targs.to_json_with_info(session['params'], session['targetList'])
    return {**outp, "info": targs.getROIInfo(session['params'])}


@app.route('/generateSlits', methods=["GET", "POST"])
def generateSlits():
    session['targetList'] = targs.mark_inside(session['targetList'])
    # auto_sel=False, since everything is already selected by this point?
    session['targetList'] = calcmask.gen_slits(
        session['targetList'], session['params'], auto_sel=False)
    session.modified = True
    outp = targs.to_json_with_info(session['params'], session['targetList'])
    return outp


## Performs auto-selection of slits##

@app.route('/recalculateMask', methods=["GET", "POST"])
def recalculateMask():
    session['targetList'] = targs.mark_inside(session['targetList'])
    session['targetList'] = calcmask.gen_slits(
        session['targetList'], session['params'], auto_sel=True)
    session.modified = True
    outp = targs.to_json_with_info(session['params'], session['targetList'])
    return outp


@app.route('/saveMaskDesignFile', methods=["GET", "POST"])
def saveMaskDesignFile():  # should only save current rather than re-running everything!
    logger.info('Saving mask design file')
    try:
        session['targetList'] = targs.mark_inside(session['targetList'])
        outp = {'status': 'OK', **
                targs.to_json_with_info(session['params'], session['targetList'])}
        mdfName = os.path.join(
            session['params']['OutputFits']).replace('.fits', '')
        names = [f'{mdfName}.fits', f'{mdfName}.out',
                 f'{mdfName}.png', f'{mdfName}.json']
        mdf, session['targetList'] = calcmask.gen_mask_out(
            session['targetList'], session['params'])
        session.modified = True
        tarStream = BytesIO()
        with tarfile.open(fileobj=tarStream, mode='w') as tar:
            # Add files to the tar archive
            fits_data = BytesIO()
            mdf.writeTo(fits_data)
            fits_data.seek(0)
            tarinfo = tarfile.TarInfo(name=names[0])
            tarinfo.size = len(fits_data.getvalue())
            tar.addfile(tarinfo, fits_data)

            out_data=BytesIO()
            mdf.writeOut(out_data)
            out_data.seek(0)
            tarinfo = tarfile.TarInfo(name=names[1])
            tarinfo.size = len(out_data.getvalue())
            tar.addfile(tarinfo, out_data)

            plot_data = BytesIO()
            # slitdata=f[7].data
            # typedata=f[4].data
            slit = mdf.genBluSlits()
            type = mdf.genDesiSlits()
            plt = plot.makeplot(slit.data, type.data, names[0])
            plt.savefig(plot_data, format='png')
            plot_data.seek(0)
            tarinfo = tarfile.TarInfo(name=names[2])
            tarinfo.size = len(plot_data.getvalue())
            tar.addfile(tarinfo, plot_data)
            json_data = BytesIO(json.dumps(
                outp, ensure_ascii=False, indent=4).encode('utf-8'))
            tarinfo = tarfile.TarInfo(name=names[3])
            tarinfo.size = len(json_data.getvalue())
            tar.addfile(tarinfo, json_data)

        tarStream.seek(0)

        # Send the tar file as a response
        return send_file(
            tarStream,
            as_attachment=True,
            download_name=f"{mdfName}.tar.gz",
            mimetype="application/gzip"
        )
    except Exception as err:
        logger.error(f'Exception {err}')
        response = make_response(
            jsonify({'status': 'ERR', 'msg': str(err)}), 500)
        response.headers["X-Exception"] = str(err)
        return response

# Update Params Button, Load Targets Button


@app.route('/sendTargets2Server', methods=["GET", "POST"])
def sendTargets2Server():
    filename = request.json.get('filename')
    if not filename:
        return
    session['params'] = request.json['formData']
    # need to set number params to floats
    for key, val in session['params'].items():
        try:
            if 'number' in schema['properties'].get(key, {}).get('type', []):
                session['params'][key] = float(val)
        except Exception as err:
            logger.warning(f'Failed to convert {key} to float: {err}')
            pass
    fh = [line for line in request.json['file'].split('\n') if line]
    session['targetList'] = targs.readRaw(fh, session['params'])
    # check if ra dec is 0, 0, if so, set to first target
    if session['params'].get('InputRA') == ' 00:00:00.00' and session['params'].get('InputDEC') == ' 00:00:00.00' and not session.get('targetList') is None:
        session['params']['InputRA'] = util.toSexagecimal(session['targetList'][0]['raHour'])
        session['params']['InputDEC'] = util.toSexagecimal(session['targetList'][0]['decDeg'])
    # Only backup selected targets on file load.
    session['targetList'] = [{**target, 'localselected': target['selected']}
                             for target in session['targetList']]

    # generate slits
#    session['targetList'] = calcmask.gen_obs(session['targetList'], session['params'])
    session['targetList'] = targs.mark_inside(session['targetList'])
    session['targetList'] = calcmask.gen_slits(
        session['targetList'], session['params'], auto_sel=False)
    session.modified = True

    outp = targs.to_json_with_info(session['params'], session['targetList'])
    outp = {**outp, 'status': 'OK'}
    return outp


@app.route('/updateParams4Server', methods=["GET", "POST"])
def updateParams4Server():
    session['params'] = request.json['formData']
    print(session['params'])
    # ok, session['params'] = validate_params(session['params'])
    ok = True
    if not ok:
        return [str(x) for x in session['params']]

    if 'targetList' not in session:
        session['targetList'] = []
    session['targetList'] = targs.mark_inside(session['targetList'])
    session['targetList'] = calcmask.gen_slits(
        session['targetList'], session['params'], auto_sel=False)
    session.modified = True
    outp = targs.to_json_with_info(session['params'], session['targetList'])
    outp = {**outp, 'status': 'OK'}
    return outp


# Loads original params
@app.route('/getSchema')
def getConfigParams():
    logger.debug(f'Param Schema: {schema}')
    session['got schema'] = True
    return jsonify(schema)


@app.route('/getMaskLayout')
def getMaskLayout():
    """
    Gets the mask layout, which is defined in maskLayout.py as a python data structure for convenience.
    MaskLayoput, GuiderFOV and Badcolumns are defined in maskLayouts.py

    Returns a JSON with mask, guiderFOC and badColumns
    """
    try:
        instrument = "deimos"
        # a list of (x,y,flag), polygon vertices
        mask = ml.MaskLayouts[instrument]
        # list of (x, y, w, h, ang), boxes
        guiderFOV = ml.GuiderFOVs[instrument]
        badColumns = ml.BadColumns[instrument]  # list of lines, as polygons
        # might need to be jsonified
        return {"mask": mask, "guiderFOV": guiderFOV, "badColumns": badColumns}
    except Exception as err:
        logger.error(err)
        return ((0, 0, 0),)


@app.route('/')
def home():
    return render_template('dt.html')


@app.route("/targets", methods=["GET", "POST"])
def LoadTargets():
    return


if __name__ == '__main__':
    # t = Timer(1, launchBrowser, ['localhost', 9302, '/'])
    # t.start()
    app.run(host='localhost', port=9302, debug=True, use_reloader=False)
