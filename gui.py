#!/usr/bin/env python3

import inspect
from models import TronPosWebClassifications, TronPosOdooExchangeUp, MSDatetime, MSInt, MSBigInt, MSBit
from tkcalendar import Calendar, DateEntry
import copy
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from os import path
import sys
import pymssql
import configparser
import traceback


def db_error_handler(func):
    """function used as decorator for error handling communication with DB

    Args:
        func (function): function to wrap in decorator
    """
    def inner_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except pymssql.IntegrityError as e:
            print("error")
            if(e.args[0] == 2627):
                print("PK alredy exists")
                messagebox.showerror(
                    "Napaka", "Že obstaja objekt z takim primarnim ključem")
            elif(e.args[0] == 547):
                messagebox.showerror(
                    "Napaka", "Dokument ne referencira nobenega drugega objekta")

        except pymssql.Error as e:
            print("Unable to connect to db")
            messagebox.showerror(
                "Napaka", "Neuspešno spajanje na bazo")
        except:

            traceback.print_tb(sys.exc_info()[2])

            print("Internal error")

    return inner_func


class ObjectTreeView(ttk.Treeview):
    """ Wrapped class for tkk.Treeview for schema classes"""

    def __init__(self, schemaobject, *args, **kwargs):
        """constuctor

        Args:
            schemaobject (schema class): schema class
        """
        super().__init__(*args, **kwargs)

        objectfields = [k for k, _ in schemaobject.fields.items()]

        self['columns'] = objectfields[1:]

        self.column("#0", stretch=tk.NO)
        self.heading("#0", text=objectfields[0], anchor=tk.CENTER,
                     command=lambda _col="#0": self.sortoncolumn(_col, False))

        for name in (objectfields[1:]):
            self.heading(name, text=name, anchor=tk.CENTER,
                         command=lambda _col=name: self.sortoncolumn(_col, False))
            self.column(name, stretch=tk.NO)

    def sortoncolumn(self, col, reverse):
        """function for sorting items when clicking on column

        Args:
            col (Treeview iid): string
            reverse (bool): if True, sort in reversed order, else sort in normal order
        """
        if(col == "#0"):
            l = [((int(k), k), k) for k in self.get_children('')]
        else:
            l = [(self.set(k, col), k) for k in self.get_children('')]

        l.sort(reverse=reverse)

        for index, (_val, k) in enumerate(l):
            self.move(k, '', index)

        self.heading(
            col, command=lambda _col=col: self.sortoncolumn(_col, not reverse))

    def insertObject(self, schema_object, index='end'):
        """inserts object into treeview

        Args:
            schema_object (schema object): schema object to insert
            index (str, optional): treeview index. Defaults to 'end'.
        """

        obj_values = schema_object.getFieldValuesSQL()
        self.insert(
            '', index, iid=obj_values[0], text=obj_values[0], values=obj_values[1:])

    def refreshObject(self, schema_object, last_id=None):
        """refreshes object in treeview

        Args:
            schema_object (schema object): schema object to refresh
            last_id (treeview iid, optional): iid of object. Defaults to None. If none, then value is taken from object clone
        """
        if(last_id is None):
            last_id = schema_object.clone.getFieldValuesSQL()[0]

        current_index = 'end'
        if(self.exists(last_id)):
            current_index = self.index(last_id)
            self.delete(last_id)

        self.insertObject(schema_object, current_index)


