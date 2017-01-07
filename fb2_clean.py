#!/usr/bin/env python3
# coding: utf8

import argparse
import sys
import os
import zipfile
from xml.dom import minidom
import uuid
import base64
import time

#-------------------------------------------------

def main():
  ap_Parser = argparse.ArgumentParser()

  ap_Parser.add_argument("-b", "--book", help="handle one book")
  ap_Parser.add_argument("-f", "--folder", help="folder for search books (without subfolders)")
  ap_Parser.add_argument("-s", "--subfolders", action="store_true", help="enable search in subfolders")

  ap_Parser.add_argument("-z", "--zip", action="store_true", help="enable result compression")

  ap_Parser.add_argument("-r", "--remove", action="store_true", help="enable removal original file")

  ap_Parser.add_argument("-i", "--ID", action="store_true", help="enable generation book's ID if exist")
  ap_Parser.add_argument("-c", "--clean", action="store_true", help="enable removal incorrect tags")
  #ap_Parser.add_argument("-d", "--cover", action="store_true", help="enable cover image compression if it large than 210x350 px")
  ap_Parser.add_argument("-t", "--tabulation", action="store_true", help="enable alignment indentation")
  ap_Parser.add_argument("-n", "--name", action="store_true", help="enable renaming book")

  ap_Parser.add_argument("-v", "--validation", action="store_true", help="validation only, without writing any changes")

  ap_Parser.add_argument("-d", "--details", action="store_true", help="enable display details during work")

  arg_Args = ap_Parser.parse_args()

  ht_Args = {
    "SUB": arg_Args.subfolders,
    "ZIP": arg_Args.zip,
    "REMOVE": arg_Args.remove,
    "ID": arg_Args.ID,
    "CLEAN": arg_Args.clean,
    "COVER": False,#arg_Args.cover,
    "TABULATION": arg_Args.tabulation,
    "RENAME": arg_Args.name,
    "VALIDATION": arg_Args.validation,
    "DETAILS": arg_Args.details
  }

  time_Start = time.time()

  if arg_Args.book != None:
    # processing single file
    proc_File(arg_Args.book, ht_Args)
  elif arg_Args.folder != None:
    # processing folder
    proc_Folder(arg_Args.folder, ht_Args)
  else:
    printE("One of folowing argument is required: --book, --folder", 0)

  printI("INFO", "Elapsed time: %.3f sec" % (time.time() - time_Start), 1, ht_Args["DETAILS"])
   

#-------------------------------------------------

def proc_Folder(str_Path, ht_Args):
  if os.path.isdir(str_Path):
    printI("PROC", "Processing folder: %s" % str_Path, 1, ht_Args["DETAILS"])

    lst_Objects = os.listdir(str_Path)

    for v_Object in lst_Objects:
      str_PathCurr = os.path.join(str_Path, v_Object)

      if os.path.isfile(str_PathCurr):
        proc_File(str_PathCurr, ht_Args)
      else:
        if ht_Args["SUB"]:
          proc_Folder(str_PathCurr, ht_Args)

  else:
    printE("Not folder: %s" % str_Path, 1)

#-------------------------------------------------

