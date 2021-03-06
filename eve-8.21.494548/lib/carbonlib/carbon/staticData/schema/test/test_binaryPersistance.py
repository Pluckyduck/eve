#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\carbon\staticData\schema\test\test_binaryPersistance.py
if __name__ == '__main__':
    import sys, os
    carbonLibPath = os.path.abspath(os.path.join(__file__, '../../../../../'))
    sys.path.append(carbonLibPath)
import carbon.staticData.schema.validator as validator
import carbon.staticData.schema.schemaOptimizer as schemaOptimizer
import carbon.staticData.schema.binaryRepresenter as binaryRepresenter
import carbon.staticData.schema.binaryLoader as binaryLoader
import cStringIO
import unittest
import itertools

def Persist(data, schema):
    optSchema = schemaOptimizer.OptimizeSchema(schema, validator.SERVER)
    return binaryRepresenter.RepresentAsBinary(data, optSchema)


def Marshal(data, schema):
    optSchema = schemaOptimizer.OptimizeSchema(schema, validator.SERVER)
    return binaryLoader.LoadFromString(data, optSchema)


def PersistAndMarshal(data, schema):
    optSchema = schemaOptimizer.OptimizeSchema(schema, validator.SERVER)
    binaryRepresentation = binaryRepresenter.RepresentAsBinary(data, optSchema)
    return binaryLoader.LoadFromString(binaryRepresentation, optSchema)


