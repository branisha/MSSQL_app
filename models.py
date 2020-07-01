#!/usr/bin/env python3

import copy
from abc import ABC, abstractmethod

import pymssql
import datetime

from collections import OrderedDict


class MSType(ABC):
    """Base MSSSQL data type -> abstact class

    Vals:
        DESCRIPTOR (string): user friendly name of type    

    """

    DESCRIPTOR = "MSSQL TIP"

    def __init__(self, value=None, isNull=False, isPK=False, isFK=False):
        """Constructor

        Args:
            value ([type], optional): value of datatype. Defaults to None.
            isNull (bool, optional): Is field nullable?. Defaults to False.
            isPK (bool, optional): Is field primary key?. Defaults to False.
            isFK (bool, optional): is field foregin key?. Defaults to False.
        """
        self.isNull = isNull
        self.isPK = isPK
        self.isFK = isFK
        self.value = value

    def setValue(self, value):
        """Getter for value

        Args:
            value ([type]): sets current value
        """
        self.value = value

    def getValue(self):
        """Setter for value

        Returns:
            [type]: returns current value
        """
        return self.value

    def getValueSQL(self):
        """Getter for SQL value

        Returns:
            [type]: returns current value in sql format
        """
        return self.getValue()

    @ abstractmethod
    def isValueOK(self):
        """Checks if current value is valid for datatype

        Raises:
            NotImplementedError: Abstract method

        Returns:
            bool: True if valid, False otherwise
        """
        raise NotImplementedError


class MSVarchar(MSType):
    """Class for MSSQL VARCHAR type"""

    def __init__(self, maxsize=255, *args, **kwargs):
        """Constuctor

        Args:
            maxsize (int, optional): max length of varchar. Defaults to 255.
        """
        super().__init__(*args, **kwargs)
        self.maxsize = maxsize
        self.DESCRIPTOR = "VARCHAR({})".format(maxsize)

    def isValueOK(self):

        if(self.isNull is True and self.getValue() is None):
            return True
        if(isinstance(self.getValue(), str) and len(self.getValue()) < self.maxsize):
            return True
        return False


class MSInt(MSType):
    """Class for MSSSQL INT type"""

    DESCRIPTOR = "INT"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def isValueOK(self):

        if(self.isNull is True and self.getValue() is None):
            return True
        if(isinstance(self.getValue(), int) and self.getValue() > -2**31 and self.getValue() < 2**31 - 1):
            return True
        return False


class MSBit(MSType):

    DESCRIPTOR = "BOOL"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def isValueOK(self):
        if(self.isNull is True and self.getValue() is None):
            return True
        if(self.getValue() in (True, False, "True", "False", 0, 1)):
            return True

        return False

    def getValueSQL(self):
        if(self.getValue() in (True, "True", 1)):
            return 1
        elif(self.getValue() in (False, "False", 0)):
            return 0


class MSBigInt(MSType):

    DESCRIPTOR = "BIG INT"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def isValueOK(self):
        if(self.isNull is True and self.getValue() is None):
            return True
        if(isinstance(self.getValue(), int) and self.getValue() > -2**63 and self.getValue() < 2**63 - 1):
            return True
        return False


class MSDatetime(MSType):

    DESCRIPTOR = "DATETIME"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def isValueOK(self):

        if(self.isNull is True and self.getValue() is None):
            return True
        if(isinstance(self.getValue(), datetime.datetime)):
            return True

        if(isinstance(self.getValue(), datetime.date)):
            return True

        return False

    def getValueSQL(self):
        if(isinstance(self.getValue(), datetime.date)):
            return datetime.datetime.combine(self.getValue(), datetime.time())

        return self.getValue()