def proc_File(str_Path, ht_Args):
  if os.path.isfile(str_Path):
    lst_ObjectsFB2 = []

    str_Dir = os.path.dirname(str_Path)
    str_NameIn = os.path.basename(str_Path)
    #str_Name, str_Ext = os.path.splitext(os.path.basename(str_Path))
    #print("file \"%s\", extension \"%s\", path \"%s\"" % (str_Name, str_Ext, str_Dir))

    printI("PROC", "Processing file: %s" % str_Path, 1, ht_Args["DETAILS"])

    # unzip
    fill_ListFB2(str_Path, lst_ObjectsFB2, ht_Args)
    #print(lst_ObjectsFB2)

    for str_ObjectFB2 in lst_ObjectsFB2:
      # parse
      md_XML = None
      try:
        md_XML = minidom.parse(str_ObjectFB2[0])
      except:
        printE("Failed to parse file: %s" % str_ObjectFB2[0], 2)
      else:
        printI("PARSE", "Parsing file: %s" % str_ObjectFB2[0], 2, ht_Args["DETAILS"])

        bl_IsChanged = proc_FB2(md_XML, ht_Args)

        # RENAME
        str_NameGen = proc_Name(md_XML, ht_Args, str_ObjectFB2[1])

        # TABULATION
        str_ResultFB2, bl_IsChanged = proc_Tabulation(md_XML, bl_IsChanged, ht_Args)

        # write
        if not ht_Args["VALIDATION"]:
          if bl_IsChanged:
            str_NameOut = proc_Write(str_ResultFB2, str_Dir, str_NameGen, ht_Args)
            if str_NameOut != str_NameIn:
              proc_Remove(str_Path, ht_Args)
          else:
            str_NameOut = proc_NameOut(str_NameGen, ht_Args)
            if str_NameOut != str_NameIn:
              if not os.path.exists(str_NameOut):
                proc_Write(str_ResultFB2, str_Dir, str_NameGen, ht_Args)
              proc_Remove(str_Path, ht_Args)

  else:
    printE("Not file: %s" % str_Path, 1)

#-------------------------------------------------

def proc_Remove(str_Path, ht_Args):
  # REMOVE
  if ht_Args["REMOVE"]:
    if os.path.exists(str_Path):
      printI("INFO", "Removing file: %s" % str_Path, 3, ht_Args["DETAILS"])
      os.remove(str_Path)

#-------------------------------------------------

def proc_NameOut(str_NameGen, ht_Args):
  # ZIP
  if ht_Args["ZIP"]:
    return str_NameGen + ".zip"
  return str_NameGen

def proc_Write(str_ResultFB2, str_Dir, str_NameGen, ht_Args):
  file_FB2 = None
  str_NameOut = ""

  # ZIP
  if ht_Args["ZIP"]:
    str_NameOut = str_NameGen + ".zip"
    file_FB2 = zipfile.ZipFile(os.path.join(str_Dir, str_NameOut), 'w', zipfile.ZIP_DEFLATED)
    file_FB2.writestr(str_NameGen, str_ResultFB2)
  else:
    str_NameOut = str_NameGen
    file_FB2 = open(os.path.join(str_Dir, str_NameOut), "w")
    file_FB2.writelines(str_ResultFB2)

  printI("INFO", "Write file: %s" % str_NameOut, 3, ht_Args["DETAILS"])

  file_FB2.close()
  return str_NameOut

#-------------------------------------------------

def proc_Name(md_XML, ht_Args, str_NameCurr):
  if ht_Args["RENAME"]:
    str_NameGen = fb2_get_book_name(md_XML)
    if str_NameGen == None:
      return str_NameCurr
    #print(str_NameGen)
    return str_NameGen
  return str_NameCurr

#-------------------------------------------------

def proc_FB2(md_XML, ht_Args):
  bl_IsChanged = False

  # ID
  if ht_Args["ID"]:
    bl_IsChanged |= proc_ID(md_XML, ht_Args)

  #print(bl_IsChanged)
  # CLEAN
  if ht_Args["CLEAN"]:
    bl_IsChanged |= proc_Clean(md_XML, ht_Args)
  #print(bl_IsChanged)

  # COVER
  if ht_Args["COVER"]:
    bl_IsChanged |= proc_Cover(md_XML, ht_Args)

  #print(bl_IsChanged)

  return bl_IsChanged

#-------------------------------------------------

def fill_ListFB2(str_Path, lst_ObjectsFB2, ht_Args):
  if zipfile.is_zipfile(str_Path):
    bl_IsBooksInside = False

    zf_File = zipfile.ZipFile(str_Path, "r")
    for str_InnerPath in zf_File.namelist():
      if os.path.splitext(str_InnerPath)[1] == ".fb2":
        bl_IsBooksInside = True

        printI("INFO", "Found fb2 file:  %s" % str_InnerPath, 3, ht_Args["DETAILS"])

        lst_ObjectsFB2.append([zf_File.open(str_InnerPath, "r"), os.path.basename(str_InnerPath)])

    if not bl_IsBooksInside:

      printI("INFO", "Fb2 files not found", 3, ht_Args["DETAILS"])

  else:
    if os.path.splitext(str_Path)[1] == ".fb2":
      lst_ObjectsFB2.append([str_Path, os.path.basename(str_Path)])
    else:

      printI("INFO", "File isn't fb2:  %s" % str_Path, 3, ht_Args["DETAILS"])

