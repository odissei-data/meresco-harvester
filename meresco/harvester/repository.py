## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2006-2007 SURFnet B.V. http://www.surfnet.nl
# Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2010-2011, 2015, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2015, 2017, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
#
# This file is part of "Meresco Harvester"
#
# "Meresco Harvester" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Harvester" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Harvester"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from sys import exc_info
from traceback import format_exception
from time import localtime

from .action import Action
from .eventlogger import NilEventLogger
from .oairequest import OAIError, OaiRequest
from .saharaobject import SaharaObject
from .timeslot import Timeslot
from .virtualuploader import UploaderFactory

from gustos.common.units import COUNT
from functools import reduce

nillogger = NilEventLogger()


class Repository(SaharaObject):
    def __init__(self, domainId, repositoryId, oaiRequestClass=None):
        SaharaObject.__init__(self, [
            'repositoryGroupId', 'baseurl', 'set',
            'collection', 'metadataPrefix', 'use',
            'targetId', 'mappingId', 'action',
            'userAgent', 'authorizationKey',
            'complete', 'maximumIgnore', 'continuous'], ['shopclosed'])
        self.domainId = domainId
        self.id = repositoryId
        self.mockUploader = None
        self.uploadfulltext = True
        self._oaiRequestClass = oaiRequestClass or OaiRequest

    def closedSlots(self):
        if not hasattr(self, '_closedslots'):
            if self.shopclosed:
                self._closedslots = [Timeslot(txt) for txt in self.shopclosed]
            else:
                self._closedslots = []
        return self._closedslots

    def shopClosed(self, dateTuple = localtime()[:5]):
        return reduce(lambda lhs, rhs: lhs or rhs, [x.areWeWithinTimeslot( dateTuple) for x in self.closedSlots()], False)

    def target(self):
        return self._proxy.getTargetObject(self.targetId)

    def mapping(self):
        return self._proxy.getMappingObject(self.mappingId)

    def maxIgnore(self):
        return int(self.maximumIgnore) if self.maximumIgnore else 0

    def createUploader(self, logger):
        if self.mockUploader:
            return self.mockUploader
        return UploaderFactory().createUploader(self.target(), logger, self.collection)

    def oairequest(self):
        return self._oaiRequestClass(self.baseurl, userAgent=self.userAgent or None, authorizationKey=self.authorizationKey or None)

    def _createAction(self, stateDir, logDir, generalHarvestLog):
        return Action.create(self, stateDir=stateDir, logDir=logDir, generalHarvestLog=generalHarvestLog)

    def do(self, stateDir, logDir, generalHarvestLog=nillogger, gustosClient=None):
        try:
            if not (stateDir or logDir):
                raise RepositoryException('Missing stateDir and/or logDir')
            action = self._createAction(stateDir=stateDir, logDir=logDir, generalHarvestLog=generalHarvestLog)
            if action.info():
                generalHarvestLog.logLine('START',action.info(), id=self.id)
            actionIsDone, message, hasResumptionToken = action.do()
            if actionIsDone:
                self.action = None
                self._proxy.repositoryActionDone(self.domainId, self.id)
            if message:
                generalHarvestLog.logLine('END', message, id = self.id)
            completeHarvest = hasResumptionToken and self.complete == True
            if completeHarvest:
                generalHarvestLog.logInfo('Repository will be completed in one attempt', id=self.id)
            return message, completeHarvest
        except OAIError as e:
            gustosClient and gustosClient.report(values={ "Harvester": { "Events": { "errors": { COUNT: 1 } } } })
            errorMessage = _errorMessage()
            generalHarvestLog.logError(errorMessage, id=self.id)
            if e.errorCode() == 'badResumptionToken':
                action.resetState()
                return errorMessage, self.complete == True
            return errorMessage, False
        except:
            gustosClient and gustosClient.report(values={ "Harvester": { "Events": { "errors": { COUNT: 1 } } } })
            errorMessage = _errorMessage()
            generalHarvestLog.logError(errorMessage, id=self.id)
            return errorMessage, False


class RepositoryException(Exception):
    pass


def _errorMessage():
    xtype, xval, xtb = exc_info()
    return '|'.join(line.strip() for line in format_exception(xtype, xval, xtb))
