#!/usr/bin/env python
# inspired by https://github.com/gklingler/CodeDependencyVisualizer

import clang.cindex
import os
import fnmatch

from UmlFile import *


VISIBILITY = {
    clang.cindex.AccessSpecifier.PUBLIC: '+',
    clang.cindex.AccessSpecifier.PROTECTED: '#',
    clang.cindex.AccessSpecifier.PRIVATE: '-'
}


def getNamespace(cursor, namespace):
    c = cursor.semantic_parent
    if c.kind == clang.cindex.CursorKind.TRANSLATION_UNIT:
        return namespace
    else:
        namespace = getNamespace(c, namespace)
        namespace.add(c.displayname)
        return namespace


def propagate(cursor, parent=None):
    for child in cursor.get_children():
        if child.kind in actions:
            actions[child.kind](child, parent)
        else:
            unknownKind(child, parent)


def class_decl(cursor, parent=None):
    if cursor.is_anonymous():
        return

    n = getNamespace(cursor, UmlNamespace())
    id = '.'.join(n.namespace + [cursor.displayname])
    if parent is not None:
        n = parent.namespace.copy()
    c = UmlClass(id, n, cursor.displayname)
    if c.id not in umlFile.umlClass:
        umlFile.umlClass[c.id] = c
    else:
        c = umlFile.umlClass[c.id]

    # print("class_decl   : " + c.id.ljust(70) + str(cursor.kind).ljust(40) + cursor.displayname)
    propagate(cursor, c)


def cxx_method(cursor, parent=None):
    if parent is None:
        return

    if cursor.displayname in parent.methods:
        # print("cxx_method EXIST : " + (id + "::" + cursor.displayname).ljust(70) + str(cursor.kind).ljust(40))
        return

    arguments = []
    for a in cursor.get_arguments():
        arguments.append((a.type.spelling, a.spelling))
    parent.methods[cursor.displayname] = UmlMethod(cursor.displayname, cursor.result_type.spelling, "",
                                              VISIBILITY[cursor.access_specifier])
    # print("cxx_method : " + (id + "::" + cursor.displayname).ljust(70) + str(cursor.kind).ljust(40))


def typeToUmlType(type):
    id = None

    t = type

    if type.get_num_template_arguments() == 1 or type.get_num_template_arguments() == 2:
        t = t.get_template_argument_type(0)

    if t.kind == clang.cindex.TypeKind.POINTER or t.kind == clang.cindex.TypeKind.LVALUEREFERENCE:
        t = t.get_pointee()

    if t.kind == clang.cindex.TypeKind.RECORD or t.kind == clang.cindex.TypeKind.ENUM or \
            (t.get_num_template_arguments() == -1 and t.kind == clang.cindex.TypeKind.ELABORATED):
        id = t.get_canonical().spelling.replace("::", '.')


    # TODO: update this
    # if id is None:
    #      print(type.get_canonical().spelling.ljust(50) + str(type.kind).ljust(50) + t.get_canonical().spelling.ljust(50) + str(t.kind))

    if id in umlFile.umlClass:
        return UmlType(type.spelling, umlFile.umlClass[id])

    return UmlType(type.spelling, None)


def field_decl(cursor, parent=None):
    # print("field_decl   : " + '::'.join(getNamespace(cursor, [])).ljust(70) + str(cursor.kind).ljust(40) + cursor.displayname)
    if parent is not None and cursor.displayname not in parent.attributes and not cursor.is_anonymous():
        parent.attributes[cursor.displayname] = UmlAttribubte(cursor.displayname, typeToUmlType(cursor.type),
                                                              VISIBILITY[cursor.access_specifier])


def cxx_base_specifier(cursor, parent=None):
    t = cursor.type.get_canonical().spelling.replace("::", '.')
    if t in umlFile.umlClass:
        parent.parents.add(umlFile.umlClass[t])
    else:
        parent.parentsDistant.add(cursor.type.spelling)
    # print("cxx_base_specifier   : " + parent.id.ljust(40) + str(cursor.type.spelling))


def unknownKind(cursor, parent=None):
    # print("unknown Kind : " + str(cursor.kind).ljust(40) + cursor.displayname)
    propagate(cursor)


actions = {
    clang.cindex.CursorKind.CLASS_DECL: class_decl,
    clang.cindex.CursorKind.CLASS_TEMPLATE: class_decl,
    clang.cindex.CursorKind.STRUCT_DECL: class_decl,

    clang.cindex.CursorKind.CXX_BASE_SPECIFIER: cxx_base_specifier,

    clang.cindex.CursorKind.CXX_METHOD: cxx_method,
    clang.cindex.CursorKind.FUNCTION_TEMPLATE: cxx_method,
    clang.cindex.CursorKind.CONSTRUCTOR: cxx_method,
    clang.cindex.CursorKind.DESTRUCTOR: cxx_method,

    clang.cindex.CursorKind.FIELD_DECL: field_decl,

    clang.cindex.CursorKind.NAMESPACE: propagate,
}

index = clang.cindex.Index.create()

umlFile = UmlFile()

jsonCompileCommand = '../BlobEngine/cmake-build-debug/'

compdb = clang.cindex.CompilationDatabase.fromDirectory(jsonCompileCommand)

source_folder = os.path.abspath('../BlobEngine/src/')
include_folder = os.path.abspath('../BlobEngine/include')

for cc in compdb.getAllCompileCommands():
    if os.path.abspath(cc.filename).startswith(source_folder):
    # if cc.filename == os.path.abspath('../BlobEngine/src/glTF2/SceneManager.cpp'):
        clangArgs = []
        for a in cc.arguments:
            clangArgs.append(a)
        clangArgs.pop(0)
        clangArgs.remove(cc.filename)
        clangArgs.append('-I/lib/clang/10.0.1/include')

        tu = index.parse(cc.filename, args=clangArgs,
                         options=clang.cindex.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES)

        for cursor in tu.cursor.get_children():
            current_file = os.path.abspath(str(cursor.location.file))
            if current_file.startswith(source_folder) or current_file.startswith(include_folder):
                if cursor.kind in actions:
                    actions[cursor.kind](cursor)
                else:
                    unknownKind(cursor)


folder = "test/"
if not os.path.exists(folder):
    os.makedirs(folder)
umlFile.draw(folder)