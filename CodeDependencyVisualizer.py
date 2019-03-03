#!/usr/bin/env python
# inspired by https://github.com/gklingler/CodeDependencyVisualizer
import clang.cindex
import os
import logging
import fnmatch

index = clang.cindex.Index.create()

class UmlClass:
    MEMBER_PROP_MAP = {
        'private': '-',
        'public': '+',
        'protected': '#'
    }

    LINK_TYPE_MAP = {
        'inherit': '<|--',
        'aggregation': 'o--',
        'composition': '*--'
    }

    def __init__(self):
        self.fqn = None
        self.nameSpace = None
        self.parents = []
        self.privateFields = []
        self.privateMethods = []
        self.publicFields = []
        self.publicMethods = []
        self.protectedFields = []
        self.protectedMethods = []

    def addParentByFQN(self, fullyQualifiedClassName):
        self.parents.append(fullyQualifiedClassName)

    def isEmbpty(self):
        if not self.parents and not self.privateFields and not self.privateMethods and not self.publicFields and not self.publicMethods and not self.protectedFields and not self.protectedMethods:
            return True
        return False

    def __str__(self):
        r = ""
        if self.nameSpace is not None:
            r += "namespace " + self.nameSpace
        r += "class " + self.fqn + " {\n"

        for p in self.privateFields:
            r += "\t-" + p[0] + " : " + p[1] + "\n"
        for p in self.publicFields:
            r += "\t+" + p[0] + " : " + p[1] + "\n"

        for p in self.privateMethods:
            r += "\t-" + p[1] + p[2] + " : " + p[0] + "\n"
        for p in self.publicMethods:
            r += "\t+" + p[1] + p[2] + " : " + p[0] + "\n"
        r += "}\n"
        return r


class PumlFile:
    LINK_TYPE_MAP = {
        'inherit': '<|--',  # héritage
        'aggregation': '<--o',  # une classe
        'composition': '<--*',  # une classe mais ils sont dépendants
        'association': '<--',  # un pointer
        'dependency': '<..'  # est utilisé dans les entete
    }

    def __init__(self):
        self.umlClass = {}
        self.inherit = {}
        self.aggregation = {}
        self.composition = {}
        self.association = {}
        self.dependency = {}

    def addClass(self, uml):
        self.umlClass[uml.fqn] = uml

    def __str__(self):
        r = "@startuml\n"
        for key, value in self.umlClass.items():
            r += str(value)
            r += "\n"

        r += "@enduml\n"
        return r

    def linkClass(self):
        for u in self.umlClass:
            print(u)

        print()
        print("test :")

        for uk, u in self.umlClass.items():
            for v in [x for x in u.privateFields if x[1] in self.umlClass]:
                u.privateFields.remove(v)
                
                print(v[1])


pumlFile = PumlFile()

def findFilesInDir(rootDir, patterns):
    """ Searches for files in rootDir which file names mathes the given pattern. Returns
    a list of file paths of found files"""
    foundFiles = []
    for root, dirs, files in os.walk(rootDir):
        for p in patterns:
            for filename in fnmatch.filter(files, p):
                foundFiles.append(os.path.join(root, filename))
    return foundFiles


def processClassField(cursor):
    """ Returns the name and the type of the given class field.
    The cursor must be of kind CursorKind.FIELD_DECL"""
    type = None
    fieldChilds = list(cursor.get_children())
    if len(fieldChilds) == 0:  # if there are not cursorchildren, the type is some primitive datatype
        type = cursor.type.spelling
    else:  # if there are cursorchildren, the type is some non-primitive datatype (a class or class template)
        for cc in fieldChilds:
            if cc.kind == clang.cindex.CursorKind.TEMPLATE_REF:
                type = cc.spelling
            elif cc.kind == clang.cindex.CursorKind.TYPE_REF:
                type = cursor.type.spelling
    name = cursor.spelling
    return name, type