class BinaryPersistenceTest(unittest.TestCase):

    def testVector4Representation(self):
        schema = {'type': 'vector4'}
        testVector = (0.0, 1.0, 2.0, 3.0)
        self.assertEqual(testVector, PersistAndMarshal(testVector, schema))

    def testVector4Aliasing(self):
        schema = {'type': 'vector4',
         'aliases': {'x': 0,
                     'y': 1,
                     'z': 2,
                     'radius': 3}}
        testVector = (0.0, 1.0, 2.0, 3.0)
        dataResult = PersistAndMarshal(testVector, schema)
        self.assertEqual(testVector[0], dataResult.x)
        self.assertEqual(testVector[1], dataResult.y)
        self.assertEqual(testVector[2], dataResult.z)
        self.assertEqual(testVector[3], dataResult.radius)

    def testVector3Representation(self):
        schema = {'type': 'vector3'}
        testVector = (0.0, 1.0, 2.0)
        self.assertEqual(testVector, PersistAndMarshal(testVector, schema))

    def testVector3Aliasing(self):
        schema = {'type': 'vector3',
         'aliases': {'r': 0,
                     'g': 1,
                     'b': 2}}
        testVector = (0.0, 1.0, 2.0)
        persistedVector = PersistAndMarshal(testVector, schema)
        self.assertEqual(testVector[0], persistedVector.r)
        self.assertEqual(testVector[0], persistedVector[0])
        self.assertEqual(testVector[1], persistedVector.g)
        self.assertEqual(testVector[1], persistedVector[1])
        self.assertEqual(testVector[2], persistedVector.b)
        self.assertEqual(testVector[2], persistedVector[2])

    def testVector2Representation(self):
        schema = {'type': 'vector2'}
        testVector = (0.0, 1.0)
        self.assertEqual(testVector, PersistAndMarshal(testVector, schema))

    def testVector2Aliasing(self):
        schema = {'type': 'vector2',
         'aliases': {'u': 0,
                     'v': 1}}
        testVector = (10.0, 5.0)
        persistedVector = PersistAndMarshal(testVector, schema)
        self.assertEqual(testVector[0], persistedVector.u)
        self.assertEqual(testVector[0], persistedVector[0])
        self.assertEqual(testVector[1], persistedVector.v)
        self.assertEqual(testVector[1], persistedVector[1])

    def testStringRepresentation(self):
        schema = {'type': 'string'}
        testString = 'MyTest string'
        self.assertEqual(testString, PersistAndMarshal(testString, schema))

    def testResPathRepresentation(self):
        schema = {'type': 'resPath'}
        testString = 'res:/MyFile/Is/here.red'
        self.assertEqual(testString, PersistAndMarshal(testString, schema))

    def testFixedSizedList(self):
        schema = {'type': 'list',
         'sortOrder': 'ASCENDING',
         'itemTypes': {'type': 'int'}}
        data = [1,
         4,
         5,
         6]
        persisted = PersistAndMarshal(data, schema)
        self.assertEqual(len(data), len(persisted))
        for dataItem, persistedItem in itertools.izip(data, persisted):
            self.assertEqual(dataItem, persistedItem)

        self.assertEqual(data[2], persisted[2])

    def testEnumRepresentation(self):
        schema = {'type': 'enum',
         'values': {'VALUE1': 1,
                    'VALUE2': 2,
                    'VALUE3': 3}}
        enumValue = 'VALUE1'
        self.assertEqual(enumValue, PersistAndMarshal(enumValue, schema))

    def testBoolRepresentation(self):
        schema = {'type': 'bool'}
        value = True
        self.assertEqual(value, PersistAndMarshal(value, schema))

    def testIntRepresentation(self):
        schema = {'type': 'int'}
        value = 13
        self.assertEqual(value, PersistAndMarshal(value, schema))

    def testPODObjectRepresentation(self):
        schema = {'type': 'object',
         'attributes': {'a': {'type': 'int'},
                        'b': {'type': 'float'},
                        'c': {'type': 'vector4'}}}
        data = {'a': 19,
         'b': 0.5,
         'c': (2.0, 3.0, 4.0, 5.0)}
        dataResult = PersistAndMarshal(data, schema)
        self.assertEqual(data['a'], dataResult['a'])
        self.assertEqual(data['b'], dataResult['b'])
        self.assertEqual(data['c'], dataResult['c'])

    def testComplexObjectRepresentation(self):
        schema = {'type': 'object',
         'attributes': {'a': {'type': 'int'},
                        'b': {'type': 'string'},
                        'c': {'type': 'vector4',
                              'isOptional': True}}}
        data = {'a': 19,
         'b': 'hello',
         'c': (2.0, 3.0, 4.0, 5.0)}
        dataResult = PersistAndMarshal(data, schema)
        self.assertEqual(data['a'], dataResult['a'])
        self.assertEqual(data['b'], dataResult['b'])
        self.assertEqual(data['c'], dataResult['c'])
        data2 = {'a': 1,
         'b': 'world'}
        dataResult2 = PersistAndMarshal(data2, schema)
        self.assertEqual(data2['a'], dataResult2['a'])
        self.assertEqual(data2['b'], dataResult2['b'])
        with self.assertRaises(KeyError):
            dataResult2['c']

    def testObjectAttributeRepresentation(self):
        schema = {'type': 'object',
         'attributes': {'test': {'type': 'int'}}}
        data = {'test': 49}
        dataResult = PersistAndMarshal(data, schema)
        self.assertEqual(data['test'], dataResult.test)

    def testPODListRepresentation(self):
        schema = {'type': 'list',
         'itemTypes': {'type': 'vector4'}}
        data = [(1.0, 2.0, 3.0, 4.0), (2.0, 3.0, 4.0, 5.0)]
        dataResult = PersistAndMarshal(data, schema)
        self.assertEqual(2, len(dataResult))
        self.assertEqual(data[0], dataResult[0])
        self.assertEqual(data[1], dataResult[1])
        for i, d in enumerate(dataResult):
            self.assertNotEqual(i, 2)
            self.assertEqual(d, data[i])

    def testVariableSizeListRepresentation(self):
        schema = {'type': 'list',
         'itemTypes': {'type': 'string'}}
        data = ['Hello', 'World']
        dataResult = PersistAndMarshal(data, schema)
        self.assertEqual(2, len(dataResult))
        self.assertEqual(data[0], dataResult[0])
        self.assertEqual(data[1], dataResult[1])
        for i, d in enumerate(dataResult):
            self.assertNotEqual(i, 2)
            self.assertEqual(d, data[i])

    def testDictRepresentation(self):
        schema = {'type': 'dict',
         'keyTypes': {'type': 'int'},
         'valueTypes': {'type': 'int'}}
        data = {1: 2,
         2: 3,
         3: 4,
         4: 5}
        dataResult = PersistAndMarshal(data, schema)
        self.assertEqual(len(data), len(dataResult))
        for k, v in data.iteritems():
            self.assertEqual(v, dataResult[k])

    def testBinaryPODComposition(self):
        itemSchema = {'type': 'vector4'}
        composedListSchema = {'type': 'list',
         'itemTypes': {'type': 'binary',
                       'schema': itemSchema}}
        resolvedItemSchema = {'type': 'list',
         'itemTypes': itemSchema}
        item1Data = (1.0, 2.0, 3.0, 4.0)
        item2Data = (2.0, 3.0, 4.0, 5.0)
        item1Binary = Persist(item1Data, itemSchema)
        item2Binary = Persist(item2Data, itemSchema)
        composedBinary = Persist([item1Binary, item2Binary], composedListSchema)
        mashalledComposed = Marshal(composedBinary, resolvedItemSchema)
        self.assertEqual(2, len(mashalledComposed))
        self.assertEqual(item1Data, mashalledComposed[0])
        self.assertEqual(item2Data, mashalledComposed[1])

    def testBinaryComplexComposition(self):
        itemSchema = {'type': 'object',
         'attributes': {'name': {'type': 'string'},
                        'height': {'type': 'int'}}}
        composedListSchema = {'type': 'dict',
         'keyTypes': {'type': 'int'},
         'valueTypes': {'type': 'binary',
                        'schema': itemSchema}}
        resolvedItemSchema = {'type': 'dict',
         'keyTypes': {'type': 'int'},
         'valueTypes': itemSchema}
        robert = {'name': 'Robert',
         'height': 180}
        karen = {'name': 'Karen',
         'height': 156}
        employeesData = {1: robert,
         30: karen}
        robertBinary = Persist(robert, itemSchema)
        karenBinary = Persist(karen, itemSchema)
        employeesBinary = {1: robertBinary,
         30: karenBinary}
        composedBinary = Persist(employeesBinary, composedListSchema)
        mashalledComposed = Marshal(composedBinary, resolvedItemSchema)
        self.assertEqual(2, len(mashalledComposed))
        self.assertEqual(employeesData[1]['name'], mashalledComposed[1]['name'])
        self.assertEqual(employeesData[1]['height'], mashalledComposed[1]['height'])
        self.assertEqual(employeesData[30]['name'], mashalledComposed[30]['name'])
        self.assertEqual(employeesData[30]['height'], mashalledComposed[30]['height'])

    def testUnsignedIntObject(self):
        schema = {'type': 'object',
         'attributes': {'a': {'type': 'int',
                              'min': 0},
                        'b': {'type': 'int'},
                        'c': {'type': 'int',
                              'min': 20},
                        'd': {'type': 'int',
                              'exclusiveMin': -1},
                        'e': {'type': 'int',
                              'exclusiveMin': -2},
                        'f': {'type': 'int',
                              'exclusiveMin': 20}}}
        data = {'a': 40,
         'b': -1,
         'c': 23,
         'd': 3,
         'e': -1,
         'f': 30}
        dataResult = PersistAndMarshal(data, schema)
        self.assertEqual(data['a'], dataResult.a)
        self.assertEqual(data['b'], dataResult.b)
        self.assertEqual(data['c'], dataResult.c)
        self.assertEqual(data['d'], dataResult.d)
        self.assertEqual(data['e'], dataResult.e)
        self.assertEqual(data['f'], dataResult.f)

    def testCFGOverridesForObject(self):
        schema = {'type': 'object',
         'attributes': {'a': {'type': 'int'}}}

        class CFGObjectType(object):

            def __init__(self):
                self.a = 1
                self.b = 2

        cfgObject = CFGObjectType()
        override = Persist({'a': 0}, schema)
        loaderState = binaryLoader.LoaderState(binaryLoader.defaultLoaderFactories, cfgObject=cfgObject)
        loadedObject = binaryLoader.LoadFromString(override, schemaOptimizer.OptimizeSchema(schema, validator.SERVER), loaderState)
        self.assertEqual(loadedObject.a, 0)
        self.assertEqual(loadedObject.b, 2)

    def testCFGOverridesForDict(self):
        schema = {'type': 'dict',
         'keyTypes': {'type': 'int'},
         'valueTypes': {'type': 'object',
                        'attributes': {'a': {'type': 'int'}}}}

        class CFGObjectType(object):

            def __init__(self, **kwargs):
                for i in kwargs:
                    setattr(self, i, kwargs[i])

        class CFGDictType(object):

            def __init__(self, d):
                self.__d__ = d

            def GetIfExists(self, k):
                if k in self.__d__:
                    return self.__d__[k]
                else:
                    return None

        cfgDictData = {1: CFGObjectType(a=1, b=2),
         2: CFGObjectType(a=3)}
        override = Persist({1: {'a': 0}}, schema)
        loaderState = binaryLoader.LoaderState(binaryLoader.defaultLoaderFactories, cfgObject=CFGDictType(cfgDictData))
        loadedObject = binaryLoader.LoadFromString(override, schemaOptimizer.OptimizeSchema(schema, validator.SERVER), loaderState)
        self.assertEqual(loadedObject[1].a, 0)
        self.assertEqual(loadedObject[1].b, 2)
        self.assertEqual(loadedObject[2].a, 3)

    def testBinaryIndexing(self):
        schema = {'type': 'dict',
         'buildIndex': True,
         'keyTypes': {'type': 'int'},
         'valueTypes': {'type': 'object',
                        'attributes': {'name': {'type': 'string'},
                                       'age': {'type': 'int',
                                               'min': 0}}}}
        data = {0: {'name': 'Pete',
             'age': 5},
         13: {'name': 'Kevin',
              'age': 12}}
        binaryData = Persist(data, schema)
        ioBuffer = cStringIO.StringIO(binaryData)
        ioBuffer.seek(0)
        optSchema = schemaOptimizer.OptimizeSchema(schema, validator.SERVER)
        indexedData = binaryLoader.LoadIndexFromFile(ioBuffer, optSchema, 100)
        self.assertEqual(len(indexedData), len(data))
        for k, v in data.iteritems():
            self.assertEqual(v['name'], indexedData[k].name)
            self.assertEqual(v['age'], indexedData[k].age)

    def testBinaryNestedDictionaryIndexing(self):
        schema = {'type': 'dict',
         'buildIndex': True,
         'keyTypes': {'type': 'int'},
         'valueTypes': {'type': 'dict',
                        'buildIndex': True,
                        'keyTypes': {'type': 'int'},
                        'valueTypes': {'type': 'object',
                                       'attributes': {'age': {'type': 'int',
                                                              'min': 0},
                                                      'name': {'type': 'string'}}}}}
        data = {123: {1: {'age': 5,
                   'name': 'Toddler Joe'},
               100: {'age': 500,
                     'name': 'Old man Gary'}},
         1234: {1: {'age': 50,
                    'name': 'Middle aged Jack'},
                100: {'age': 50000,
                      'name': 'Yoda'}}}
        binaryData = Persist(data, schema)
        ioBuffer = cStringIO.StringIO(binaryData)
        ioBuffer.seek(0)
        optSchema = schemaOptimizer.OptimizeSchema(schema, validator.SERVER)
        indexedData = binaryLoader.LoadIndexFromFile(ioBuffer, optSchema, 100)
        self.assertEqual(len(indexedData), len(data))
        for k, v in data.iteritems():
            dictionary = v
            for key, value in dictionary.iteritems():
                data = indexedData[k][key]
                self.assertEqual(value['age'], data.age)
                self.assertEqual(value['name'], data.name)

    def testDictionaryContains(self):
        schema = {'type': 'dict',
         'keyTypes': {'type': 'int'},
         'valueTypes': {'type': 'object',
                        'attributes': {'name': {'type': 'string'},
                                       'age': {'type': 'int',
                                               'min': 0}}}}
        data = {0: {'name': 'Pete',
             'age': 5},
         13: {'name': 'Kevin',
              'age': 12}}
        dataResult = PersistAndMarshal(data, schema)
        self.assertTrue(0 in dataResult)
        self.assertTrue(13 in dataResult)
        self.assertFalse(10 in dataResult)
        self.assertFalse('WTF' in dataResult)

    def testBinaryIndexContains(self):
        schema = {'type': 'dict',
         'buildIndex': True,
         'keyTypes': {'type': 'int'},
         'valueTypes': {'type': 'object',
                        'attributes': {'name': {'type': 'string'},
                                       'age': {'type': 'int',
                                               'min': 0}}}}
        data = {0: {'name': 'Pete',
             'age': 5},
         13: {'name': 'Kevin',
              'age': 12}}
        binaryData = Persist(data, schema)
        ioBuffer = cStringIO.StringIO(binaryData)
        ioBuffer.seek(0)
        optSchema = schemaOptimizer.OptimizeSchema(schema, validator.SERVER)
        indexedData = binaryLoader.LoadIndexFromFile(ioBuffer, optSchema, 100)
        self.assertTrue(0 in indexedData)
        self.assertTrue(13 in indexedData)
        self.assertFalse(-1 in indexedData)
        self.assertFalse(10 in indexedData)
        self.assertFalse('WTF' in indexedData)

    def testEnumIntegerValues(self):
        schema = {'type': 'enum',
         'readEnumValue': True,
         'values': {'A': 1,
                    'B': 50,
                    'C': 11045}}
        data = 'A'
        loadedData = PersistAndMarshal(data, schema)
        self.assertEqual(loadedData, 1)
        data = 'C'
        loadedData = PersistAndMarshal(data, schema)
        self.assertEqual(loadedData, 11045)


if __name__ == '__main__':
    import sys
    suite = unittest.TestLoader().loadTestsFromTestCase(BinaryPersistenceTest)
    unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)