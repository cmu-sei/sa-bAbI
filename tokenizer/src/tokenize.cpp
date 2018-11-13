#include <clang-c/Index.h>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <json.hpp>
#include <map>
#include <fstream>

using json = nlohmann::json;

const char *getTokenKindCString(CXTokenKind kind) {
  switch (kind) {
  case CXToken_Punctuation:
    return "Punctuation";
  case CXToken_Keyword:
    return "Keyword";
  case CXToken_Identifier:
    return "Identifier";
  case CXToken_Literal:
    return "Literal";
  case CXToken_Comment:
    return "Comment";
  default:
    return "Unknown";
  }
}

bool endsWith(const std::string &s, const std::string &m) {
  return 
	s.size() >= m.size() 
	&& s.compare(s.size() - m.size(), m.size(), m) == 0;
}

void handleIdentifier(CXCursor &cursor, json &jsonData) {
  CXType type = clang_getCursorType(cursor);
  CXCursorKind kind = clang_getCursorKind(cursor);

  // Store the cursor type name
  if (type.kind != CXType_Invalid) {
    CXString typeName = clang_getTypeSpelling(type);
    jsonData["type"] = clang_getCString(typeName);
    clang_disposeString(typeName);
  }

  if (clang_isDeclaration(kind)) {
    // For declarations, determine the USR
    CXString usr = clang_getCursorUSR(cursor);
    jsonData["id"] = clang_getCString(usr);
    CXCursorKind cursorKind = clang_getCursorKind(cursor);
    CXString curKindName = clang_getCursorKindSpelling(cursorKind);
    jsonData["kind"] = clang_getCString(curKindName);
    clang_disposeString(curKindName);
    clang_disposeString(usr);
  } else if (clang_isExpression(kind)) {
    CXFile file;
    unsigned line, column, offset;
    CXSourceLocation loc;

    // Lookup where the identifier was declared
    // Try getCursorDefinition() first, and if it fails try getCursorReferenced
    CXCursor def = clang_getCursorDefinition(cursor);
    if (clang_equalCursors(def, clang_getNullCursor())) {
      def = clang_getCursorReferenced(cursor);
    }

    if (!clang_equalCursors(def, clang_getNullCursor())) {
      loc = clang_getCursorLocation(def);
      clang_getSpellingLocation(loc, &file, &line, &column, &offset);
      {
        json ref;
	CXString fileName = clang_getFileName(file);
	ref["file"] = clang_getCString(fileName);
        ref["linenum"] = line;
        jsonData["ref"] = ref;
      }

      CXString usr = clang_getCursorUSR(def);
      jsonData["id"] = clang_getCString(usr);
      CXCursorKind cursorKind = clang_getCursorKind(def);
      CXString curKindName = clang_getCursorKindSpelling(cursorKind);

      jsonData["kind"] = clang_getCString(curKindName);
      clang_disposeString(curKindName);
      clang_disposeString(usr);
    }
  }
}

void handleTokens(CXTranslationUnit &tu, CXToken *tokens, unsigned count,
                  json &jsonData) {
  for (unsigned i = 0; i < count; i++) {
    json tokenJson;
    CXCursor cursor;
    CXToken &token = tokens[i];
        
    CXTokenKind tokenKind = clang_getTokenKind(token);
    if(tokenKind == CXToken_Comment) {
        continue;
    }    
    tokenJson["kind"] = getTokenKindCString(tokenKind);
    
    // Get information about the token location
    CXFile file;
    unsigned line, column, offset;
    CXSourceLocation loc = clang_getTokenLocation(tu, token);
    clang_getFileLocation(loc, &file, &line, &column, &offset);
    CXString fileName = clang_getFileName(file);

    tokenJson["line"] = line;
    clang_disposeString(fileName);

    // Extract the token text
    CXString spell = clang_getTokenSpelling(tu, token);
    tokenJson["text"] = clang_getCString(spell);
    clang_disposeString(spell);

    // Inspect the semantics of the token
    clang_annotateTokens(tu, &token, 1, &cursor);
    CXCursorKind cursorKind = clang_getCursorKind(cursor);

    // We currently filter out inclusion directives and tokens with 
    // type "InvalidFile". The latter seem to show up in the middle 
    // of preprocessor directives
    if(   cursorKind == CXCursor_InvalidFile 
       || cursorKind == CXCursor_InclusionDirective) {
      continue;
    }

    CXString curKindName = clang_getCursorKindSpelling(cursorKind);
    tokenJson["sem"] = clang_getCString(curKindName);
    clang_disposeString(curKindName);

    if (tokenKind == CXToken_Identifier) {
      handleIdentifier(cursor, tokenJson["sym"]);
    }

    jsonData.push_back(tokenJson);
  }
}

