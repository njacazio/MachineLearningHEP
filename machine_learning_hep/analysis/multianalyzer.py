#############################################################################
##  © Copyright CERN 2018. All rights not expressly granted are reserved.  ##
##                 Author: Gian.Michele.Innocenti@cern.ch                  ##
## This program is free software: you can redistribute it and/or modify it ##
##  under the terms of the GNU General Public License as published by the  ##
## Free Software Foundation, either version 3 of the License, or (at your  ##
## option) any later version. This program is distributed in the hope that ##
##  it will be useful, but WITHOUT ANY WARRANTY; without even the implied  ##
##     warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    ##
##           See the GNU General Public License for more details.          ##
##    You should have received a copy of the GNU General Public License    ##
##   along with this program. if not, see <https://www.gnu.org/licenses/>. ##
#############################################################################

"""
main script for doing data processing, machine learning and analysis
"""
import os
from machine_learning_hep.utilities import mergerootfiles, get_timestamp_string
from machine_learning_hep.logger import get_logger
class MultiAnalyzer: # pylint: disable=too-many-instance-attributes, too-many-statements
    species = "multianalyzer"
    def __init__(self, analyzer_class, datap, case, typean, doperiodbyperiod):
        self.logger = get_logger()
        self.datap = datap
        self.typean = typean
        self.case = case
        self.d_resultsallpmc = datap["analysis"][self.typean]["mc"]["resultsallp"]
        self.d_resultsallpdata = datap["analysis"][self.typean]["data"]["resultsallp"]
        self.d_resultsmc = datap["analysis"][self.typean]["mc"]["results"]
        self.d_resultsdata = datap["analysis"][self.typean]["data"]["results"]
        self.d_valevtdata = datap["validation"]["data"]["dir"]
        self.d_valevtmc = datap["validation"]["mc"]["dir"]
        self.d_valevtallpdata = datap["validation"]["data"]["dirmerged"]
        self.d_valevtallpmc = datap["validation"]["mc"]["dirmerged"]
        self.n_evtvalroot = datap["files_names"]["namefile_evtvalroot"]
        self.prodnumber = len(self.d_resultsmc)
        # Prepare a list of analyzers. The last entry is the analyzer for all periods merged.
        self.process_listsample = [None] * (self.prodnumber + 1)
        self.p_useperiod = datap["analysis"][self.typean]["useperiod"]
        self.doperiodbyperiod = doperiodbyperiod
        # Add period-wise analyzers if given period is enabled
        for indexp in range(self.prodnumber):
            if doperiodbyperiod and self.p_useperiod[indexp]:
                self.process_listsample[indexp] = analyzer_class(self.datap, case, typean,
                                                                 self.d_resultsdata[indexp],
                                                                 self.d_resultsmc[indexp],
                                                                 self.d_valevtdata[indexp],
                                                                 self.d_valevtmc[indexp])
        # Add the periods-merged analyzer
        self.process_listsample[self.prodnumber] = analyzer_class(self.datap, case, typean,
                                                                  self.d_resultsallpdata,
                                                                  self.d_resultsallpmc,
                                                                  self.d_valevtallpdata,
                                                                  self.d_valevtallpmc)

        self.lper_normfilesorig = []
        self.lper_normfiles = []
        self.dlper_valevtroot = datap["validation"]["data"]["dir"]
        for i, _ in enumerate(self.d_resultsdata):
            self.lper_normfilesorig.append(os.path.join(self.dlper_valevtroot[i], \
                                                   "correctionsweights.root"))
            self.lper_normfiles.append(os.path.join(self.d_resultsdata[i], \
                                                   "correctionsweights.root"))
        self.f_normmerged = os.path.join(self.d_resultsallpdata, \
                                                    "correctionsweights.root")

    def analyze(self, *ana_steps):
        # Collect potentially failed analysis steps
        failed_steps = []
        for step in ana_steps:
            for analyzer in self.process_listsample:
                if not analyzer:
                    continue
                if not analyzer.analysis_step(step):
                    failed_steps.append((analyzer.__class__.__name__, step))
        if failed_steps:
            self.logger.error("Following analysis steps could not be found:")
            for fs in failed_steps:
                print(f"Analyzer class: {fs[0]}, anqalysis step: {fs[1]}")

    def multi_preparenorm(self):
        listempty = []
        tmp_merged = \
                f"/data/tmp/hadd/{self.case}_{self.typean}/norm_analyzer/{get_timestamp_string()}/"
        for indexp in range(self.prodnumber):
            mergerootfiles([self.lper_normfilesorig[indexp]], self.lper_normfiles[indexp],
                           tmp_merged)
        if self.doperiodbyperiod is True:
            for indexp in range(self.prodnumber):
                if self.p_useperiod[indexp] == 1:
                    listempty.append(self.lper_normfiles[indexp])
        mergerootfiles(listempty, self.f_normmerged, tmp_merged)