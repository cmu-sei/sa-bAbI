#include <clang-c/Index.h>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <json.hpp>
#include <map>

using json = nlohmann::json;

struct Location {
  std::string file;
  unsigned line;
  unsigned column;
  unsigned offset;

  Location() {
    this->file = "";
    this->line = 0;
    this->column = 0;
    this->offset = 0;
  }
};

struct SymbolInfo {
  std::string spelling;
  std::string kind;
  bool isBuiltin;
  Location origin;
  bool hasDefinition;
  CXVisibilityKind visibility;
  CXLinkageKind linkage;
  CXAvailabilityKind availability;
  std::map<unsigned, Location> occurrences;
};

typedef std::map<std::string, SymbolInfo> SymbolMap;

struct VisitorData {
  SymbolMap &symMap;
  std::string tuName;
  VisitorData(SymbolMap &sm, const char *name) : symMap(sm), tuName(name) {}
};

void getLocation(CXCursor &cursor, Location &loc) {
  CXFile file;
  CXSourceLocation srcLoc = clang_getCursorLocation(cursor);
  clang_getSpellingLocation(srcLoc, &file, &loc.line, &loc.column, &loc.offset);
  CXString fileSpelling = clang_getFileName(file);
  const char *fileStr = clang_getCString(fileSpelling);
  if (fileStr != nullptr) {
    loc.file = clang_getCString(fileSpelling);
  } else {
    loc.file = "";
  }
  clang_disposeString(fileSpelling);
}

void populateSymbolInfo(CXCursor &cursor, SymbolInfo &symInfo) {
  CXCursorKind kind = clang_getCursorKind(cursor);
  CXString kindStr = clang_getCursorKindSpelling(kind);
  symInfo.kind = clang_getCString(kindStr);
  clang_disposeString(kindStr);

  CXString spelling = clang_getCursorSpelling(cursor);
  symInfo.spelling = clang_getCString(spelling);
  clang_disposeString(spelling);

  CXCursor def = clang_getCursorDefinition(cursor);
  symInfo.hasDefinition = !clang_equalCursors(def, clang_getNullCursor());

  symInfo.linkage = clang_getCursorLinkage(cursor);
  symInfo.availability = clang_getCursorAvailability(cursor);
  symInfo.visibility = clang_getCursorVisibility(cursor);

  // This is probably horrible, but I can't find a better way to detect
  // instrinsics with libclang at the moment.
  std::string builtin_prefix("__builtin");
  if (symInfo.spelling.compare(0, builtin_prefix.size(), builtin_prefix) == 0) {
    symInfo.isBuiltin = true;
  } else {
    symInfo.isBuiltin = false;
    getLocation(cursor, symInfo.origin);
  }
}

void dumpCursorInfo(CXCursor &cursor) {
  CXCursorKind kind = clang_getCursorKind(cursor);
  CXString kindStr = clang_getCursorKindSpelling(kind);
  std::cout << clang_getCString(kindStr) << " ";
  clang_disposeString(kindStr);

  CXType type = clang_getCursorType(cursor);
  CXString typeStr = clang_getTypeSpelling(type);
  std::cout << clang_getCString(typeStr) << " ";
  clang_disposeString(typeStr);

  CXType ctype = clang_getCanonicalType(type);
  CXString ctypeStr = clang_getTypeSpelling(ctype);
  std::cout << clang_getCString(ctypeStr) << " ";
  clang_disposeString(ctypeStr);

  CXString spelling = clang_getCursorSpelling(cursor);
  std::cout << clang_getCString(spelling) << " ";
  clang_disposeString(spelling);

  CXString usr = clang_getCursorUSR(cursor);
  std::cout << clang_getCString(usr) << " ";
  clang_disposeString(usr);

  std::cout << clang_isReference(kind) << " ";
  std::cout << std::endl;
}

bool isDeclOrDeclRef(CXCursor &cursor) {
  CXCursorKind kind = clang_getCursorKind(cursor);
  return clang_isDeclaration(kind) || kind == CXCursor_DeclRefExpr ||
         kind == CXCursor_MemberRefExpr || kind == CXCursor_TypeRef;
}

