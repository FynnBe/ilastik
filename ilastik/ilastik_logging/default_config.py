from __future__ import absolute_import
###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
import os
import logging.config
import warnings
from . import loggingHelpers
from ilastik.config import cfg as ilastik_config

DEFAULT_LOGFILE_PATH = os.path.expanduser("~/ilastik_log.txt")

class OutputMode(object):
    CONSOLE = 0
    LOGFILE = 1
    BOTH = 2
    LOGFILE_WITH_CONSOLE_ERRORS = 3

def get_logfile_path():
    root_handlers = logging.getLogger().handlers
    for handler in root_handlers:
        if isinstance(handler, logging.FileHandler):
            return handler.baseFilename
    return None

def get_default_config( prefix="",
                        output_mode=OutputMode.LOGFILE_WITH_CONSOLE_ERRORS,
                        logfile_path=DEFAULT_LOGFILE_PATH):

    if output_mode == OutputMode.CONSOLE:
        root_handlers = ["console", "console_warn"]
        warnings_module_handlers = ["console_warnings_module"]

    if output_mode == OutputMode.LOGFILE:
        root_handlers = ["rotating_file"]
        warnings_module_handlers = ["rotating_file"]

    if output_mode == OutputMode.BOTH:
        root_handlers = ["console", "console_warn", "rotating_file"]
        warnings_module_handlers = ["console_warnings_module", "rotating_file"]

    if output_mode == OutputMode.LOGFILE_WITH_CONSOLE_ERRORS:
        root_handlers = ["rotating_file", "console_errors_only"]
        warnings_module_handlers = ["rotating_file"]

    default_log_config = {
        "version": 1,
        #"incremental" : False,
        #"disable_existing_loggers": True,
        "formatters": {
            "verbose": {
                "format": "{}%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s".format(prefix)
            },
            "location": {
                #"format": "%(levelname)s %(thread)d %(name)s:%(funcName)s:%(lineno)d %(message)s"
                "format": "{}%(levelname)s %(name)s: %(message)s".format(prefix)
            },
            "timestamped": {
                #"format": "%(levelname)s %(thread)d %(name)s:%(funcName)s:%(lineno)d %(message)s"
                "format": "{}%(levelname)s %(name)s: [%(asctime)s] %(message)s".format(prefix)
            },
            "simple": {
                "format": "{}%(levelname)s %(message)s".format(prefix)
            },
        },
        "filters" : {
            "no_warn" : {
                "()":"ilastik.ilastik_logging.loggingHelpers.NoWarnFilter"
            }
        },
        "handlers": {
            "console":{
                "level":"DEBUG",
                "class":"logging.StreamHandler",
                "stream":"ext://sys.stdout",
                "formatter": "location",
                "filters":["no_warn"] # This handler does NOT show warnings (see below)
            },
            "console_timestamp":{
                "level":"DEBUG",
                "class":"logging.StreamHandler",
                "stream":"ext://sys.stdout",
                "formatter": "timestamped",
                "filters":["no_warn"] # Does not show warnings
            },
            "console_warn":{
                "level":"WARN", # Shows ONLY warnings and errors, on stderr
                "class":"logging.StreamHandler",
                "stream":"ext://sys.stderr",
                "formatter":"verbose"
            },
            "console_errors_only":{
                "level":"ERROR", # Shows ONLY errors, on stderr
                "class":"logging.StreamHandler",
                "stream":"ext://sys.stderr",
                "formatter":"verbose"
            },
            "console_warnings_module":{
                "level":"WARN",
                "class":"logging.StreamHandler",
                "stream":"ext://sys.stderr",
                "formatter":"simple"
            },
            "console_trace":{
                "level":"DEBUG",
                "class":"logging.StreamHandler",
                "stream":"ext://sys.stdout",
                "formatter": "verbose"
            },
            "rotating_file":{
                "level":"DEBUG",
                "class":"logging.handlers.RotatingFileHandler",
                "filename" : logfile_path,
                "maxBytes":20e6, # 20 MB
                "backupCount":5,
                "formatter":"verbose",
                "encoding": "utf-8"
            },
        },
        "root": {
            "handlers": root_handlers,
            "level": "INFO",
            "encoding": "utf-8"
        },
        "loggers": {
            # This logger captures warnings module warnings
            "py.warnings":                             {  "level":"WARN", "encoding": "utf-8", "handlers":warnings_module_handlers, "propagate": False },

            "PyQt5": {"level": "INFO", "encoding": "utf-8"},

            # The requests module spits out a lot of INFO messages by default.
            "requests": {"level":"WARN", "encoding": "utf-8"},

            "wsdt": {"level": "INFO", "encoding": "utf-8"},

            # When copying to a json file, remember to remove comments and change True/False to true/false
            "__main__":                                                 { "level": "INFO", "encoding": "utf-8"  },
            "ilastik_main":                                             { "level": "INFO", "encoding": "utf-8"  },
            "thread_start":                                             { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow":                                                 { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.request":                                         { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.request.RequestLock":                             { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.request.SimpleRequestCondition":                  { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.graph":                                           { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.graph.Slot":                                      { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.operators":                                       { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.classifiers":                                     { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.operators.ioOperators":                           { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.operators.ioOperators.opRESTfulVolumeReader":     { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.operators.cacheMemoryManager.CacheMemoryManager": { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.operators.vigraOperators":                        { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.operators.ioOperators.ioOperators.OpH5WriterBigDataset":   { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.operators.classifierOperators":                   { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.operators.opCompressedCache":                     { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.operators.opRelabelConsecutive":                  { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.utility.io_util.RESTfulVolume":                        { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.utility.io_util.tiledVolume":                          { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.operators.opFeatureMatrixCache":                  { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.operators.opConcatenateFeatureMatrices":          { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.utility.roiRequestBatch":                         { "level": "INFO", "encoding": "utf-8"  },
            "lazyflow.utility.bigRequestStreamer":                      { "level": "INFO", "encoding": "utf-8"  },
            "ilastik":                                                  { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.clusterOps":                                       { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.applets":                                          { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.applets.base.appletSerializer":                    { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.applets.dataSelection":                            { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.applets.featureSelection":                         { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.applets.pixelClassification":                      { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.applets.thresholdTwoLevels":                       { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.applets.thresholdTwoLevels.ipht":                  { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.applets.objectExtraction":                         { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.applets.blockwiseObjectClassification":            { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.applets.tracking.conservation":                    { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.shell":                                            { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.shell.projectManager":                             { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.shell.gui.ipcManager":                             { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.workflows":                                        { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.widgets":                                          { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.utility":                                          { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.utility.exportingOperator":                        { "level": "INFO", "encoding": "utf-8"  },
            "ilastik.utility.exportFile":                               { "level": "INFO", "encoding": "utf-8"  },
            "workflows":                                                { "level": "INFO", "encoding": "utf-8"  },
            "volumina":                                                 { "level": "INFO", "encoding": "utf-8"  },
            "volumina.pixelpipeline":                                   { "level": "INFO", "encoding": "utf-8"  },
            "volumina.imageScene2D":                                    { "level": "INFO", "encoding": "utf-8"  },
            "volumina.utility.shortcutManager":                         { "level": "INFO", "encoding": "utf-8"  },
            # Python doesn't provide a trace log level, so we use a workaround.
            # By convention, trace loggers have the same hierarchy as the regular loggers, but are prefixed with 'TRACE' and always emit DEBUG messages
            # To enable trace messages, change one or more of these to use level DEBUG
            "TRACE": { "level": "INFO", "encoding": "utf-8" , "handlers":["console_trace","console_warn"] },
            "TRACE.lazyflow.graph.Slot":                                { "level": "INFO", "encoding": "utf-8"  },
            "TRACE.lazyflow.graph.Operator":                            { "level": "INFO", "encoding": "utf-8"  },
            "TRACE.lazyflow.graph.OperatorWrapper":                     { "level": "INFO", "encoding": "utf-8"  },
            "TRACE.lazyflow.operators.ioOperators":                     { "level": "INFO", "encoding": "utf-8"  },
            "TRACE.lazyflow.operators":                                 { "level": "INFO", "encoding": "utf-8"  },
            "TRACE.lazyflow.operators.operators":                       { "level": "INFO", "encoding": "utf-8"  },
            "TRACE.lazyflow.operators.generic":                         { "level": "INFO", "encoding": "utf-8"  },
            "TRACE.lazyflow.operators.classifierOperators":             { "level": "INFO", "encoding": "utf-8"  },
            "TRACE.lazyflow.operators.operators.ArrayCacheMemoryMgr":   { "level": "INFO", "encoding": "utf-8"  },
            "TRACE.lazyflow.operators.valueProviders.OpValueCache":     { "level": "INFO", "encoding": "utf-8"  },
            "TRACE.ilastik.clusterOps":                                 { "level": "INFO", "encoding": "utf-8"  },
            "TRACE.ilastik.applets":                                    { "level": "INFO", "encoding": "utf-8"  },
            "TRACE.ilastik.applets.blockwiseObjectClassification":      { "level": "INFO", "encoding": "utf-8"  },
            "TRACE.ilastik.shell":                                      { "level": "INFO", "encoding": "utf-8"  },
            "TRACE.volumina":                                           { "level": "INFO", "encoding": "utf-8"  },
            "TRACE.volumina.imageScene2D":                              { "level": "INFO", "encoding": "utf-8"  }
        }
    }
    return default_log_config

def init(format_prefix="", output_mode=OutputMode.LOGFILE_WITH_CONSOLE_ERRORS, logfile_path=DEFAULT_LOGFILE_PATH):
    if logfile_path == "/dev/null":
        assert output_mode != OutputMode.LOGFILE, "Must enable a logging mode."
        output_mode = OutputMode.CONSOLE

    # Preserve pre-existing handlers
    original_root_handlers = list(logging.getLogger().handlers)

    # Start with the default
    default_config = get_default_config( format_prefix, output_mode, logfile_path )
    logging.config.dictConfig( default_config )

    # Preserve pre-existing handlers
    for handler in original_root_handlers:
        logging.getLogger().addHandler(handler)

    # Update from the user's customizations
    loggingHelpers.updateFromConfigFile()

    # Capture warnings from the warnings module
    logging.captureWarnings(True)

    # Warnings module warnings are shown only once
    warnings.filterwarnings("once")

    # Don't warn about pending deprecations (PyQt generates some of these)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

    # Don't warn about duplicate python bindings for opengm
    # (We import opengm twice, as 'opengm' 'opengm_with_cplex'.)
    warnings.filterwarnings("ignore", message='.*to-Python converter for .*opengm.*', category=RuntimeWarning)

    # Hide all other python converter warnings unless we're in debug mode.
    if not ilastik_config.getboolean("ilastik", "debug"):
        warnings.filterwarnings("ignore", message='.*to-Python converter for .*second conversion method ignored.*', category=RuntimeWarning)


    # Custom format for warnings
    def simple_warning_format(message, category, filename, lineno, line=None):
        filename = os.path.split(filename)[1]
        return filename + "(" + str(lineno) + "): " + category.__name__ + ": " + message.args[0]

    warnings.formatwarning = simple_warning_format