#-------------------------------------------------
#===================== COVER =====================
#-------------------------------------------------

def proc_Cover(md_XML, ht_Args):
  node_FictionBook = md_XML.getElementsByTagName("FictionBook")
  if len(node_FictionBook) == 1:
    node_Description = node_FictionBook[0].getElementsByTagName("description")
    if len(node_Description) == 1:
      node_TitleInfo = node_Description[0].getElementsByTagName("title-info")
      if len(node_TitleInfo) == 1:
        node_Coverpage = node_TitleInfo[0].getElementsByTagName("coverpage")
        if len(node_Coverpage) == 1:
          node_CoverImages = node_Coverpage[0].getElementsByTagName("image")
          if len(node_CoverImages) > 0:

            for node_CoverImage in node_CoverImages:

              ht_IAtts = node_CoverImage.attributes or {}
              for str_IKey, str_IVal in ht_IAtts.items():
                if len(str_IKey) > 4 and  str_IKey[-4:] == "href":
                  node_Binaries = node_FictionBook[0].getElementsByTagName("binary")
                  for node_Binary in node_Binaries:
                    bl_IsCurrent = False
                    ht_BAtts = node_Binary.attributes or {}
                    for str_BKey, str_BVal in ht_BAtts.items():
                      if str_BKey == "id" and str_BVal == str_IVal[1:]:
                        print("got it!")
                        node_Text = node_Binary.firstChild
                        if node_Text != None and node_Text.nodeType == node_Text.TEXT_NODE:
                          f_Img = open("out.jpg", "wb")
                          str_OutImg = ""
                          try:
                            str_OutImg = base64.decodestring(node_Text.nodeValue.encode('ascii'))
                          except:
                            printE("Cover image %s incorrect" % str_BVal, 3)
                          else:
                            f_Img.write(str_OutImg)
                            f_Img.close()
                            return True
                          f_Img.close()
                        else:
                          printE("Cover image %s empty or incorrect" % str_BVal, 3)
            return False
          else:
            printE("Current fb2 file totally incorrect: expected cover images, but nothing found", 3)
            return False
        elif len(node_Coverpage) == 0:
          return False
          

  printE("Current fb2 file totally incorrect; cover images aren't processed", 3)
  return False

  
#-------------------------------------------------
#===================== NODES =====================
#-------------------------------------------------

lst_Inlines = ["", "strong", "emphasis", "style", "a", "strikethrough", "sub", "sup", "code", "image"]