CXChildVisitResult astVisit(CXCursor cursor, CXCursor parent,
                            CXClientData data) {
  // NOTE: Currently not using the parent parameter, but it
  // is required in the callback. Putting this here to avoid
  // a warning. Can remove if the parameter is used.
  (void)parent;
  VisitorData *visitorData = (VisitorData *)data;
  SymbolMap &symMap = visitorData->symMap;
  Location loc;
  getLocation(cursor, loc);
  //dumpCursorInfo(cursor);
  if (visitorData->tuName.compare(loc.file) == 0 && isDeclOrDeclRef(cursor)) {
    CXCursor origin = clang_getCursorReferenced(cursor);

    if (!clang_equalCursors(origin, clang_getNullCursor())) {
      CXString usr = clang_getCursorUSR(origin);
      std::string usrStr = clang_getCString(usr);
      SymbolMap::iterator symbolQuery = symMap.find(usrStr);
      clang_disposeString(usr);

      if (symbolQuery == symMap.end()) {
        std::pair<SymbolMap::iterator, bool> result =
            symMap.emplace(usrStr, SymbolInfo{});
        symbolQuery = result.first;
        populateSymbolInfo(origin, symbolQuery->second);
      }

      SymbolInfo &symInfo = symbolQuery->second;
      unsigned offset = loc.offset;
      if (symInfo.occurrences.find(offset) == symInfo.occurrences.end()) {
        symInfo.occurrences[offset] = loc;
      }
    }
  }

  clang_visitChildren(cursor, astVisit, data);
  return CXChildVisit_Continue;
}

int main(int argc, char **argv) {
  // Handle arguments
  if (argc < 2) {
    std::cerr << "Usage: find_symbols sourcefile [compiler options ...]\n";
    exit(1);
  }
  // First argument: the path to a source file
  const auto filename = argv[1];
  // Second argument: filename filter for tokens
  const auto compileArgs = &argv[2];
  // The # of compiler args
  auto numArgs = argc - 2;

  // This script will produce json data, represented by this object
  json jsonResult;

  // excludeDeclsFromPCH = 1: precompiled headers omitted in TUs
  // displayDiagnostics = 1: show warnings/errors in TUs
  CXIndex index = clang_createIndex(1, 1);

  // Create a translation unit
  unsigned options = 0;
  //  options = options | CXTranslationUnit_DetailedPreprocessingRecord;
  CXTranslationUnit tu = clang_parseTranslationUnit(
      index,                // The index to use
      filename,             // The path to the source file
      compileArgs,          // The compiler args
      numArgs,              // Number of compiler args
      nullptr, 0, options); // Remaining options are not needed

  if (tu == nullptr) {
    std::cerr << "Failed to parse translation unit." << std::endl;
    exit(1);
  }

  CXString tuSpelling = clang_getTranslationUnitSpelling(tu);
  const char *tuName = clang_getCString(tuSpelling);
  jsonResult["filename"] = tuName;

  SymbolMap symbolMap;
  VisitorData data(symbolMap, tuName);
  CXCursor cursor = clang_getTranslationUnitCursor(tu);
  clang_visitChildren(cursor, astVisit, &data);

  jsonResult["symbols"] = {};
  for (auto const &sym : symbolMap) {
    // Ignore symbols with no spelling
    if (sym.second.spelling.compare("") == 0) {
      continue;
    }
    if(sym.second.spelling.compare("fun") == 0) {
      continue;
    }
    if(sym.second.spelling.compare("strcpy") == 0) {
      continue;
    }
    if(sym.second.spelling.compare("memset") == 0) {
      continue;      
    }
    if(sym.second.spelling.compare("memcpy") == 0) {
      continue;      
    }
    if(sym.second.spelling.compare("malloc") == 0) {
      continue;      
    }

    json symbolJson;

    symbolJson["is_builtin"] = sym.second.isBuiltin;
    if (!sym.second.isBuiltin) {
      json origin;
      origin["file"] = sym.second.origin.file;
      origin["line"] = sym.second.origin.line;
      origin["column"] = sym.second.origin.column;
      origin["offset"] = sym.second.origin.offset;
      symbolJson["origin"] = origin;
    }
    symbolJson["spelling"] = sym.second.spelling;
    symbolJson["kind"] = sym.second.kind;
    symbolJson["linkage"] = sym.second.linkage;
    symbolJson["availability"] = sym.second.availability;
    symbolJson["visibility"] = sym.second.visibility;
    symbolJson["def"] = sym.second.hasDefinition;    
    symbolJson["occurrences"] = {};
    for (auto const &loc : sym.second.occurrences) {
      json occ;
      occ["file"] = loc.second.file;
      occ["line"] = loc.second.line;
      occ["column"] = loc.second.column;
      occ["offset"] = loc.second.offset;
      symbolJson["occurrences"].push_back(occ);
    }

    jsonResult["symbols"].push_back(symbolJson);
  }

  // Clean up
  clang_disposeString(tuSpelling);
  clang_disposeTranslationUnit(tu);
  clang_disposeIndex(index);

  std::cout << std::setw(4) << jsonResult << std::endl;
  return 0;
}