class SchemaObject(ABC):
    """Base class for schema objects, which represents table
    
        Each inherited class should contain variable TABLE_NAME, fields as OrderedDict.
        See examples.
    """

    @classmethod
    def GetPK(baseclass):
        """Finds primary key name and associated MSType object

        Args:
            baseclass (inherited class): inherited class that has defined 'fields' vatriable. See examples.

        Raises:
            ValueError: raises if primary key is not found

        Returns:
            tuple(string, MSType): returns primary key field name, and MSType that holds value
        """
        for field_name, field_type in baseclass.fields.items():
            if(field_type.isPK is True):
                return (field_name, field_type)

        raise ValueError("PK Key not defined")

    def __init__(self, fields, table_name, fields_dict={}):
        """Constuctor

        Args:
            fields (dict{string:MSType}): fields used for this schema
            table_name (string): name of SQL table in database that corresponds to this schema
            fields_dict (dict{string:[type]}): initial values for object. Defaults to {}.
        """
        self.fields = fields

        for key, value in fields_dict.items():
            self.setField(key, value)

        self.TABLE_NAME = table_name
        self.clone = copy.deepcopy(self)

    def getPK(self):
        """object version of GetPK method"""
        for field_name, field_type in self.fields.items():
            if(field_type.isPK is True):
                return (field_name, field_type)

        raise ValueError("PK Key not defined")

    def getPKname(self):
        """returns name of primary key field

        Returns:
            string: primary key field name
        """
        return self.getPK()[0]

    def getPKfield(self):
        """returns primary key associated type

        Returns:
            MSType: primary key MSType
        """
        return self.getPK()[1]

    def getFieldNames(self):
        """returns all field names in this schema

        Returns:
            list[string]: list of field names
        """
        return [key for key, _ in self.fields.items()]

    def getFieldValuesSQL(self):
        """returns all values of this object in sql format

        Returns:
            list: coresponing sql value of each MSType
        """
        return [field.getValueSQL() for _, field in self.fields.items()]

    def generatePlaceholderString(self):
        """generates placeholder string for SQL query

        Returns:
            string: string of placeholder symbols
        """
        return "(" + (",".join(["%s" for _ in self.getFieldNames()])) + ")"

    def setField(self, name, value):
        """sets field to value

        Args:
            name (string): name of field
            value ([type]): value to be set in field

        Returns:
            MSType.setValue: MSType.setValue
        """
        return self.fields[name].setValue(value)

    def getField(self, name):
        """returns value of field

        Args:
            name (string): name of field

        Returns:
            [type]: current value of field
        """
        return self.fields[name].getValue()

    def updateObject(self, connection_parameters):
        """updates objects in SQL DB

        Args:
            connection_parameters (kwargs dict): pymssql connection parameters

        Returns:
            int: number of updated rows
        """
        testStr = "UPDATE {} SET".format(self.TABLE_NAME)

        field_values = []

        for field_name, field_type in self.fields.items():
            field_values.append(field_type.getValueSQL())
            testStr += " {}=%s,".format(field_name)

        testStr = testStr[:-1] + " WHERE {}=%s".format(self.getPKname())
        field_values.append(self.clone.getPKfield().getValueSQL())

        affected_rows = 0

        with pymssql.connect(**connection_parameters) as conn:
            with conn.cursor(as_dict=True) as cursor:
                cursor.execute(testStr, tuple(field_values))
                affected_rows = cursor.rowcount
                conn.commit()

        self.clone = copy.deepcopy(self)


        return affected_rows

    def insertObject(self, connection_parameters):
        """inserts object into SQL DB

        Args:
            connection_parameters (kwargs dict): pymssql connection parameters

        Returns:
            int: number of affected rows
        """

        leftsideQuery = "(" + (",".join(self.getFieldNames())) + ")"

        rightsideQuery = self.generatePlaceholderString()

        completeStr = "INSERT INTO {} {} VALUES {}".format(
            self.TABLE_NAME, leftsideQuery, rightsideQuery)

        affected_rows = 0
        with pymssql.connect(**connection_parameters) as conn:
            with conn.cursor(as_dict=True) as cursor:
                cursor.execute(completeStr, tuple(self.getFieldValuesSQL()))
                affected_rows = cursor.rowcount
                conn.commit()

        self.clone = copy.deepcopy(self)

        return affected_rows

    def deleteObject(self, connection_parameters):
        """deletes object from SQL DB

        Args:
            connection_parameters (kwargs dict): pymssql connection parameters

        Returns:
            int: number of affected rows
        """

        # (internal?) BUG: when param is 0
        if(self.getPKfield().getValueSQL() == 0):
            affected_rows = 0
            with pymssql.connect(**connection_parameters) as conn:
                with conn.cursor(as_dict=True) as cursor:
                    cursor.execute("DELETE FROM {} WHERE {}=0".format(
                        self.TABLE_NAME, self.getPKname()))
                    affected_rows = cursor.rowcount
                    conn.commit()

            return affected_rows

        completeStr = "DELETE FROM {} WHERE {}=%s".format(
            self.TABLE_NAME, self.getPKname())

        affected_rows = 0
        with pymssql.connect(**connection_parameters) as conn:
            with conn.cursor(as_dict=True) as cursor:
                cursor.execute(completeStr, self.getPKfield().getValueSQL())
                affected_rows = cursor.rowcount
                conn.commit()

        return affected_rows

    def testMethod(self):
        """Test method for connection

        Returns:
            ?: ?
        """
        return "Info"

    @classmethod
    def FetchAllObjects(baseClass, connection_parameters):
        """fetches all objects for this schema from SQL DB

        Args:
            baseClass (baseClass): inherited class
            connection_parameters (kwargs dict): pymssql connection parameters

        Returns:
            list: list of baseClass objects
        """     
        query = "SELECT * FROM {}".format(baseClass.TABLE_NAME)

        results = []
        with pymssql.connect(**connection_parameters) as conn:
            with conn.cursor(as_dict=True) as cursor:
                cursor.execute(query)
                for row in cursor.fetchall():
                    results.append(baseClass(row))
                conn.commit()

        return results

    @classmethod
    def FetchObjectsWhere(baseClass, connection_parameters, filter_dict):
        """fetches all objects matching filter

        Args:
            baseClass (baseClass): inherited class
            connection_parameters (kwargs dict): pymssql connection parameters
            filter_dict (dict{string:value}): dict containing field names and values as filter 

        Returns:
            list: list of baseClass objects
        """
        query = "SELECT * FROM {} WHERE".format(baseClass.TABLE_NAME)

        parameter_list = []
        for key, ms_value in filter_dict.items():
            query += " {}=%s,".format(key)
            parameter_list.append(ms_value)

        results = []
        with pymssql.connect(**connection_parameters) as conn:
            with conn.cursor(as_dict=True) as cursor:
                cursor.execute(query[:-1], tuple(parameter_list))
                for row in cursor.fetchall():
                    results.append(baseClass(row))
                conn.commit()

        return results