ht_Nodes = {
  "genre":          [""],
  "author":         ["first-name", "middle-name", "last-name", "nickname", "home-page", "email", "id"],
  "first-name":     [""],
  "middle-name":    [""],
  "last-name":      [""],
  "nickname":       [""],
  "home-page":      [""],
  "email":          [""],
  "id":             [""],
  "book-title":     [""],
  "p":              ["", "strong", "emphasis", "style", "a", "strikethrough", "sub", "sup", "code", "image"],
  "strong":         ["", "strong", "emphasis", "style", "a", "strikethrough", "sub", "sup", "code", "image"],
  "emphasis":       ["", "strong", "emphasis", "style", "a", "strikethrough", "sub", "sup", "code", "image"],
  "style":          ["", "strong", "emphasis", "style", "a", "strikethrough", "sub", "sup", "code", "image"],
  "a":              ["", "strong", "emphasis", "style", "strikethrough", "sub", "sup", "code", "image"],
  "strikethrough":  ["", "strong", "emphasis", "style", "a", "strikethrough", "sub", "sup", "code", "image"],
  "sub":            ["", "strong", "emphasis", "style", "a", "strikethrough", "sub", "sup", "code", "image"],
  "sup":            ["", "strong", "emphasis", "style", "a", "strikethrough", "sub", "sup", "code", "image"],
  "code":           ["", "strong", "emphasis", "style", "a", "strikethrough", "sub", "sup", "code", "image"],
  "image":          [],
  "title":          ["p", "empty-line"],
  "empty-line":     [],
  "subtitle":       ["", "strong", "emphasis", "style", "a", "strikethrough", "sub", "sup", "code", "image"],
  "text-author":    ["", "strong", "emphasis", "style", "a", "strikethrough", "sub", "sup", "code", "image"],
  "epigraph":       ["p", "poem", "cite", "empty-line", "text-author"],
  "table":          ["tr"],
  "tr":             ["th", "td"],
  "th":             ["", "strong", "emphasis", "style", "a", "strikethrough", "sub", "sup", "code", "image"],
  "td":             ["", "strong", "emphasis", "style", "a", "strikethrough", "sub", "sup", "code", "image"],
  "cite":           ["p", "subtitle", "empty-line", "poem", "table", "text-author"],
  "stanza":         ["title", "subtitle", "v"],
  "v":              ["", "strong", "emphasis", "style", "a", "strikethrough", "sub", "sup", "code", "image"],
  "date":           [""],
  "poem":           ["title", "epigraph", "stanza", "text-author", "date"],
  "annotation":     ["p", "poem", "cite", "subtitle", "empty-line", "table"],
  "keywords":       [""],
  "coverpage":      ["image"],
  "lang":           [""],
  "src-lang":       [""],
  "translator":     ["first-name", "middle-name", "last-name", "nickname", "home-page", "email", "id"],
  "sequence":       [],
  "title-info":     ["genre", "author", "book-title", "annotation", "keywords", "date", "coverpage", "lang", "src-lang", "translator", "sequence"],
  "src-title-info": ["genre", "author", "book-title", "annotation", "keywords", "date", "coverpage", "lang", "src-lang", "translator", "sequence"],
  "document-info":  ["author", "program-used", "date", "src-url", "src-ocr", "id", "version", "history", "publisher"],
  "program-used":   [""],
  "src-url":        [""],
  "src-ocr":        [""],
  "version":        [""],
  "history":        ["p", "poem", "cite", "subtitle", "empty-line", "table"],
  "publisher":      [""],                                                                                 # in publish-info
  "publisher":      ["first-name", "middle-name", "last-name", "nickname", "home-page", "email", "id"],   # in document-info
  "publish-info":   ["book-name", "publisher", "city", "year", "isbn", "sequence"],
  "book-name":      [""],
  "city":           [""],
  "year":           [""],
  "isbn":           [""],
  "custom-info":    [""],
  "output":         ["part", "output-document-class"],
  "part":           [],
  "output-document-class": ["part"],
  "description":    ["title-info", "src-title-info", "document-info", "publish-info", "custom-info", "output"],
  "body":           ["image", "title", "epigraph", "section"],
  "section":        ["title", "epigraph", "image", "annotation", "section", "p", "poem", "subtitle", "cite", "empty-line", "table"],
  "binary":         [""],
  "FictionBook":    ["description", "body", "binary"]
}

str_Punctuations = """!)]};:,.?&"""

#-------------------------------------------------
#=================== TABULATION ==================
#-------------------------------------------------

