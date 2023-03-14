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
# Copyright (C) 2011, 2013, 2015, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2011, 2015, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
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

from meresco.harvester.onlineharvest import OnlineHarvest
from io import StringIO
from meresco.harvester.mapping import Mapping, DataMapAssertionException, DEFAULT_DC_CODE
import os
from seecr.test import CallTrace, SeecrTestCase

class OnlineHarvestTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.mock_createUpload_exception = ''
        self._testpath = os.path.realpath(os.path.curdir)
        self.output = StringIO()
        self.mappingData = dict(identifier="mappingId", code=DEFAULT_DC_CODE)
        self.mapping = Mapping('mappingId')
        self.mapping.code = DEFAULT_DC_CODE
        self.harvest = OnlineHarvest(self.output)

    def testRealMapping(self):
        data = 'file://%s/mocktud/00002.xml' % self._testpath
        self.harvest.performMapping(self.mappingData, data)
        self.assertEqual(3,self.output.getvalue().count('upload.id='))

    def testMapping(self):
        upload = CallTrace('upload')
        upload.id = 'id'
        upload.isDeleted = True
        mapping = CallTrace()
        mapping.returnValues['createUpload'] = upload
        self.harvest = OnlineHarvest(self.output)
        data = 'file://%s/mocktud/00002.xml' % self._testpath
        self.harvest.performMapping(None, data, mapping)
        self.assertEqual(['addObserver', 'mappingInfo', 'createUpload', 'createUpload', 'createUpload'], [m.name for m in mapping.calledMethods])
        for createUploadMethod in mapping.calledMethods[2:]:
            self.assertTrue(createUploadMethod.kwargs['doAsserts'])

    def testMappingWithDeletedRecord(self):
        data = 'file://%s/mocktud/00003.xml' % self._testpath
        self.harvest.performMapping(dict(identifier='mappingId', code=DEFAULT_DC_CODE, name="My Mapping"), data)
        self.assertEqual("Mappingname 'My Mapping'\n\nupload.id=repository.id:oai:tudelft.nl:107087\nDELETED", self.output.getvalue().strip())

    def testMappingRaisesDataMapAssertionException(self):
        mapping = CallTrace()
        self.harvest = OnlineHarvest(self.output)

        calls = []
        def createUpload(*args, **kwargs):
            calls.append(1)
            if len(calls) == 1:
                raise DataMapAssertionException('O no, it\'s a snake!!')
            upload = CallTrace('upload')
            upload.id = 'id'
            upload.isDeleted = True
            return upload
        mapping.methods['createUpload'] = createUpload
        data = 'file://%s/mocktud/00002.xml' % self._testpath
        self.harvest.performMapping(None, data, mappingObject=mapping)
        self.assertEqual(2, self.output.getvalue().count('upload.id='))

    def testMappingRaisesException(self):
        mapping = CallTrace()
        self.harvest = OnlineHarvest(self.output)

        mapping.exceptions['createUpload'] = Exception('Mushroom, mushroom')
        data = 'file://%s/mocktud/00002.xml' % self._testpath
        try:
            self.harvest.performMapping(None, data, mappingObject=mapping)
            self.fail()
        except Exception as ex:
            self.assertEqual('Mushroom, mushroom', str(ex))
        self.assertEqual('\n',self.output.getvalue())


