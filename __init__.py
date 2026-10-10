import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from via_stitching_plugin import ViaStitchingPlugin
ViaStitchingPlugin().register()