def iterate_Tabulation(md_XML, node_Curr, i_Lvl):
  #print(i_Lvl)

  str_Curr = ""
  if node_Curr.nodeType == node_Curr.TEXT_NODE:
    str_Curr = node_Curr.toxml().replace("\n", " ").strip()

  else:
    bl_IsSingle = True
    if len(ht_Nodes.get(node_Curr.nodeName, [""])) > 0:
      bl_IsSingle = False

    if node_Curr.nodeName in lst_Inlines:
      if node_Curr.previousSibling != None and node_Curr.previousSibling.nodeType == node_Curr.TEXT_NODE and node_Curr.previousSibling.nodeValue.replace("\n", " ").strip() != "":
        str_Curr += " "
    else:
      str_Curr += "\n" + "  " * i_Lvl

    str_Curr += "<" + node_Curr.nodeName
    ht_Atts = node_Curr.attributes or {}
    for str_Key, str_Val in ht_Atts.items():
      str_Curr += " %s=\"%s\"" % (str_Key, md_XML.createTextNode(str_Val).toxml())

    if bl_IsSingle:
      str_Curr += "/"
    str_Curr += ">"

    bl_IsLastInline = False
    for node_Child in node_Curr.childNodes:
      str_Child = iterate_Tabulation(md_XML, node_Child, i_Lvl + 1)
      if str_Child != "":
        str_Curr += str_Child
        bl_IsLastInline = (node_Child.nodeType == node_Child.TEXT_NODE) or (node_Child.nodeName in lst_Inlines)
        if node_Child.nodeName in lst_Inlines and node_Child.nextSibling != None and node_Child.nextSibling.nodeType == node_Child.TEXT_NODE:
          str_Next = node_Child.nextSibling.nodeValue.replace("\n", " ").strip()
          if str_Next != "":
            if str_Next[0] not in str_Punctuations:
              str_Curr = str_Curr + " "

    if not bl_IsSingle:
      if not (bl_IsLastInline or len(node_Curr.childNodes) == 0):
        str_Curr += "\n" + "  " * i_Lvl
      str_Curr += "</" + node_Curr.nodeName + ">"

    #print(str_Curr)

  return str_Curr
  

def proc_Tabulation(md_XML, bl_IsChanged, ht_Args):
  if ht_Args["TABULATION"]:
    printI("INFO", "Alignment indentation", 3, ht_Args["DETAILS"])

    str_ResultFB2 = "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
    for node_Curr in md_XML.childNodes:
      str_ResultFB2 += iterate_Tabulation(md_XML, node_Curr, 0)
    #str_ResultFB2 = md_XML.toxml()

    return str_ResultFB2, True

  return md_XML.toxml(), bl_IsChanged

#-------------------------------------------------
#===================== CLEAN =====================
#-------------------------------------------------

def iterate_Clean(node_Curr, ht_Args):
  if node_Curr.nodeType == node_Curr.TEXT_NODE:
    return False
  else:
    bl_Res = False

    for node_Child in reversed(node_Curr.childNodes):
      bl_IsNeedDel = False

      if node_Child.nodeType == node_Child.TEXT_NODE:
        if node_Child.nodeValue.replace("\n", " ").strip() == "":
          bl_IsNeedDel = True
        elif not ("" in ht_Nodes.get(node_Curr.nodeName)) and node_Curr.parentNode.nodeName != "publish-info":
          bl_IsNeedDel = True
      elif ht_Nodes.get(node_Child.nodeName) == None:
        bl_IsNeedDel = True
      elif not (node_Child.nodeName in ht_Nodes.get(node_Curr.nodeName)):
        bl_IsNeedDel = True
      elif node_Curr.parentNode.nodeName == "publish-info" and node_Curr.nodeName == "publisher":
        bl_IsNeedDel = True
      else:
        bl_Res |= iterate_Clean(node_Child, ht_Args)

      if bl_IsNeedDel:
        if not (node_Child.nodeType == node_Child.TEXT_NODE and node_Child.nodeValue.replace("\n", " ").strip() == ""):
          printI("INFO", "Wrong node removed from %s:\n%s" % (node_Curr.nodeName, node_Child.toprettyxml()), 3, ht_Args["DETAILS"])
        node_Curr.removeChild(node_Child)
        bl_Res = True

    return bl_Res

def proc_Clean(md_XML, ht_Args):
  bl_Res = False
  for node_Curr in md_XML.childNodes:
    bl_Res |= iterate_Clean(node_Curr, ht_Args)
  return bl_Res
  
#-------------------------------------------------
#======================= ID ======================
#-------------------------------------------------