class TronPosOdooExchangeUp(SchemaObject):

    """Schema class for TronPosOdooExchangeUp"""

    TABLE_NAME = "TronPosOdooExchangeUp"

    fields = OrderedDict([
        ('tpfirm_id', MSInt(isPK=True)),
        ('tpfirmName', MSVarchar(255)),
        ('tpfirmActive', MSBit()),
        ('TronRetailServerDataBase', MSVarchar(255)),
        ('OdooHost',  MSVarchar(255)),
        ('OdooPort', MSInt()),
        ('OdooDataBase', MSVarchar(255)),
        ('OdooUserName', MSVarchar(255)),
        ('OdooPassword', MSVarchar(255)),
        ('recDate', MSDatetime(isNull=True)),
        ('OdooECommerce', MSBit(isNull=True)),
        ('RowChID', MSBigInt()),
        ('SyncClientUser', MSVarchar(255, isNull=True)),
        ('SyncClientPassword', MSVarchar(1000, isNull=True)),
        ('WebClassificationTable', MSVarchar(50, isNull=True)),
        ('TopWebClassifications', MSBit())
    ])

    def __init__(self, fields_dict={}):
        """constructor -> sends deep copy of fields to superclass

        Args:
            fields_dict (dict, optional): initial values of object. Defaults to {}.
        """

        super().__init__(copy.deepcopy(self.fields), self.TABLE_NAME, fields_dict)


class TronPosWebClassifications(SchemaObject):
    """Schema class for TronPosWebClassifications"""

    TABLE_NAME = "TronPosWebClassifications"

    fields = OrderedDict([
        ('id', MSInt(isPK=True)),
        ('tpfirm_id', MSInt(isFK=True)),
        ('TopWebClassificationGUID', MSVarchar(255)),
        ('Name', MSVarchar(50, isNull=True))
    ])

    def __init__(self, fields_dict={}):
        """constructor -> sends deep copy of fields to superclass

        Args:
            fields_dict (dict, optional): initial values of object. Defaults to {}.
        """

        super().__init__(copy.deepcopy(self.fields), self.TABLE_NAME, fields_dict)

