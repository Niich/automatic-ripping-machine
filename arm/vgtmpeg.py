#!/usr/bin/python3

import sys
import os
import logging
import subprocess
import re
import shlex
import utils

from config import cfg

def vgtmpeg_mainfeature(srcpath, basepath, logfile, disc):
    """process dvd with mainfeature enabled.\n
    srcpath = Path to source for HB (dvd or files)\n
    basepath = Path where HB will save trancoded files\n
    logfile = Logfile for HB to redirect output to\n
    disc = Disc object\n

    Returns nothing
    """
    logging.info("Starting DVD Movie Mainfeature processing")

    filename = os.path.join(basepath, disc.videotitle + ".dvd")
    filepathname = os.path.join(basepath, filename)

    logging.info("Ripping title Mainfeature to " + shlex.quote(filepathname))

    if disc.disctype == "dvd":
        vg_args = cfg['VG_ARGS_DVD']        
    elif disc.disctype == "bluray":
        vg_args = cfg['VG_ARGS_BD']

<<<<<<< HEAD
    cmd = ' export ld_library_path=/usr/local/lib && nice {0} -i {1} {2} "{3}" >> {4} 2>&1'.format(
=======
    cmd = 'export LD_LIBRARY_PATH=/usr/local/lib && nice {0} -i {1} {2} "{3}" >> {4} 2>&1'.format(
>>>>>>> 70082bc93e3e2f078dd11a7b0dbdb1c37bc220a3
        cfg['VGTMPEG_CLI'],
        shlex.quote(srcpath),
        vg_args,
        shlex.quote(filepathname),
        logfile
        )

    logging.debug("Sending command: %s", (cmd))

    try:
        subprocess.check_output(
            cmd,
            shell=True
        ).decode("utf-8")
        logging.info("Vgtmpeg call successful")
    except subprocess.CalledProcessError as hb_error:
        err = "Call to vgtmpeg failed with code: " + str(hb_error.returncode) + "(" + str(hb_error.output) + ")"
        logging.error(err)
        sys.exit(err)

    logging.info("vgtmpeg processing complete")
    logging.debug(str(disc))
    utils.move_files(basepath, filename, disc.hasnicetitle, disc.videotitle + " (" + disc.videoyear + ")", True)
    utils.scan_emby()

    try:
        os.rmdir(basepath)
    except OSError:
        pass