def proc_ID(md_XML, ht_Args):
  node_FictionBook = md_XML.getElementsByTagName("FictionBook")
  if len(node_FictionBook) == 1:
    node_Description = node_FictionBook[0].getElementsByTagName("description")
    if len(node_Description) == 1:
      node_DocumentInfo = node_Description[0].getElementsByTagName("document-info")
      if len(node_DocumentInfo) == 1:
        node_ID = node_DocumentInfo[0].getElementsByTagName("id")
        if len(node_ID) > 0:
          node_Text = node_ID[0].firstChild
          if node_Text != None:
            #print(node_Text.nodeValue)
            printI("INFO", "Node \"ID\" already exist", 3, ht_Args["DETAILS"])
            return False
      else:
        printE("Current fb2 file totally incorrect: \"document-info\" node found not once (0 or more than 1)", 3)
        return False
    else:
      printE("Current fb2 file totally incorrect: \"description\" node found not once (0 or more than 1)", 3)
      return False
  else:
    printE("Current fb2 file totally incorrect: \"FictionBook\" node found not once (0 or more than 1)", 3)
    return False

  node_FictionBook = md_XML.getElementsByTagName("FictionBook")
  node_Description = node_FictionBook[0].getElementsByTagName("description")
  node_DocumentInfo = node_Description[0].getElementsByTagName("document-info")
  node_ID = node_DocumentInfo[0].getElementsByTagName("id")

  str_ID = str(uuid.uuid4())
  textnode_ID = md_XML.createTextNode(str_ID)

  if len(node_ID) > 0:
    node_ID[0].appendChild(textnode_ID)
  else:
    node_ID = md_XML.createElement("id")
    node_ID.appendChild(textnode_ID)

    lst_PrevNodes = ["version", "history", "publisher"]

    for str_Afternode in lst_PrevNodes:
      node_Afternode = node_DocumentInfo[0].getElementsByTagName(str_Afternode)
      if len(node_Afternode) > 0:
        node_DocumentInfo[0].insertBefore(node_ID, node_Afternode[0])
        break
    else:
      node_DocumentInfo[0].appendChild(node_ID)

  printI("INFO", "Node \"ID\" created successfully", 3, ht_Args["DETAILS"])
  #print(str_ID)

  return True

#-------------------------------------------------
#================== From Cactus ==================
#================ with some fixes ================
#-------------------------------------------------

def fb2_get_book_name(dom):
    title_info_node = dom.getElementsByTagName("title-info")
    if len(title_info_node) == 0:
        return None

    author_node = title_info_node[0].getElementsByTagName("author")
    if len(author_node) == 0:
        return None

    first_name_node = author_node[0].getElementsByTagName("first-name")
    last_name_node = author_node[0].getElementsByTagName("last-name")
    nickname_node = author_node[0].getElementsByTagName("nickname")

    book_title_node = title_info_node[0].getElementsByTagName("book-title")
    if len(book_title_node) == 0:
        return None

    book_name = None
    first_name = None
    last_name = None
    nickname = None

    if len(book_title_node) > 0:
      book_name = xml_get_text(book_title_node[0].firstChild)
    if len(first_name_node) > 0:
      first_name = xml_get_text(first_name_node[0].firstChild)
    if len(last_name_node) > 0:
      last_name = xml_get_text(last_name_node[0].firstChild)
    if len(nickname_node) > 0:
      nickname = xml_get_text(nickname_node[0].firstChild)

    if book_name != None and (first_name != None and last_name != None or nickname != None):
        res_name = ""
        tr_table = res_name.maketrans("\/?|:", ".....")
        if first_name != None and last_name != None:
          res_name = first_name + " " + last_name + " - " + book_name + ".fb2"
        else:
          res_name = nickname + " - " + book_name + ".fb2"
        res_name = res_name.translate(tr_table)
        return res_name
    else:
        return None

def xml_get_text(node):
    if node is None:
         return None
    else:
        return node.nodeValue

#-------------------------------------------------
#=================================================
#-------------------------------------------------

def printE(str_Msg, i_Lvl):
  i_Lvl = 0 if i_Lvl < 0 else i_Lvl
  #print("\t" * i_Lvl + "[ERROR]\t" + str_Msg, file = sys.stderr)
  print("\t" * i_Lvl + "[ERROR]\t" + str_Msg)

def printI(str_Hdr, str_Msg, i_Lvl, bl_Flag):
  i_Lvl = 0 if i_Lvl < 0 else i_Lvl
  if bl_Flag:
    print("\t" * i_Lvl + "[" + str_Hdr + "]\t" + str_Msg)

#-------------------------------------------------
#=================================================
#-------------------------------------------------

if __name__ == "__main__":
  main()

#-------------------------------------------------
