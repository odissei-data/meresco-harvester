## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2011-2012, 2015-2016, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2012, 2015, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
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

from os.path import join, isfile
from seecr.test import SeecrTestCase

from meresco.harvester.harvesterdata import HarvesterData
from meresco.harvester.datastore import OldDataStore, DataStore

DATA = {
    'adomain.domain': """{
    "identifier": "adomain",
    "mappingIds": ["ignored MAPPING"],
    "targetIds": ["ignored TARGET"],
    "repositoryGroupIds": ["Group1", "Group2"]
}""",
    'adomain.Group1.repositoryGroup': """{
    "identifier": "Group1",
    "name": {"nl": "Groep1", "en": "Group1"},
    "repositoryIds": ["repository1", "repository2"]
}""",
    'adomain.Group2.repositoryGroup': """{
    "identifier": "Group2",
    "name": {"nl": "Groep2", "en": "Group2"},
    "repositoryIds": ["repository2_1", "repository2_2"]
} """,
    'adomain.repository1.repository': """{
    "identifier": "repository1",
    "repositoryGroupId": "Group1"
}""",
    'adomain.repository2.repository': """{
    "identifier": "repository2",
    "repositoryGroupId": "Group1"
}""",
    'adomain.repository2_1.repository': """{
    "identifier": "repository2_1",
    "repositoryGroupId": "Group2"
}""",
    'adomain.repository2_2.repository': """{
    "identifier": "repository2_2",
    "repositoryGroupId": "Group2"
}""",
'adomain.remi.repository': """{
    "identifier": "remi",
    "repositoryGroupId": "NoGroup"
}"""}