unsigned getFileSize(const char *fileName) {
  FILE *fp = fopen(fileName, "r");
  fseek(fp, 0, SEEK_END);
  auto size = ftell(fp);
  fclose(fp);
  return size;
}

std::string getFileName(const std::string& s, char sep='/') {
  size_t i = s.rfind(sep, s.length());
  if (i != std::string::npos) {
    return(s.substr(i+1, s.length() - i));
  }
  return("");
}

CXSourceRange getFileRange(const CXTranslationUnit &tu, const char *filename) {
  CXFile file = clang_getFile(tu, filename);
  auto fileSize = getFileSize(filename);

  // Get start and end location of the file, then generate
  // a range from start to end
  CXSourceLocation startLoc = clang_getLocationForOffset(tu, file, 0);
  CXSourceLocation endLoc = clang_getLocationForOffset(tu, file, fileSize);
  return clang_getRange(startLoc, endLoc);
}

void handleFile(const char *filePath);

int main(int argc, char **argv) {
  for(int ii = 1; ii < argc; ii++) {
    handleFile(argv[ii]);
  }
}

void handleFile(const char *filePath) {
  // This script will produce json data, represented by this object
  json jsonResult;

  // excludeDeclsFromPCH = 1: precompiled headers omitted in TUs
  // displayDiagnostics = 1: show warnings/errors in TUs
  CXIndex index = clang_createIndex(1, 1);

  const char *args[] = {"-I/usr/lib/llvm-3.8/bin/../lib/clang/3.8.1/include"};
 
  // Create a translation unit
  unsigned options = 0;
  options = options | CXTranslationUnit_DetailedPreprocessingRecord;
  CXTranslationUnit tu = clang_parseTranslationUnit(
      index,                // The index to use
      filePath,             // The path to the source file
      args,          // The compiler args
      1,              // Number of compiler args
      nullptr, 0, options); // Remaining options are not needed

  if (tu == nullptr) {
    std::cerr << "Failed to parse translation unit." << std::endl;
    exit(1);
  }

  CXString tuSpelling = clang_getTranslationUnitSpelling(tu);
  const char *tuName = clang_getCString(tuSpelling);
  jsonResult["filename"] = tuName;

  // Create a CXSouceRange spanning the whole file (start to end)
  CXSourceRange range = getFileRange(tu, filePath);
  if (clang_Range_isNull(range)) {
    std::cerr << "Failed to tokenize file." << std::endl;
    exit(1);
  }

  // Tokenize this range (that is, the whole file)
  CXToken *tokens;
  unsigned count;
  clang_tokenize(tu, range, &tokens, &count);

  jsonResult["tokens"] = {};

  // Process the tokens
  handleTokens(tu, tokens, count, jsonResult["tokens"]);
  clang_disposeTokens(tu, tokens, count);

  // Clean up
  clang_disposeString(tuSpelling);
  clang_disposeTranslationUnit(tu);
  clang_disposeIndex(index);

  std::ofstream outFile;
  outFile.open (getFileName(filePath) + ".tok");
  outFile << std::setw(4) << jsonResult << std::endl;
  outFile.close();
}