def processClassMemberDeclaration(umlClass, cursor):
    """ Processes a cursor corresponding to a class member declaration and
    appends the extracted information to the given umlClass """
    if cursor.kind == clang.cindex.CursorKind.CXX_BASE_SPECIFIER:
        for baseClass in cursor.get_children():
            if baseClass.kind == clang.cindex.CursorKind.TEMPLATE_REF:
                umlClass.parents.append(baseClass.spelling)
            elif baseClass.kind == clang.cindex.CursorKind.TYPE_REF:
                umlClass.parents.append(baseClass.type.spelling)
    elif cursor.kind == clang.cindex.CursorKind.FIELD_DECL:  # non static data member
        name, type = processClassField(cursor)
        if name is not None and type is not None:
            # clang < 3.5: needs patched cindex.py to have
            # clang.cindex.AccessSpecifier available:
            # https://gitorious.org/clang-mirror/clang-mirror/commit/e3d4e7c9a45ed9ad4645e4dc9f4d3b4109389cb7
            if cursor.access_specifier == clang.cindex.AccessSpecifier.PUBLIC:
                umlClass.publicFields.append((name, type))
            elif cursor.access_specifier == clang.cindex.AccessSpecifier.PRIVATE:
                umlClass.privateFields.append((name, type))
            elif cursor.access_specifier == clang.cindex.AccessSpecifier.PROTECTED:
                umlClass.protectedFields.append((name, type))
    elif cursor.kind == clang.cindex.CursorKind.CXX_METHOD:
        try:
            returnType, argumentTypes = cursor.type.spelling.split(' ', 1)
            if cursor.access_specifier == clang.cindex.AccessSpecifier.PUBLIC:
                umlClass.publicMethods.append((returnType, cursor.spelling, argumentTypes))
            elif cursor.access_specifier == clang.cindex.AccessSpecifier.PRIVATE:
                umlClass.privateMethods.append((returnType, cursor.spelling, argumentTypes))
            elif cursor.access_specifier == clang.cindex.AccessSpecifier.PROTECTED:
                umlClass.protectedMethods.append((returnType, cursor.spelling, argumentTypes))
        except:
            logging.error("Invalid CXX_METHOD declaration! " + str(cursor.type.spelling))
    elif cursor.kind == clang.cindex.CursorKind.FUNCTION_TEMPLATE:
        returnType, argumentTypes = cursor.type.spelling.split(' ', 1)
        if cursor.access_specifier == clang.cindex.AccessSpecifier.PUBLIC:
            umlClass.publicMethods.append((returnType, cursor.spelling, argumentTypes))
        elif cursor.access_specifier == clang.cindex.AccessSpecifier.PRIVATE:
            umlClass.privateMethods.append((returnType, cursor.spelling, argumentTypes))
        elif cursor.access_specifier == clang.cindex.AccessSpecifier.PROTECTED:
            umlClass.protectedMethods.append((returnType, cursor.spelling, argumentTypes))


def processClass(cursor):
    """ Processes an ast node that is a class. """
    umlClass = UmlClass()
    if cursor.kind == clang.cindex.CursorKind.CLASS_TEMPLATE:
        umlClass.fqn = cursor.spelling
    else:
        umlClass.fqn = cursor.type.spelling

    for c in cursor.get_children():
        processClassMemberDeclaration(umlClass, c)

    if not umlClass.isEmbpty():
        pumlFile.addClass(umlClass)


def traverseAst(cursor, dirs):
    if (cursor.location.file is not None and (
            cursor.kind == clang.cindex.CursorKind.CLASS_DECL
            or cursor.kind == clang.cindex.CursorKind.CLASS_TEMPLATE
    )):
        for d in dirs:
            if d in os.path.normpath(cursor.location.file.name):
                # print(str(os.path.normpath(cursor.location.file.name)) + " -- " + str(dirs))
                # print(cursor.kind)
                # print(cursor.type.spelling)
                processClass(cursor)
                break

    for child_node in cursor.get_children():
        traverseAst(child_node, dirs)


def parseTranslationUnit(filePath, srcDir, clangArgs):
    #clangArgs = ['-x', 'c++'] + ['-I' + includeDir for includeDir in includeDirs]
    tu = index.parse(filePath, args=clangArgs, options=clang.cindex.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES)
    for diagnostic in tu.diagnostics:
        print(diagnostic)
    # print('Translation unit:' + tu.spelling + "\n")

    dirs = []
    dirs.extend(includeDirs)
    dirs.append(srcDir)
    traverseAst(tu.cursor, dirs)


# directory = '../BlobTest/src'
# include = ['../BlobTest/include']

directory = '../BlobManager/src/'
#include = ['../BOmberBlob/include']
jsonCompileCommand = '../BlobManager/cmake-build-debug/'
withUnusedHeaders = False

compdb = clang.cindex.CompilationDatabase.fromDirectory(jsonCompileCommand)

directory = os.path.abspath(os.path.normpath(directory))
#for idx, val in enumerate(include):
#    include[idx] = os.path.abspath(os.path.normpath(val))

filesToParse = findFilesInDir(directory, ['*.cpp', '*.cxx', '*.c', '*.cc'])

for sourceFile in filesToParse:
    try:
        file_args = compdb.getCompileCommands(sourceFile)

        for i in range(len(file_args)):
            print("cc" + str(i) + " arguments :")
            cc = file_args[i]
            clangArgs = []
            conf.
            for j in range(len(cc.arguments)):
                ccc = cc[j]
                print(ccc)
                clangArgs.append(ccc)
            #clangArgs.pop(0)
            #clangArgs.pop(0)
            print(clangArgs[1])
            print()
            clangArgs = [clangArgs[1]]
            os.chdir(cc.directory)
            parseTranslationUnit(cc.filename, directory, cc.arguments)
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)

pumlFile.linkClass()
print(pumlFile)