class TreeFrame(tk.Frame):
    """frame that contains treeview, with added scrollbars"""
    def __init__(self, schemaobject, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.treeview = ObjectTreeView(schemaobject, self)
        self.treeview.selection_remove()

        scrollbar_vertical = tk.Scrollbar(
            self, orient="vertical", command=self.treeview.yview)
        scrollbar_horizontal = tk.Scrollbar(
            self, orient="horizontal", command=self.treeview.xview)

        self.treeview.grid(column=0, row=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.treeview.configure(
            yscrollcommand=scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set)

        scrollbar_vertical.grid(column=1, row=0, sticky="nsw")
        scrollbar_horizontal.grid(column=0, row=1, sticky="sew")

        self.pack(fill=tk.BOTH, expand=1)


class ObjectView(tk.Frame):
    """main class for viewing object, with basic functionality"""
    @db_error_handler
    def cb(self, originalobject, newobject, window):
        """callback function, which is to be called when object is ready to be inserted or modified

        Args:
            originalobject (schema object): this is original object. If it's None, that means that is for insert, otherwise it's for update
            newobject (schema object): new object to be inserted/updated
            window (tk.Toplevel): dialog window, which is closed at the end
        """
        final_value = 0
        if(originalobject is None):
            final_value = newobject.insertObject(
                self.root_object.CONNECTION_PARAMETERS)
            self.treeview.insertObject(newobject)

        else:
            oldid = newobject.clone.getField('id')
            final_value = newobject.updateObject(
                self.root_object.CONNECTION_PARAMETERS)
            self.treeview.refreshObject(newobject, oldid)

        if(final_value > 0):
            window.destroy()

    def __init__(self, schemaobject, *args, root_object, **kwargs):
        """constuctor

        Args:
            schemaobject (schema object or class): class or object, used for fetching objects
            root_object (tk.Tk): root tk object contaning connection parameters for DB
        """
        super().__init__(*args, **kwargs)

        self.root_object = root_object
        self.schemaobject = schemaobject
        self.button_toolbar = tk.Frame(self)

        self.addbutton = tk.Button(
            self.button_toolbar, text='Dodaj', command=lambda: ObjectDialog(schemaobject, self.cb, self))
        self.modifybutton = tk.Button(
            self.button_toolbar, text='Spremeni', command=self.modify_button)
        self.deletebutton = tk.Button(
            self.button_toolbar, text='Briši', command=self.delete_button)

        self.addbutton.pack(side=tk.LEFT, )
        self.modifybutton.pack(side=tk.LEFT, padx=5)
        self.deletebutton.pack(side=tk.LEFT, padx=5)

        self.button_toolbar.pack(fill=tk.X, ipady=10)

        tree_frame = TreeFrame(schemaobject, self)
        self.treeview = tree_frame.treeview
        self.treeview.bind('<<TreeviewSelect>>', self.selection_handler)
        self.treeview.bind('<Double-1>', lambda e: self.modify_button())


        self.treeview.selection_remove()

        tree_frame.pack(fill=tk.BOTH, expand=1)

    def selection_handler(self, event):
        if(len(self.treeview.selection()) == 1):
            self.modifybutton.configure(state=tk.NORMAL)
        else:
            self.modifybutton.configure(state=tk.DISABLED)

        if(len(self.treeview.selection()) < 1):
            self.deletebutton.configure(state=tk.DISABLED)
        else:
            self.deletebutton.configure(state=tk.NORMAL)

    @db_error_handler
    def modify_button(self):
        """Modify action of object. This action should be called only when single object is selected."""
        item = self.treeview.selection()[0]

        idd = self.treeview.item(item)['text']
        tt = self.schemaobject.FetchObjectsWhere(
            self.root_object.CONNECTION_PARAMETERS, {self.schemaobject.GetPK()[0]: idd})
        tta = tt[0]

        ObjectDialog(tta, self.cb)

    @db_error_handler
    def delete_button(self):
        """Delete action. If multiple objects are selected, all of them will be deleted.
        """
        toDelete = tk.messagebox.askokcancel(
            'Brisanje dokumenta', 'Če izbrišete ta dokument, boste izbrisali tudi vse povezane dokumente. Ali želite nadaljevati?', icon='warning')

        if(toDelete is False):
            return

        items = self.treeview.selection()

        for item in items:
            idd = self.treeview.item(item)['text']


            tt = self.schemaobject.FetchObjectsWhere(
                self.root_object.CONNECTION_PARAMETERS, {self.schemaobject.GetPK()[0]: idd})
            tta = tt[0]

            fkitems = TronPosWebClassifications.FetchObjectsWhere(
                self.root_object.CONNECTION_PARAMETERS, {'tpfirm_id': tta.getField('tpfirm_id')})

            for fkitem in fkitems:
                fkitem.deleteObject(self.root_object.CONNECTION_PARAMETERS)

            tta.deleteObject(self.root_object.CONNECTION_PARAMETERS)

            self.treeview.delete(idd)



class TronPosOdooExchangeUpView(ObjectView):
    """View class for TronPosOdooExchangeUpView"""
    def __init__(self, *args, root_object, **kwargs):
        """constructor. Adds buttons for display of connected foregin objects.

        Args:
            root_object (tk.Tk): root_object (tk.Tk): root tk object contaning connection parameters for DB

        """
        super().__init__(*args, root_object=root_object, **kwargs)
        

        self.showbutton = tk.Button(
            self.button_toolbar, text='Pokaži zunanje povezave na dokument', command=self.show_fk)
        self.showallbutton = tk.Button(
            self.button_toolbar, text='Pokaži vse zunanje povezave', command=self.showall_fk)
        self.testbutton = tk.Button(
            self.button_toolbar, text='Poveži', command=self.test_method)

        self.showbutton.pack(side=tk.LEFT, padx=5)
        self.showallbutton.pack(side=tk.LEFT, padx=5)
        self.testbutton.pack(side=tk.LEFT, padx=5)

        self.treeview.bind('<<TreeviewSelect>>', self.selection_handle)
        self.treeview.selection_remove()

    def test_method(self):
        """Test method. Logic will be added here
        """
        pass

    def selection_handle(self, event):
        """function that is called when selection of treeview is changed. Enables and disables buttons.

        Args:
            event (tk event): selection event, not used here, added for compatibility
        """
        if(len(self.treeview.selection()) == 1):
            self.modifybutton.configure(state=tk.NORMAL)
            self.showbutton.configure(state=tk.NORMAL)
            self.testbutton.configure(state=tk.NORMAL)
        else:
            self.modifybutton.configure(state=tk.DISABLED)
            self.showbutton.configure(state=tk.DISABLED)
            self.testbutton.configure(state=tk.DISABLED)

        if(len(self.treeview.selection()) < 1):
            self.deletebutton.configure(state=tk.DISABLED)
        else:
            self.deletebutton.configure(state=tk.NORMAL)

    @db_error_handler
    def show_fk(self):
        """shows all foregin key connected objects
        """
        if(len(self.treeview.selection()) < 1):
            return

        item = self.treeview.selection()[0]

        idd = self.treeview.item(item)['text']

        received_objs = self.schemaobject.FetchObjectsWhere(
            self.root_object.CONNECTION_PARAMETERS, {self.schemaobject.GetPK()[0]: idd})
        selected_obj = received_objs[0]

        fk_objs = TronPosWebClassifications.FetchObjectsWhere(
            self.root_object.CONNECTION_PARAMETERS, {'tpfirm_id': selected_obj.getField('tpfirm_id')})

        topW = tk.Toplevel(self)
        topW.title('Povezave na {}'.format(idd))

        view = ObjectView(TronPosWebClassifications, topW, root_object=self.root_object)


        for fk_obj in fk_objs:
            view.treeview.insertObject(fk_obj)
        view.pack(expand=1, fill=tk.BOTH)

    @db_error_handler
    def showall_fk(self):
        """shows all objects from TronPosWebClassifications
        """
        fk_objs = TronPosWebClassifications.FetchAllObjects(
            self.root_object.CONNECTION_PARAMETERS)

        topW = tk.Toplevel(self)
        topW.title('TronPosWebClassifications')

        view = ObjectView(TronPosWebClassifications, topW, root_object=self.root_object)

        for fk_obj in fk_objs:
            view.treeview.insertObject(fk_obj)
        view.pack(expand=1, fill=tk.BOTH)

    @db_error_handler
    def cb(self, originalobject, newobject, window):
        """callback function, which is to be called when object is ready to be inserted or modified. This one also checks if foregin key objects needs to be updated

        Args:
            originalobject (schema object): this is original object. If it's None, that means that is for insert, otherwise it's for update
            newobject (schema object): new object to be inserted/updated
            window (tk.Toplevel): dialog window, which is closed at the end
        """

        final_value = 0

        if(originalobject is None):

            final_value = newobject.insertObject(
                self.root_object.CONNECTION_PARAMETERS)
            self.treeview.insertObject(newobject)

        else:
            if(newobject.getField('tpfirm_id') != newobject.clone.getField('tpfirm_id')):
                # Needs PK check 
                id_list = TronPosOdooExchangeUp.FetchObjectsWhere(
                    self.root_object.CONNECTION_PARAMETERS, {'tpfirm_id': newobject.getField('tpfirm_id')})

                if(len(id_list) > 0):
                    messagebox.showerror(
                        'Napaka', 'Že obstaja objekt z takim primarnim ključem')
                    return

                # Check if FK objects exist
                objs = TronPosWebClassifications.FetchObjectsWhere(
                    self.root_object.CONNECTION_PARAMETERS, {'tpfirm_id': newobject.clone.getField('tpfirm_id')})
                if(len(objs) > 0):
                    toUpdate = tk.messagebox.askokcancel(
                        'Zunanja povezava', 'Na dokument obstajajo zunanje povezave. Za nadaljevanje je potrebno vezane dokumente spremeniti. Želite nadaljevati?', icon='warning')
                    if(toUpdate):
                        original_copy = copy.deepcopy(newobject.clone)
                        final_value = newobject.insertObject(
                            self.root_object.CONNECTION_PARAMETERS)
                        for objfk in objs:
                            objfk.setField(
                                'tpfirm_id', newobject.getField('tpfirm_id'))
                            objfk.updateObject(
                                self.root_object.CONNECTION_PARAMETERS)
    
                        original_copy.deleteObject(
                            self.root_object.CONNECTION_PARAMETERS)
                        self.treeview.refreshObject(
                            newobject, original_copy.getField('tpfirm_id'))

                else:
                    # No FK objects present
                    oldid = newobject.clone.getField('tpfirm_id')
                    final_value = newobject.updateObject(
                        self.root_object.CONNECTION_PARAMETERS)
                    self.treeview.refreshObject(newobject, oldid)
            else:
                # No primary key collision
                oldid = newobject.clone.getField('tpfirm_id')
                final_value = newobject.updateObject(
                    self.root_object.CONNECTION_PARAMETERS)
                self.treeview.refreshObject(newobject, oldid)

        if(final_value > 0):
            window.destroy()


class ObjectDialog(tk.Toplevel):
    def __init__(self, schemaobject, cb, *args, **kwargs):
        """edit view/dialog for schema object

        Args:
            schemaobject (schema object or class): If it's object, then it populated edit field of that object. If it's class, then values are set to default.
            cb (function): callback function to be called when object is read for modify/insert
        """


        super().__init__(*args, **kwargs)

        self.cb = cb

        self.frame_container = tk.Frame(self)

        self.binded_vars = {}

        if(inspect.isclass(schemaobject)):
            self.originalobject = None
            self.schemaobject = schemaobject()
            self.title('Novi objekt')
        else:
            self.originalobject = schemaobject
            self.schemaobject = copy.deepcopy(schemaobject)
            self.title('Objekt {}'.format(
                schemaobject.getPKfield().getValueSQL()))

        for i, (field_name, mstype) in enumerate(schemaobject.fields.items()):
            entry_label = tk.Label(self.frame_container,
                         text="{} [{}]".format(field_name, mstype.DESCRIPTOR))
            self.binded_vars[field_name] = {'type': mstype}

            if(type(mstype) in (MSInt, MSBigInt, MSBit)):
                binded_var = tk.IntVar()
            else:
                binded_var = tk.StringVar()

            self.binded_vars[field_name]['var'] = binded_var

            if(mstype.getValue() is not None):
                binded_var.set(mstype.getValue())

            main_entry = tk.Entry(self.frame_container, textvariable=binded_var)

            if(isinstance(mstype, MSDatetime)):
                main_entry = DateEntry(self.frame_container, width=12, background='darkblue',
                               foreground='white', borderwidth=2, state="readonly")
                date_val = mstype.getValue()
                if(date_val is not None):
                    main_entry.set_date(date_val)
                self.binded_vars[field_name]['var'] = main_entry

            elif(isinstance(mstype, MSBit)):
                main_entry = tk.Checkbutton(self.frame_container)
                if(binded_var.get() == 1):
                    main_entry.select()
                main_entry.configure(variable=binded_var)

            self.binded_vars[field_name]['control'] = main_entry

            entry_label.grid(row=i, column=0)
            main_entry.grid(row=i, column=1)

            if(mstype.isNull):
                isnullvar = tk.IntVar()
                self.binded_vars[field_name]['null'] = isnullvar

                checkboxbtn = tk.Checkbutton(
                    self.frame_container, text='NULL', command=lambda main_entry=main_entry, isnullvar=isnullvar: toggleMe(isnullvar, main_entry))
                if(mstype.getValue() is None):
                    isnullvar.set(1)
                    checkboxbtn.select()
                    toggleMe(isnullvar, main_entry)
                checkboxbtn.configure(variable=isnullvar)
                checkboxbtn.grid(row=i, column=2)

        if(self.originalobject is None):
            button_text = "Kreiraj"
        else:
            button_text = "Shrani"

        tk.Button(self.frame_container, text=button_text,
                  command=self.parseObject).grid(row=i+1, columnspan=3, ipadx=20, pady=10)

        self.frame_container.pack()

    def parseObject(self):
        """function that check if object is valid

        Raises:
            ValueError: raised if value is not valid
        """
        error_count = 0
        for fieldname, values_dict in self.binded_vars.items():
            if('null' in values_dict and values_dict['null'].get() == 1):
                self.schemaobject.setField(fieldname, None)
            else:
                try:
                    if(isinstance(values_dict['var'], DateEntry)):
                        testvalue = values_dict['var'].get_date()
                    else:
                        testvalue = values_dict['var'].get()

                    originalvalue = self.schemaobject.getField(fieldname)
                    self.schemaobject.setField(fieldname, testvalue)
                    if(self.schemaobject.fields[fieldname].isValueOK() is False):
                        self.schemaobject.setField(fieldname, originalvalue)
                        raise ValueError

                    if(isinstance(values_dict['var'], DateEntry)):
                        style = ttk.Style()
                        style.configure('my.DateEntry', foreground='black')
                        values_dict['control'].configure(style='my.DateEntry')
                    else:
                        values_dict['control'].configure(fg='black')

                except:
                    if(isinstance(values_dict['var'], DateEntry)):
                        style = ttk.Style()
                        style.configure('my.DateEntry', foreground='red')
                        values_dict['control'].configure(style='my.DateEntry')
                    else:
                        values_dict['control'].configure(fg='red')
                    error_count += 1

        if(error_count < 1):
            self.cb(self.originalobject, self.schemaobject, self)


def toggleMe(var, controlEntry):
    """function that handles toggling of entry fields, used for "isNull" option 

    Args:
        var (tk IntVar): IntVar binded to "isNull" checkbox
        controlEntry (tk Widget): Widget that is enabled or disabled
    """
    if(var.get() == 1):
        controlEntry.configure(state=tk.DISABLED)
    else:
        if(isinstance(controlEntry, DateEntry)):
            controlEntry.configure(state='readonly')
        else:
            controlEntry.configure(state=tk.NORMAL)


@db_error_handler
def test_connection(connection_parameters):
    """functions that quickly checks if connection to DB is successful

    Args:
        connection_parameters (kwargs dict): pymssql connection parameters

    Returns:
        bool: True if connection is available, False otherwise
    """
    with pymssql.connect(**connection_parameters) as conn:
        with conn.cursor(as_dict=True) as cursor:
            return True


class MainWindow(tk.Tk):
    """main control tk Element"""

    CONFIG_FILE = "config.ini"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lift()
        self.attributes('-topmost', True)
        self.attributes('-topmost', False)
        self.withdraw()

        config = configparser.ConfigParser()

        if(path.isfile(self.CONFIG_FILE)):
            config.read(self.CONFIG_FILE)

        else:
            # Write default file
            config['CONNECTION_SETTINGS'] = {
                'dbhost': 'localhost',
                'dbname': 'OdooExchangeSync',
                'dbuser': 'SA',
                'dbpass': '<YourStrong@Passw0rd>'
            }
            with open(self.CONFIG_FILE, "w") as f:
                config.write(f)

        self.CONNECTION_PARAMETERS = {}

        try:
            self.CONNECTION_PARAMETERS['server'] = config['CONNECTION_SETTINGS']['dbhost']
            self.CONNECTION_PARAMETERS['database'] = config['CONNECTION_SETTINGS']['dbname']
            self.CONNECTION_PARAMETERS['user'] = config['CONNECTION_SETTINGS']['dbuser']
            self.CONNECTION_PARAMETERS['password'] = config['CONNECTION_SETTINGS']['dbpass']
        except KeyError as _:
            print("ERR")
            messagebox.showerror(
                "Napaka", "Nepravilna konfiguracijska datoteka")
            sys.exit()

        if(test_connection(self.CONNECTION_PARAMETERS) is not True):
            sys.exit()

        self.deiconify()

        self.geometry("1366x768")

        tv = TronPosOdooExchangeUpView(
            TronPosOdooExchangeUp, self, root_object=self)

        testsObjs = TronPosOdooExchangeUp.FetchAllObjects(
            self.CONNECTION_PARAMETERS)

        for obi in testsObjs:
            tv.treeview.insertObject(obi)
        tv.pack(expand=1, fill=tk.BOTH)


mainwindow = MainWindow()
mainwindow.title('Glavno okno')

mainwindow.mainloop()