class _HarvesterDataTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        for fname, data in DATA.items():
            with open(join(self.tempdir, fname), "w") as fp:
                fp.write(data)
        self.n = 0
        def mock_id():
            self.n+=1
            return 'mock-id: %s' % self.n
        self.hd = self.createHarvesterData(mock_id)

    def testGetRepositoryGroupIds(self):
        self.assertEqual(["Group1", "Group2"], self.hd.getRepositoryGroupIds(domainId="adomain"))

    def testGetRepositoryIds(self):
        self.assertEqual(["repository1", "repository2"], self.hd.getRepositoryIds(domainId="adomain", repositoryGroupId="Group1"))
        self.assertEqual(["repository1", "repository2", "repository2_1", "repository2_2"], self.hd.getRepositoryIds(domainId="adomain"))

    def testGetRepositoryGroupId(self):
        self.assertEqual("Group1", self.hd.getRepositoryGroupId(domainId="adomain", repositoryId="repository1"))

    def testGetRepositoryGroup(self):
        expected = {
            'identifier': 'Group1',
            'name': {'en': 'Group1', 'nl': 'Groep1'},
            'repositoryIds': ['repository1', 'repository2'],
        }
        if self.with_id:
            expected['@id'] = 'mock-id: 1'
        self.assertEqual(expected, self.hd.getRepositoryGroup(identifier='Group1', domainId='adomain'))

    def testGetRepositoryGroups(self):
        expected =[
            {   'identifier': 'Group1',
                'name': {'en': 'Group1', 'nl': 'Groep1'},
                'repositoryIds': ['repository1', 'repository2'],
            },
            {   'identifier': 'Group2',
                'name': {'en': 'Group2', 'nl': 'Groep2'},
                'repositoryIds': ['repository2_1', 'repository2_2'],
            }
        ]
        if self.with_id:
            expected[0]['@id'] = 'mock-id: 2'
            expected[1]['@id'] = 'mock-id: 3'
        self.assertEqual(expected, self.hd.getRepositoryGroups(domainId='adomain'))

    def testGetRepositories(self):
        result = self.hd.getRepositories(domainId='adomain')
        if self.with_id:
            self.assertEqualsWS("""[
{
    "identifier": "repository1",
    "repositoryGroupId": "Group1",
    "@id": "mock-id: 4"
},
{
    "identifier": "repository2",
    "repositoryGroupId": "Group1",
    "@id": "mock-id: 5"
},
{
    "identifier": "repository2_1",
    "repositoryGroupId": "Group2",
    "@id": "mock-id: 6"
},
{
    "identifier": "repository2_2",
    "repositoryGroupId": "Group2",
    "@id": "mock-id: 7"
}
]""", result.dumps())
        else:
            self.assertEqualsWS("""[
{
    "identifier": "repository1",
    "repositoryGroupId": "Group1"
},
{
    "identifier": "repository2",
    "repositoryGroupId": "Group1"
},
{
    "identifier": "repository2_1",
    "repositoryGroupId": "Group2"
},
{
    "identifier": "repository2_2",
    "repositoryGroupId": "Group2"
}
]""", result.dumps())

    def testGetRepositoriesWithError(self):
        try:
            self.hd.getRepositories(domainId='adomain', repositoryGroupId='doesnotexist')
            self.fail()
        except ValueError as e:
            self.assertEqual('adomain.doesnotexist.repositoryGroup', str(e))

        try:
            self.hd.getRepositories(domainId='baddomain')
            self.fail()
        except ValueError as e:
            self.assertEqual('baddomain.domain', str(e))

    def testGetRepository(self):
        result = self.hd.getRepository(domainId='adomain', identifier='repository1')
        expected = {
            "identifier": "repository1",
            "repositoryGroupId": "Group1",
        }
        if self.with_id:
            expected['@id'] = 'mock-id: 1'
        self.assertEqual(expected, result)

    def testGetRepositoryWithErrors(self):
        try:
            self.hd.getRepository(domainId='adomain', identifier='repository12')
            self.fail()
        except ValueError as e:
            self.assertEqual('adomain.repository12.repository', str(e))

    def testAddDomain(self):
        self.assertEqual(['adomain'], self.hd.getDomainIds())
        self.hd.addDomain(identifier="newdomain")
        if self.with_id:
            self.assertEqual({'@id': 'mock-id: 1', 'identifier': 'newdomain'}, self.hd.getDomain('newdomain'))
        else:
            self.assertEqual({'identifier': 'newdomain'}, self.hd.getDomain('newdomain'))
        self.assertEqual(['adomain', 'newdomain'], self.hd.getDomainIds())
        try:
            self.hd.addDomain(identifier="newdomain")
            self.fail()
        except ValueError as e:
            self.assertEqual('The domain already exists.', str(e))
        try:
            self.hd.addDomain(identifier="domain#with#invalid%characters")
            self.fail()
        except ValueError as e:
            self.assertEqual('Name is not valid. Only use alphanumeric characters.', str(e))
        try:
            self.hd.addDomain(identifier="")
            self.fail()
        except ValueError as e:
            self.assertEqual('No name given.', str(e))

    def testUpdateDomain(self):
        d0 = self.hd.getDomain('adomain')
        self.assertEqual('nono', d0.get('description', 'nono'))
        if self.with_id:
            id0 = d0['@id']
            self.assertTrue(id0)
        self.hd.updateDomain('adomain', description='Beschrijving')
        d1 = self.hd.getDomain('adomain')
        self.assertEqual('Beschrijving', d1.get('description', 'nono'))
        if self.with_id:
            self.assertEqual('mock-id: 2', d1.get('@id'))
            self.assertNotEqual(d0['@id'], d1['@id'])
            self.assertTrue(isfile(join(self.tempdir, '_', 'adomain.domain.%s' % id0)))
            self.assertEqual('nono', self.hd.getDomain('adomain', guid=id0).get('description', 'nono'))

    def testAddRepositoryGroup(self):
        domain = self.hd.getDomain('adomain')
        if self.with_id:
            self.assertEqual('mock-id: 1', domain['@id'])
        self.assertEqual(['Group1', 'Group2'], self.hd.getRepositoryGroupIds(domainId='adomain'))
        self.hd.addRepositoryGroup(identifier="newgroup", domainId='adomain')
        newgroup = self.hd.getRepositoryGroup(identifier='newgroup', domainId='adomain')
        if self.with_id:
            self.assertEqual('mock-id: 2', newgroup['@id'])
        domain = self.hd.getDomain('adomain')
        if self.with_id:
            self.assertEqual('mock-id: 1', domain['@base'])
            self.assertEqual('mock-id: 3', domain['@id'])
        self.assertEqual(['Group1', 'Group2', 'newgroup'], self.hd.getRepositoryGroupIds(domainId='adomain'))
        try:
            self.hd.addRepositoryGroup(identifier="Group1", domainId='adomain')
            self.fail()
        except ValueError as e:
            self.assertEqual('The repositoryGroup already exists.', str(e))
        try:
            self.hd.addRepositoryGroup(identifier="GROUP1", domainId='adomain')
            self.fail()
        except ValueError as e:
            self.assertEqual('The repositoryGroup already exists.', str(e))
        try:
            self.hd.addRepositoryGroup(identifier="group#with#invalid%characters", domainId='adomain')
            self.fail()
        except ValueError as e:
            self.assertEqual('Name is not valid. Only use alphanumeric characters.', str(e))
        try:
            self.hd.addRepositoryGroup(identifier="", domainId='adomain')
            self.fail()
        except ValueError as e:
            self.assertEqual('No name given.', str(e))

    def testUpdateRepositoryGroup(self):
        groep1 = self.hd.getRepositoryGroup('Group1', 'adomain')
        self.assertEqual('Groep1', groep1.get('name', {}).get('nl', ''))
        if self.with_id:
            self.assertEqual('mock-id: 1', groep1['@id'])
        self.hd.updateRepositoryGroup('Group1', domainId='adomain', name={"nl":"naam"})
        groep1 = self.hd.getRepositoryGroup('Group1', 'adomain')
        if self.with_id:
            self.assertEqual('mock-id: 2', groep1['@id'])
            self.assertEqual('mock-id: 1', groep1['@base'])
        self.assertEqual('naam', self.hd.getRepositoryGroup('Group1', 'adomain')['name']['nl'])
        self.assertEqual('Group1', self.hd.getRepositoryGroup('Group1', 'adomain')['name']['en'])

    def testDeleteRepositoryGroup(self):
        domain = self.hd.getDomain('adomain')
        if self.with_id:
            self.assertEqual('mock-id: 1', domain['@id'])
        self.assertEqual(['Group1', 'Group2'], self.hd.getRepositoryGroupIds(domainId='adomain'))
        group = self.hd.getRepositoryGroup('Group2', domainId='adomain')
        if self.with_id:
            self.assertEqual('mock-id: 2', group['@id'])
        self.hd.deleteRepositoryGroup('Group2', domainId='adomain')
        domain = self.hd.getDomain('adomain')
        if self.with_id:
            self.assertEqual('mock-id: 1', domain['@base'])
            self.assertEqual('mock-id: 3', domain['@id'])
        self.assertEqual(['Group1'], self.hd.getRepositoryGroupIds(domainId='adomain'))

    def testAddRepository(self):
        if self.with_id:
            groep1id = self.hd.getRepositoryGroup('Group1', 'adomain')['@id']
        self.assertEqual(['repository1', 'repository2'], self.hd.getRepositoryIds(domainId='adomain', repositoryGroupId='Group1'))
        self.hd.addRepository(identifier="newrepo", domainId='adomain', repositoryGroupId='Group1')
        if self.with_id:
            self.assertNotEqual(groep1id, self.hd.getRepositoryGroup('Group1', 'adomain')['@id'])
        repo = self.hd.getRepository(identifier="newrepo", domainId='adomain')
        if self.with_id:
            self.assertEqual('mock-id: 2', repo['@id'])
        self.assertEqual(['repository1', 'repository2', 'newrepo'], self.hd.getRepositoryIds(domainId='adomain', repositoryGroupId='Group1'))
        self.assertEqual('Group1', self.hd.getRepository(identifier='newrepo', domainId='adomain')['repositoryGroupId'])
        try:
            self.hd.addRepository(identifier="repository1", domainId='adomain', repositoryGroupId='Group1')
            self.fail()
        except ValueError as e:
            self.assertEqual('The repository already exists.', str(e))
        try:
            self.hd.addRepository(identifier="Repository1", domainId='adomain', repositoryGroupId='Group1')
            self.fail()
        except ValueError as e:
            self.assertEqual('The repository already exists.', str(e))
        try:
            self.hd.addRepository(identifier="repository#with#invalid%characters", domainId='adomain', repositoryGroupId='Group1')
            self.fail()
        except ValueError as e:
            self.assertEqual('Name is not valid. Only use alphanumeric characters.', str(e))
        try:
            self.hd.addRepository(identifier="", domainId='adomain', repositoryGroupId='Group1')
            self.fail(group)
        except ValueError as e:
            self.assertEqual('No name given.', str(e))

    def testAddRepositoryMultipleGroups(self):
        try:
            self.hd.addRepository(identifier="repository1", domainId='adomain', repositoryGroupId='Group2')
            self.fail()
        except ValueError as e:
            self.assertEqual('Repository name already in use.', str(e))


    def testDeleteRepository(self):
        if self.with_id:
            repoid = self.hd.getRepository('repository2', 'adomain')['@id']
            groupid = self.hd.getRepositoryGroup('Group1', 'adomain')['@id']
        self.assertEqual(['repository1', 'repository2'], self.hd.getRepositoryIds(domainId='adomain', repositoryGroupId='Group1'))
        self.hd.deleteRepository(identifier="repository2", domainId='adomain', repositoryGroupId='Group1')
        self.assertEqual(['repository1'], self.hd.getRepositoryIds(domainId='adomain', repositoryGroupId='Group1'))
        if self.with_id:
            self.assertEqual(repoid, self.hd.getRepository('repository2', 'adomain', guid=repoid)['@id'])
            self.assertNotEqual(groupid, self.hd.getRepositoryGroup('Group1', 'adomain')['@id'])

    def testUpdateRepository(self):
        if self.with_id:
            repoid = self.hd.getRepository('repository1', 'adomain')['@id']
        self.hd.updateRepository('repository1',
                domainId='adomain',
                baseurl='baseurl',
                set='set',
                metadataPrefix='metadataPrefix',
                mappingId='mappingId',
                targetId='targetId',
                collection='collection',
                maximumIgnore=0,
                use=False,
                complete=True,
                continuous=True,
                action='action',
                shopclosed=['40:1:09:55-40:1:10:00'],
                userAgent='',
                authorizationKey='',
            )
        repository = self.hd.getRepository('repository1', 'adomain')
        self.assertEqual('baseurl', repository['baseurl'])
        self.assertEqual('set', repository['set'])
        self.assertEqual('metadataPrefix', repository['metadataPrefix'])
        self.assertEqual('mappingId', repository['mappingId'])
        self.assertEqual('targetId', repository['targetId'])
        self.assertEqual('collection', repository['collection'])
        self.assertEqual(0, repository['maximumIgnore'])
        self.assertEqual(False, repository['use'])
        self.assertEqual(True, repository['complete'])
        self.assertEqual(True, repository['continuous'])
        self.assertEqual('action', repository['action'])
        self.assertEqual(['40:1:09:55-40:1:10:00'], repository['shopclosed'])
        if self.with_id:
            self.assertEqual(repoid, repository['@base'])
            self.assertNotEqual(repoid, repository['@id'])

    def testRepositoryDone(self):
        self.hd.updateRepository('repository1',
                domainId='adomain',
                baseurl='baseurl',
                set='set',
                metadataPrefix='metadataPrefix',
                mappingId='mappingId',
                targetId='targetId',
                collection='collection',
                maximumIgnore=0,
                use=False,
                complete=True,
                continuous=True,
                action='action',
                shopclosed=['40:1:09:55-40:1:10:00'],
                userAgent='',
                authorizationKey='',
            )
        if self.with_id:
            repoid = self.hd.getRepository('repository1', 'adomain')['@id']
        self.hd.repositoryDone(identifier='repository1', domainId='adomain')
        repository = self.hd.getRepository('repository1', 'adomain')
        self.assertEqual(None, repository['action'])
        if self.with_id:
            self.assertEqual(repoid, repository['@id'])

    def testAddMapping(self):
        domain = self.hd.getDomain('adomain')
        if self.with_id:
            dId = domain['@id']
        self.assertEqual(['ignored MAPPING'], domain['mappingIds'])
        mappingId = self.hd.addMapping(name='newMapping', domainId='adomain')
        mappingIds = self.hd.getDomain('adomain')['mappingIds']
        if self.with_id:
            self.assertNotEqual(dId, self.hd.getDomain('adomain')['@id'])
        self.assertEqual(2, len(mappingIds))
        mapping = self.hd.getMapping(mappingId)
        self.assertEqual(mappingId, mappingIds[-1])
        self.assertEqual('newMapping', mapping['name'])
        self.assertEqual('This mapping is what has become the default mapping for most Meresco based projects.\n', mapping['description'])
        self.assertTrue(len(mapping['code']) > 100)
        self.assertEqual(mappingIds[1], mapping['identifier'])
        try:
            self.hd.addMapping(name="", domainId='adomain')
            self.fail()
        except ValueError as e:
            self.assertEqual('No name given.', str(e))

    def testUpdateMapping(self):
        mappingId = self.hd.addMapping(name='newMapping', domainId='adomain')
        mapping = self.hd.getMapping(mappingId)
        self.assertEqual(mappingId, mapping["identifier"])
        if self.with_id:
            mId = mapping['@id']
        self.assertRaises(ValueError, lambda: self.hd.updateMapping(mappingId, name='newName', description="a description", code="new code"))
        self.assertEqual('newName', self.hd.getMapping(mappingId)['name'])
        self.assertEqual('a description', self.hd.getMapping(mappingId)['description'])
        self.assertEqual('new code', self.hd.getMapping(mappingId)['code'])
        if self.with_id:
            self.assertNotEqual(mId, self.hd.getMapping(mappingId)['@id'])

    def testDeleteMapping(self):
        mappingId = self.hd.addMapping(name='newMapping', domainId='adomain')
        if self.with_id:
            mId = self.hd.getMapping(mappingId)['@id']
            dId = self.hd.getDomain('adomain')['@id']
        self.assertEqual(['ignored MAPPING', mappingId], self.hd.getDomain('adomain')['mappingIds'])
        self.hd.deleteMapping(identifier=mappingId, domainId='adomain')
        self.assertEqual(['ignored MAPPING'], self.hd.getDomain('adomain')['mappingIds'])
        self.assertRaises(ValueError, lambda: self.hd.getMapping(mappingId))
        if self.with_id:
            self.assertNotEqual(dId, self.hd.getDomain('adomain')['@id'])
            self.assertEqual('newMapping', self.hd.getMapping(mappingId, mId)['name'])

    def testAddTarget(self):
        if self.with_id:
            dId = self.hd.getDomain('adomain')['@id']
        self.assertEqual(['ignored TARGET'], self.hd.getDomain('adomain')['targetIds'])
        targetId = self.hd.addTarget(name='new target', domainId='adomain', targetType='sruUpdate')
        if self.with_id:
            self.assertNotEqual(dId, self.hd.getDomain('adomain')['@id'])
        targetIds = self.hd.getDomain('adomain')['targetIds']
        self.assertEqual(2, len(targetIds))
        target = self.hd.getTarget(targetId)
        if self.with_id:
            self.assertEqual('mock-id: 3', target['@id'])
        self.assertEqual(targetId, targetIds[-1])
        self.assertEqual('new target', target['name'])
        self.assertEqual(targetId, target['identifier'])
        try:
            self.hd.addTarget(name="", domainId='adomain', targetType='sruUpdate')
            self.fail()
        except ValueError as e:
            self.assertEqual('No name given.', str(e))

    def testUpdateTarget(self):
        targetId = self.hd.addTarget(name='new target', domainId='adomain', targetType='sruUpdate')
        if self.with_id:
            tId = self.hd.getTarget(targetId)['@id']
        self.hd.updateTarget(identifier=targetId,
                name='updated target',
                username='username',
                port=1234,
                targetType='composite',
                delegateIds=['id1', 'id2'],
                path='path',
                baseurl='baseurl',
                oaiEnvelope=False,
            )
        target = self.hd.getTarget(targetId)
        self.assertEqual('updated target', target['name'])
        self.assertEqual('username', target['username'])
        self.assertEqual(1234, target['port'])
        self.assertEqual('composite', target['targetType'])
        self.assertEqual(['id1', 'id2'], target['delegateIds'])
        self.assertEqual('path', target['path'])
        self.assertEqual('baseurl', target['baseurl'])
        self.assertEqual(False, target['oaiEnvelope'])
        if self.with_id:
            self.assertNotEqual(tId, target['@id'])
            self.assertEqual('new target', self.hd.getTarget(targetId, tId)['name'])

    def testDeleteTarget(self):
        targetId = self.hd.addTarget(name='new target', domainId='adomain', targetType='sruUpdate')
        if self.with_id:
            tId = self.hd.getTarget(targetId)['@id']
            dId = self.hd.getDomain('adomain')['@id']
        self.assertEqual(['ignored TARGET', targetId], self.hd.getDomain('adomain')['targetIds'])
        self.hd.deleteTarget(targetId, domainId='adomain')
        self.assertEqual(['ignored TARGET'], self.hd.getDomain('adomain')['targetIds'])
        self.assertRaises(ValueError, lambda: self.hd.getTarget(targetId))
        if self.with_id:
            self.assertNotEqual(dId, self.hd.getDomain('adomain')['@id'])
            self.assertEqual(targetId, self.hd.getTarget(targetId, guid=tId)['identifier'])

class HarvesterDataTest(_HarvesterDataTest):
    with_id = True
    def createHarvesterData(self, id_fn):
        return HarvesterData(self.tempdir, id_fn=id_fn, datastore=DataStore(self.tempdir, id_fn=id_fn))

    def testGetWithGuid(self):
        self.assertTrue(self.hd.getDomain('adomain', 'mock-id: 1'))
        self.assertTrue(self.hd.getRepositoryGroup('Group1', 'adomain', 'mock-id: 2'))
        self.assertTrue(self.hd.getRepository('repository1', 'adomain', 'mock-id: 3'))

    def testDeleteAndOldGuid(self):
        gid = self.hd.getRepositoryGroup('Group1', 'adomain')['@id']
        self.hd.deleteRepositoryGroup('Group1', 'adomain')
        self.assertRaises(ValueError, lambda: self.hd.getRepositoryGroup('Group1', 'adomain'))
        self.assertTrue(self.hd.getRepositoryGroup('Group1', 'adomain', gid))

class HarvesterDataOldStyleTest(_HarvesterDataTest):
    with_id = False
    def createHarvesterData(self, id_fn):
        return HarvesterData(self.tempdir, id_fn=id_fn, datastore=OldDataStore(self.tempdir, id_fn=id_fn))
