#include <clang-c/Index.h>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <json.hpp>
#include <map>

using json = nlohmann::json;

struct SymbolInfo {
    std::string text;
    std::string file;
    std::string kind;
    unsigned line;
    unsigned column;
    unsigned offset;
    unsigned frequency;
}; 

typedef std::map<std::string,SymbolInfo> SymbolMap;

void handleIdentifier(CXTranslationUnit &tu,
		      CXToken &token,
		      SymbolMap &symbolMap) {
    CXCursor cursor;
    clang_annotateTokens(tu, &token, 1, &cursor);

    CXCursor decl = clang_getNullCursor();
    CXCursorKind kind = clang_getCursorKind(cursor);

    if (clang_isDeclaration(kind)) {
        decl = cursor;	
    } else if (clang_isExpression(kind)) {
        // Try getCursorDefinition() first, and if it fails try getCursorReferenced
        decl = clang_getCursorDefinition(cursor);
        if (clang_equalCursors(decl, clang_getNullCursor())) {
            decl = clang_getCursorReferenced(cursor);
        }
    } else {
	CXString cursorKindName = clang_getCursorKindSpelling(kind);
	std::cout << "Unknown cursor type: " << clang_getCString(cursorKindName) << "\n";
	clang_disposeString(cursorKindName);
    }

    if(!clang_equalCursors(decl, clang_getNullCursor())) {
        CXString usr = clang_getCursorUSR(decl);
	std::string usrStr = clang_getCString(usr);
	SymbolMap::iterator symbolQuery = symbolMap.find(usrStr);
	if(symbolQuery == symbolMap.end()) {
	    SymbolInfo symInfo;
	    CXCursorKind declKind = clang_getCursorKind(decl);
	    CXString declKindName = clang_getCursorKindSpelling(declKind);

	    CXFile file;
	    unsigned line, column, offset;
	    CXSourceLocation loc;
	    loc = clang_getCursorLocation(decl);
	    clang_getSpellingLocation(loc, &file, &line, &column, &offset);
	    CXString fileName = clang_getFileName(file);
	    CXString spell = clang_getTokenSpelling(tu, token);
	    
	    symInfo.file = clang_getCString(fileName);
	    symInfo.line = line;
	    symInfo.column = column;
	    symInfo.offset = offset;
	    symInfo.frequency = 1;
	    symInfo.text = clang_getCString(spell);
	    symInfo.kind = clang_getCString(declKindName);

	    clang_disposeString(declKindName);
	    clang_disposeString(fileName);
	    clang_disposeString(spell);
	    symbolMap[usrStr] = symInfo;
	} else {
	    SymbolInfo &symInfo = symbolQuery->second;
	    symInfo.frequency++;
	}

	clang_disposeString(usr);
    }
}

void handleTokens(
		  CXTranslationUnit &tu, 
		  CXToken *tokens,
		  unsigned count,
		  SymbolMap &symbolMap) {
    for (unsigned i = 0; i < count; i++) {
        CXToken &token = tokens[i];
        CXTokenKind tokenKind = clang_getTokenKind(token);
        if (tokenKind == CXToken_Identifier) {
            handleIdentifier(tu, token, symbolMap);
        }
    }
}

unsigned getFileSize(const char *fileName) {
    FILE *fp = fopen(fileName, "r");
    fseek(fp, 0, SEEK_END);
    auto size = ftell(fp);
    fclose(fp);
    return size;
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

int main(int argc, char **argv) {
    // Handle arguments
    if (argc < 2) {
        std::cerr << "Usage: tokenize sourcefile [compiler options ...]\n";
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
    options = options | CXTranslationUnit_DetailedPreprocessingRecord;
    CXTranslationUnit tu = clang_parseTranslationUnit(
        index,                 // The index to use
        filename,              // The path to the source file
        compileArgs,           // The compiler args
        numArgs,               // Number of compiler args
        nullptr, 0, options);  // Remaining options are not needed

    if (tu == nullptr) {
        std::cerr << "Failed to parse translation unit." << std::endl;
        exit(1);
    }

    CXString tuSpelling = clang_getTranslationUnitSpelling(tu);
    const char *tuName = clang_getCString(tuSpelling);
    jsonResult["filename"] = tuName;

    // Create a CXSouceRange spanning the whole file (start to end)
    CXSourceRange range = getFileRange(tu, filename);
    if (clang_Range_isNull(range)) {
        std::cerr << "Failed to tokenize file." << std::endl;
        exit(1);
    }

    // Tokenize this range (that is, the whole file)
    CXToken *tokens;
    unsigned count;
    clang_tokenize(tu, range, &tokens, &count);

    // Process the tokens
    SymbolMap symbolMap;
    handleTokens(tu, tokens, count, symbolMap);
    clang_disposeTokens(tu, tokens, count);

    jsonResult["symbols"] = {};
    for(auto const& item : symbolMap) {
	json symbolJson;
	symbolJson["file"] = item.second.file;
	symbolJson["line"] = item.second.line;
	symbolJson["column"] = item.second.column;
	symbolJson["offset"] = item.second.offset;
	symbolJson["text"] = item.second.text;
	symbolJson["freq"] = item.second.frequency;
	symbolJson["kind"] = item.second.kind;
	jsonResult["symbols"].push_back(symbolJson);
    }
    // Clean up
    clang_disposeString(tuSpelling);
    clang_disposeTranslationUnit(tu);
    clang_disposeIndex(index);

    std::cout << std::setw(4) << jsonResult << std::endl;
    return 0;
}
